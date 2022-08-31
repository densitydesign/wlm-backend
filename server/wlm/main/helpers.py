from cmath import inf
from typing import OrderedDict
from django.core.cache import cache
import re
import requests
import io
import zipfile
import logging
from datetime import datetime
from unicodedata import category
from dateutil.relativedelta import relativedelta
from rest_framework.exceptions import APIException
from django.test import Client, RequestFactory
import functools

from django.contrib.gis.utils import LayerMapping
from django.db import transaction, models
from django.forms import ValidationError
from django.utils.timezone import make_aware
from django.contrib.gis.geos import Point
from main.wiki_api import (
    format_monument,
    WLM_QUERIES,
    WIKI_CANDIDATE_TYPES,
    search_commons,
    get_revision,
    get_query_template_typologies,
    get_wlm_query,
    execute_query,
)
from main.models import Monument, Picture, Region, Province, Municipality, Category, CategorySnapshot, Snapshot
from main.serializers import ProvinceGeoSerializer, MunicipalityGeoSerializer, RegionGeoSerializer
from django.contrib.gis.db.models.functions import Centroid


logger = logging.getLogger(__name__)

def get_date_snap(monuments_qs, date, group=None):

    first_image = Picture.objects.filter(
            monument__pk=models.OuterRef('pk'),
        ).order_by().values('monument__pk').annotate(
            first_image=models.Min('image_date', default=None),
        ).values('first_image')[:1]

    out = monuments_qs.annotate(
        national=models.Value("1"),
        national_name=models.Value("Italy"),
        
        date = models.Value(date),
        on_wiki = models.Case(
            models.When(first_revision__lte=date, then=models.Value(1)),
            default=models.Value(0),
        ),
        in_contest = models.Case(
            models.When(first_revision__lte=date, start__lte=date, then=models.Value(1)),
            default=models.Value(0),
        ),
        photographed = models.Case(
            models.When(first_revision__lte=date, start__lte=date, first_image_date__lte=date, then=models.Value(1)),
            default=models.Value(0),
        ),
    )
    
    if group:
        values = group if type(group) is list else [group]
        values = values + ['date']
    else:
        values = ['date']

    out = out.values(*values).order_by().annotate(
        on_wiki=models.Sum('on_wiki', default=0),
        in_contest=models.Sum('in_contest', default=0),
        photographed=models.Sum('photographed', default=0),
    )
    
    values_final = ['on_wiki', 'in_contest', 'photographed', 'date']
    if group:
        if type(group) is list:
            values_final += group
        else:
            values_final.append(group)
    
    out = out.values(*values_final)

    return out


def get_snap(monuments_qs, date_from, date_to, step_size=1, step_unit="month", group=None):
    """
    Please note that "group" parameter is not so `free` as it seems.
    (see format_history method)
    """

    start = date_from
    dates = [start]
    
    while start  <= date_to:
        start += relativedelta(**{step_unit: step_size})
        dates.append(start)
        if len(dates) > 50:
            raise APIException("Too many dates (max 50)")


    out = []
    for date in dates:
        date_snap = get_date_snap(monuments_qs, date, group=group)
        out.append(date_snap)

    flat_list = [item for sublist in out for item in sublist]

    keys_map  = OrderedDict({
            "photographed": "photographed",
            "in_contest": "inContest",
            "on_wiki" : "onWIki",
        })
    
    return {
        "data": format_history(flat_list, keys_map),
        "extent": min_max_values(flat_list, keys_map)
    }


def min_max_values(flat_list, keys_map):
    out = []
    
    for k in keys_map:
        values = [item[k] for item in flat_list if item[k] is not None]
        if not len(values):
            values = [0]
        
        datum = { "label": keys_map[k], "value": [min(values), max(values)]}
        out.append(datum)
    return out
    



