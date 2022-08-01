import re
import requests
import io
import zipfile
import logging
from datetime import datetime
from unicodedata import category
from dateutil.relativedelta import relativedelta
from rest_framework.exceptions import APIException

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


logger = logging.getLogger(__name__)

def get_date_snap(monuments_qs, date):

    first_image = Picture.objects.filter(
            monument__pk=models.OuterRef('pk'),
        ).order_by().values('monument__pk').annotate(
            first_image=models.Min('image_date')
        ).values('first_image')[:1]

    out = monuments_qs.annotate(
        first_image=models.Subquery(first_image),
    ).annotate(
        const = models.Value(1),
        mapped = models.Case(
            models.When(first_revision__lte=date, then=models.Value(1)),
            default=models.Value(0),
        ),
        authorized = models.Case(
            models.When(start__lte=date, then=models.Value(1)),
            default=models.Value(0),
        ),
        with_pictures = models.Case(
            models.When(first_image__lte=date, then=models.Value(1)),
            default=models.Value(0),
        ),
    ).values('const').order_by().annotate(
        mapped=models.Sum('mapped'),
        authorized=models.Sum('authorized'),
        with_pictures=models.Sum('with_pictures'),
    ).values('mapped', 'authorized', 'with_pictures')

    print("ss", out)

    aggregated_data = out[0]
    
    return {
        "date": date,
        "aggregated_data": aggregated_data,
    }


def get_snap(monuments_qs, date_from, date_to, step_size=1, step_unit="month"):


    start = date_from
    dates = [start]

    
    while start <= date_to:
        start += relativedelta(**{step_unit: step_size})
        dates.append(start)
        if len(dates) > 50:
            raise APIException("Too many dates")

    
    out = []
    for date in dates:
        print(monuments_qs)
        date_snap = get_date_snap(monuments_qs, date)
        out.append(date_snap)

    
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
        return value[0] or default

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
    start = monument_prop(monument_data, "start", None)
    end = monument_prop(monument_data, "end_n", None)
    parent_q_number =  monument_prop(monument_data, "parent_n", "")

    relevant_images = monument_data.get("relevantImage_n", [])


    place_geo_n = monument_prop(monument_data, "place_geo_n", None)
    try:
        coords = parse_point(place_geo_n)
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

    if not monument.pk:
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

    return monument


def update_category(monuments, category_snapshot, skip_pictures=False, skip_geo=False):
    for monument in monuments:
        update_monument(monument, category_snapshot, skip_pictures=skip_pictures, skip_geo=skip_geo)
    

def process_category_snapshot(cat_snapshot, skip_pictures=False, skip_geo=False):
    if not cat_snapshot.payload:
        results = execute_query(cat_snapshot.query)
        data = results["results"]["bindings"]
        cat_snapshot.payload = data
        cat_snapshot.save()
    monuments = [format_monument(x) for x in cat_snapshot.payload]
    update_category(monuments, cat_snapshot, skip_pictures=skip_pictures, skip_geo=skip_geo)
    


def take_snapshot(skip_pictures=False, skip_geo=False, force_new_snapshot=False):
    """
    New monuments + Update to monuments data
    New Approved/Unapproved monuments
    New pictures
    Aggregate data on geographic entities #TODO: evaluate on-the-fly aggregation with aggressive caching (break on import and pre-caching)
    """
    pending_snapshots = Snapshot.objects.filter(complete=False).order_by('-created')
    if not pending_snapshots.exists():
        logger.info("No pending snapshots")
        snapshot = Snapshot.objects.create()
    else:
        snapshot = pending_snapshots[0]     
        Snapshot.objects.exclude(pk=snapshot.pk).filter(complete=False).delete()

    categories_snapshots = []
    #creating CategorySnapshot
    for item in WLM_QUERIES + WIKI_CANDIDATE_TYPES:
        category = Category.objects.get_or_create({'label': item['label'], 'q_number': item['q_number']})[0]
        if "query_file" in item:
            query = get_wlm_query(item['query_file'])
        else:
            typologies_query = get_query_template_typologies()
            type_to_search = "wd:" + item["q_number"] + " # " + item["label"]
            query = re.sub("wd:Q_NUMBER_TYPE", type_to_search, typologies_query)
        
        cat_snapshot = CategorySnapshot.objects.get_or_create(category=category, snapshot=snapshot, query=query)[0]
        categories_snapshots.append(cat_snapshot)


    for cat_snapshot in categories_snapshots:
        if cat_snapshot.complete:
            continue
        process_category_snapshot(cat_snapshot, skip_pictures=skip_pictures, skip_geo=skip_geo)
        cat_snapshot.complete = True
        cat_snapshot.save()

    #fixing empty positions
    for monument in Monument.objects.filter(position=None).exclude(parent_q_number=""):
        if monument.parent_q_number:
            try:
                parent_monument = Monument.objects.get(q_number=monument.parent_q_number)
                monument.position = parent_monument.position
                monument.save()
            except Monument.DoesNotExist:
                pass

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


import zipfile, tempfile

# def unzip_regions(path):

#     mapping = {
#         'name' : 'DEN_REG',
#         'poly' : 'POLYGON', 
#     } 

#     with zipfile.ZipFile(path) as thezip:
#         with tempfile.TemporaryDirectory() as tempdir:
#             thezip.extractall(tempdir)


#             lm = LayerMapping(TestGeo, 'test_poly.shp', mapping)


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