def format_history(history, keys_map):
    def get_type(item):
        for key in ['region', 'province', 'municipality', 'national']:
            if key in item:
                return key
        return None

    def transform_key_values(item):
        out =  { "date":item["date"], "groups":[]}
        
        for key in keys_map:
            out["groups"].append({
                "label": keys_map[key],
                "value": item[key]
            })
        
        return out


    def reducer(acc, item):
        item_type = get_type(item)
        if not item_type:
            return acc
        
        #for items with no code, we use 0, otherwise the "sorted" function will not work
        code = item[item_type] or 0
        if item_type != 'national':
            label = item[item_type + '__name']
        else:
            label = 'Italia'

        data_item = transform_key_values(item)
        if code not in acc:
            acc[code] = { "meta" : {"label": label, "code": code, "type": item_type}, "data": [data_item] }
        else:
            acc[code]["data"] += [data_item]

        return acc

    out_dict = functools.reduce(reducer, history, {})
    def make_entry(dict_entry):
        return {**dict_entry["meta"], "history": dict_entry["data"]}
    
    #sorting entries with respect to the last value of the "on_wiki" data point (areas with more monuments on wiki are on top)
    def get_max_value(key):
        item = out_dict[key]
        if "data" not in item:
            return inf

        if not len(item["data"]):
            return inf

        if "groups" not in item["data"][-1]:
            return inf
        
        if not len (item["data"][-1]["groups"]):
            return inf
        
        if item["data"][-1]["groups"][-1]["value"] is None:
            return inf

        return -item["data"][-1]["groups"][-1]["value"]
        
    entries = [out_dict[key] for key in sorted(out_dict.keys(), key=get_max_value)]
    out = [make_entry(entry) for entry in entries]
    return out


def get_img_url(title):
    return "https://commons.wikimedia.org/wiki/Special:Filepath/" + title.replace("File:", "")


def monument_prop(monument_data, prop, default=None):
    value = monument_data.get(prop, None)
    if value is None:
        return default

    if isinstance(value, list):
        if not len(value):
            return default
        return min(value) or default
    
    return value


def update_image(monument, image_data, image_type):
    image_id = image_data.get("pageid", None)
    image_title = image_data.get("title", "")
    
    image_url = get_img_url(image_title)
    image_date_str = image_data.get("DateTime", None)
    if image_date_str:
        image_date = make_aware(datetime.fromisoformat(image_date_str))
    else:
        image_date = None

    if not image_id or not image_date:
        return

    try:
        picture = Picture.objects.get(image_id=image_id)
        Picture.objects.filter(pk=picture.pk).update(
           image_type=image_type, monument=monument, image_date=image_date, image_url=image_url,
           image_title=image_title, data=image_data, 
        )
    except Picture.DoesNotExist:
        picture = Picture.objects.create(
            image_id=image_id, image_type=image_type, monument=monument, image_date=image_date, image_url=image_url,
            image_title=image_title, data=image_data
        )
    
    return picture


def parse_point(point_str):
    return point_str.upper().replace("POINT(", "").replace(")", "").split(" ")

@transaction.atomic
def update_monument(monument_data, category_snapshot, skip_pictures=False, skip_geo=False):
    category = category_snapshot.category
    label = category.label

    code = monument_data.get("mon", None)
    if not code:
        raise ValueError("CANNOT UPDATE MONUMENT")

    try:
        monument = Monument.objects.get(q_number=code)
        if monument.snapshot == category_snapshot.snapshot:
            logger.log(logging.INFO, f"Skipping monument {code}")
            return monument

    except Monument.DoesNotExist:
        monument = Monument.objects.create(q_number=code)

    logger.log(logging.INFO, f"Updating monument {code}")

    label = monument_prop(monument_data, "monLabel", "")
    wlm_n = monument_prop(monument_data, "wlm_n", "")
    start = monument_prop(monument_data, "start_n", None)
    end = monument_prop(monument_data, "end_n", None)
    parent_q_number =  monument_prop(monument_data, "parent_n", "")

    relevant_images = monument_data.get("relevantImage_n", [])


    geo_n = monument_prop(monument_data, "geo_n", None)
    try:
        coords = parse_point(geo_n)
        lng = coords[0]
        lat = coords[1]
        
        position = Point(float(lng), float(lat))
    except Exception as e:
        position = None    

    municipality = getattr(monument, 'municipality', None)
    province = getattr(monument, 'province', None)
    region = getattr(monument, 'region', None)

    if not skip_geo and position is not None:
        try:
            municipality = Municipality.objects.get(
                poly__contains=position,
            )
            municipality = municipality
            province = municipality.province
            region = province.region
        except Municipality.DoesNotExist:
            pass

    if not monument.snapshot:
        first_revision = get_revision(code)
    else:
        first_revision = monument.first_revision

    

    Monument.objects.filter(pk=monument.pk).update(
        label=label,
        wlm_n=wlm_n,
        start=start,
        end=end,
        position=position,
        municipality = municipality,
        province = province,
        region = region,
        data=monument_data,
        first_revision=first_revision,
        snapshot=category_snapshot.snapshot,
        parent_q_number=parent_q_number,
        relevant_images=relevant_images,
    )

    monument.categories.add(category)

    if not skip_pictures:
        logger.info(f"Updating pictures for {code}")
        images = search_commons(code)
        for image in images:
            update_image(monument, image, 'wlm')

        aggregates = monument.pictures.all().aggregate(first_image_date=models.Min('image_date'))
        monument.first_image_date = aggregates['first_image_date']
        monument.save()

    return monument


def update_category(monuments, category_snapshot, skip_pictures=False, skip_geo=False):
    for monument in monuments:
        try:
            update_monument(monument, category_snapshot, skip_pictures=skip_pictures, skip_geo=skip_geo)
        except Exception as e:
            logger.exception(e)
    

def process_category_snapshot(cat_snapshot, skip_pictures=False, skip_geo=False):
    logger.info(f"process_category_snapshot {cat_snapshot.category.label}")
    if not cat_snapshot.payload:
        logger.info(f"running sparql for {cat_snapshot.category.label}")
        results = execute_query(cat_snapshot.query)
        data = results["results"]["bindings"]
        cat_snapshot.payload = data
        cat_snapshot.save()
    monuments = [format_monument(x) for x in cat_snapshot.payload]
    update_category(monuments, cat_snapshot, skip_pictures=skip_pictures, skip_geo=skip_geo)
    


def update_geo_from_parents():
    """tries to update missing municipalies, provinces and regions on all the dataset, for monuments with parents"""
    for monument in Monument.objects.filter(models.Q(position=None) | models.Q(municipality=None)).exclude(parent_q_number=""):
        if monument.parent_q_number:
            try:
                parent_monument = Monument.objects.get(q_number=monument.parent_q_number)
                monument.position = parent_monument.position

                if monument.position:
                    try:
                        municipality = Municipality.objects.get(
                            poly__contains=monument.position,
                        )
                        monument.municipality = municipality
                        monument.province = municipality.province
                        monument.region = municipality.province.region
                        
                    except Municipality.DoesNotExist:
                        pass
                    
                monument.save()
            
            except Monument.DoesNotExist:
                pass

def update_geo_areas():
    """tries to update missing municipalies, provinces and regions on all the dataset"""
    for monument in Monument.objects.filter(municipality=None, position__isnull=False):
        try:
            municipality = Municipality.objects.get(
                poly__contains=monument.position,
            )
            monument.municipality = municipality
            monument.province = municipality.province
            monument.region = municipality.province.region
            monument.save()
            
        except Municipality.DoesNotExist:
            pass
        
        


def take_snapshot(skip_pictures=False, skip_geo=False, force_restart=False):
    """
    New monuments + Update to monuments data
    New Approved/Unapproved monuments
    New pictures
    Aggregate data on geographic entities #TODO: evaluate on-the-fly aggregation with aggressive caching (break on import and pre-caching)
    """
    pending_snapshots = Snapshot.objects.filter(complete=False).order_by('-created')
    if force_restart:
        pending_snapshots.delete()
        snapshot = Snapshot.objects.create()
    elif not pending_snapshots.exists():
        logger.info("No pending snapshots")
        snapshot = Snapshot.objects.create()
    else:
        snapshot = pending_snapshots[0]     
        Snapshot.objects.exclude(pk=snapshot.pk).filter(complete=False).delete()

    categories_snapshots = []
    #creating CategorySnapshot
    for item in WLM_QUERIES + WIKI_CANDIDATE_TYPES:
        
        category = Category.objects.get_or_create(label=item["label"])[0]
        category.q_number = item["q_number"]
        category.save()

        if "query_file" in item:
            query = get_wlm_query(item['query_file'])
        else:
            typologies_query = get_query_template_typologies()
            type_to_search = "wd:" + item["q_number"] + " # " + item["label"]
            query = re.sub("wd:Q_NUMBER_TYPE", type_to_search, typologies_query)
        
        cat_snapshot = CategorySnapshot.objects.get_or_create(category=category, snapshot=snapshot, query=query)[0]
        logger.info(cat_snapshot)
        categories_snapshots.append(cat_snapshot)


    for cat_snapshot in categories_snapshots:
        if cat_snapshot.complete:
            continue
        process_category_snapshot(cat_snapshot, skip_pictures=skip_pictures, skip_geo=skip_geo)
        cat_snapshot.complete = True
        cat_snapshot.save()

    #fixing empty positions
    if not skip_geo:
        update_geo_from_parents()
    
    snapshot.complete = True
    snapshot.save()
    snapshot.category_snapshots.all().delete()




def download_extract_zip(url):
    """
    Download a ZIP file and extract its contents in memory
    yields (filename, file-like object) pairs
    """
    response = requests.get(url)
    with zipfile.ZipFile(io.BytesIO(response.content)) as thezip:
        for zipinfo in thezip.infolist():
            with thezip.open(zipinfo) as thefile:
                yield zipinfo.filename, thefile





def update_regions(shape_path):
    logger.info(f"updating regions from shapefile {shape_path}")
    mapping = {
        'name' : 'DEN_REG',
        'code' : 'COD_REG',
        'poly' : 'POLYGON', 
    } 
    lm = LayerMapping(Region, shape_path, mapping)
    Region.objects.all().delete()
    lm.save()


def update_provinces(shape_path):
    logger.info(f"updating provinces from shapefile {shape_path}")
    mapping = {
        'name' : 'DEN_UTS',
        'code' : 'COD_PROV',
        'region_code' : 'COD_REG',
        'poly' : 'POLYGON', 
    } 
    lm = LayerMapping(Province, shape_path, mapping)
    Province.objects.all().delete()
    lm.save()

def update_municipalities(shape_path):
    logger.info(f"updating municipalities from shapefile {shape_path}")
    mapping = {
        'name' : 'COMUNE',
        'code': 'PRO_COM',
        'province_code' : 'COD_PROV',
        'region_code' : 'COD_REG',
        'poly' : 'POLYGON', 
    } 
    lm = LayerMapping(Municipality, shape_path, mapping)
    Municipality.objects.all().delete()
    lm.save()



@transaction.atomic
def update_geo(regions_path, provices_path, municipalities_path):
    """
    Updates the geographic entities
    No historical tracking of changes
    # TODO: UNDERSTAND HOW TO HANDLE PREVIOUS AGGREGATIONS
    # PROBABLY: we should drop and recompute stats for each snapshot. or use on the-fly aggregation + (pre-)caching.
    Potientially this could "move" a Monument from one municipality (or indirectly province or region) to another.
    """
    update_regions(regions_path)
    update_provinces(provices_path)
    update_municipalities(municipalities_path)

    provinces = Province.objects.all()
    provinces_by_code = {}
    regions_by_code = {}
    for province in provinces:
        logger.info(f"update province {province.name}")
        province.region = Region.objects.get(code=province.region_code)
        provinces_by_code[province.code] = province
        regions_by_code[province.region_code] = province.region
        province.save()

    updated_municipalities = []
    municipalities = Municipality.objects.all()
    for municipality in municipalities:
        logger.info(f"update municipality {municipality.name}")
        municipality.province = provinces_by_code[municipality.province_code]
        municipality.region = regions_by_code[municipality.region_code]
        updated_municipalities.append(municipality)
    Municipality.objects.bulk_update(updated_municipalities, ['province', 'region'])

    #updating centroids
    Region.objects.all().annotate(c=Centroid('poly')).update(centroid=models.F('c'))
    Province.objects.all().annotate(c=Centroid('poly')).update(centroid=models.F('c'))
    Municipality.objects.all().annotate(c=Centroid('poly')).update(centroid=models.F('c'))


def update_geo_cache():
    """
    """
    regions = Region.objects.all()
    regions_geo = RegionGeoSerializer(regions, many=True).data
    cache.set("region_geo", regions_geo, None)

    regions = Region.objects.all()
    for region in regions:
        logger.info(f"update cache region provinces {region.name}")
        provinces = region.provinces.all()
        provinces_geo = ProvinceGeoSerializer(provinces, many=True).data
        cache.set(f"region_geo/{region.code}", provinces_geo, None)
        
    provinces = Province.objects.all()
    provinces_geo = ProvinceGeoSerializer(provinces, many=True).data
    cache.set(f"province_geo", provinces_geo, None)

    for province in provinces:
        logger.info(f"update cache province municipalities {province.name}")
        municipalities = province.municipalities.all()
        municipalities_geo = MunicipalityGeoSerializer(municipalities, many=True).data
        cache.set(f"province_geo/{province.code}", municipalities_geo, None)    
        
def update_first_image_date():
    first_image = Picture.objects.filter(
            monument__pk=models.OuterRef('pk'),
        ).order_by().values('monument__pk').annotate(
            first_image=models.Min('image_date', default=None),
        ).values('first_image')[:1]

    monuments = Monument.objects.annotate(
        first_image=models.Subquery(first_image),
    )

    monuments.update(first_image_date=models.F('first_image'))