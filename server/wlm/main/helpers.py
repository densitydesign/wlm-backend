from cmath import inf
import time                
from retry import retry
from django.core.paginator import Paginator
import tempfile
import csv
from typing import OrderedDict
from django.core.cache import cache
import re
import requests
import io
import zipfile
import logging
from datetime import date, timedelta, datetime
import calendar
from unicodedata import category
from dateutil.relativedelta import relativedelta
from rest_framework.exceptions import APIException
from django.test import Client, RequestFactory
import functools
from django.core.cache import caches
from rest_framework import serializers
from django.contrib.gis.utils import LayerMapping
from django.db import transaction, models
from django.forms import ValidationError
from django.utils.timezone import make_aware
from django.contrib.gis.geos import Point
from joblib import Parallel, delayed
from main.wiki_api import (
    format_monument,
    WLM_QUERIES,
    WIKI_CANDIDATE_TYPES,
    search_commons_cat,
    search_commons_wlm,
    get_revision,
    get_query_template_typologies,
    get_wlm_query,
    execute_query,
)
from main.models import Monument, Picture, Region, Province, Municipality, MunicipalityLookup,  Category, CategorySnapshot, Snapshot, CategorySnapshotError
from main.serializers import ProvinceGeoSerializer, MunicipalityGeoSerializer, RegionGeoSerializer
from django.contrib.gis.db.models.functions import Centroid
from django.core.files import File
import xlsxwriter

logger = logging.getLogger(__name__)


def get_date_snap_wlm(monuments_qs, date, group=None):

    out = (
        monuments_qs.annotate(
            national=models.Value("1"),
            national_name=models.Value("Italy"),
            photographed=models.Case(
                models.When(first_image_date__lte=date, then=models.Value(1)),
                default=models.Value(0),
            ),
            date=models.Value(date),
        )
        .annotate(
            in_contest_int=models.Case(
                models.When(start__lte=date, photographed=0, then=models.Value(1)),
                default=models.Value(0),
            )
        )
        .annotate(
            on_wiki=models.Case(
                models.When(first_revision__lte=date, photographed=0, in_contest=0, then=models.Value(1)),
                default=models.Value(0),
            ),
        )
    )

    if group:
        values = group if type(group) is list else [group]
        values = values + ["date"]
    else:
        values = ["date"]

    out = (
        out.values(*values)
        .order_by()
        .annotate(
            on_wiki=models.Sum("on_wiki", default=0),
            in_contestx=models.Sum("in_contest_int", default=0),
            photographed=models.Sum("photographed", default=0),
        )
        .annotate(
            in_contest=models.ExpressionWrapper(
                models.F("in_contestx") + models.F("photographed"), output_field=models.IntegerField()
            ),
            on_wiki=models.ExpressionWrapper(
                models.F("in_contestx") + models.F("photographed") + models.F("on_wiki"),
                output_field=models.IntegerField(),
            ),
        )
    )

    values_final = ["on_wiki", "in_contest", "photographed", "date"]
    if group:
        if type(group) is list:
            values_final += group
        else:
            values_final.append(group)

    out = out.values(*values_final)

    return out


def get_date_snap_commons(monuments_qs, date, group=None):

    out = monuments_qs.annotate(
        national=models.Value("1"),
        national_name=models.Value("Italy"),
        with_picture=models.Case(
            models.When(first_image_date_commons__lte=date, then=models.Value(1)),
            default=models.Value(0),
        ),
        date=models.Value(date),
    ).annotate(
        on_wiki=models.Case(
            models.When(first_revision__lte=date, with_picture=0, then=models.Value(1)),
            default=models.Value(0),
        ),
    )

    if group:
        values = group if type(group) is list else [group]
        values = values + ["date"]
    else:
        values = ["date"]

    out = (
        out.values(*values)
        .order_by()
        .annotate(
            on_wiki=models.Sum("on_wiki", default=0),
            with_picture=models.Sum("with_picture", default=0),
        )
        .annotate(
            on_wiki=models.ExpressionWrapper(
                models.F("with_picture") + models.F("on_wiki"), output_field=models.IntegerField()
            ),
        )
    )

    values_final = ["on_wiki", "with_picture", "date"]
    if group:
        if type(group) is list:
            values_final += group
        else:
            values_final.append(group)

    out = out.values(*values_final)

    return out


def compute_dates(date_from, date_to, step_size, step_unit):
    start = date_from
    dates = []

    if step_unit == "days":
        dates = [start]
        while start < date_to:
            start += relativedelta(days=step_size)
            dates.append(start)
            if len(dates) > 50:
                raise APIException("Too many dates (max 50)")
        if len(dates):
            prev_date = date_from - timedelta(days=1)
            dates.insert(0, prev_date)

    elif step_unit == "months":
        dates_strings = OrderedDict(
            ((date_from + timedelta(_)).strftime(r"%m-%Y"), None) for _ in range((date_to - date_from).days)
        ).keys()
        for item in dates_strings:
            month, year = [int(x) for x in item.split("-")]
            _, last_day = calendar.monthrange(year, month)
            new_date = date(year, month, last_day)
            if new_date <= date_to:
                dates.append(new_date)
        if len(dates):
            prev_date = dates[0] - relativedelta(months=1)
            _, last_day = calendar.monthrange(prev_date.year, prev_date.month)
            dates.insert(0, date(prev_date.year, prev_date.month, last_day))

    elif step_unit == "years":
        dates_strings = OrderedDict(
            ((date_from + timedelta(_)).strftime(r"%Y"), None) for _ in range((date_to - date_from).days)
        ).keys()
        for item in dates_strings:
            year = int(item)
            new_date = date(year, 12, 31)
            if new_date <= date_to:
                dates.append(new_date)
        if len(dates):
            prev_date = dates[0] - relativedelta(years=1)
            dates.insert(0, date(prev_date.year, 12, 31))

    return dates


def get_snap(monuments_qs, date_from, date_to, step_size=1, step_unit="month", group=None, mode="wlm"):
    """
    Please note that "group" parameter is not so `free` as it seems.
    (see format_history method)
    """

    dates = compute_dates(date_from, date_to, step_size, step_unit)

    out = []
    for date in dates:
        if mode == "wlm":
            date_snap = get_date_snap_wlm(monuments_qs, date, group=group)
        elif mode == "commons":
            date_snap = get_date_snap_commons(monuments_qs, date, group=group)
        else:
            raise ValueError(f"Invalid mode: {mode} should be 'wlm' or 'commons'")

        out.append(date_snap)

    flat_list = [item for sublist in out for item in sublist]

    if mode == "wlm":
        keys_map = OrderedDict(
            {
                "photographed": "photographed",
                "in_contest": "inContest",
                "on_wiki": "onWiki",
            }
        )
    else:
        keys_map = OrderedDict(
            {
                "with_picture": "withPicture",
                "on_wiki": "onWikidataOnly",
            }
        )

    return {"data": format_history(flat_list, keys_map), "extent": min_max_values(flat_list, keys_map)}


def min_max_values(flat_list, keys_map):
    out = []

    for k in keys_map:
        values = [item[k] for item in flat_list if item[k] is not None]
        if not len(values):
            values = [0]

        datum = {"label": keys_map[k], "value": [min(values), max(values)]}
        out.append(datum)
    return out


def format_history(history, keys_map):
    def get_type(item):
        for key in ["region", "province", "municipality", "national"]:
            if key in item:
                return key
        return None

    def transform_key_values(item):
        out = {"date": item["date"], "groups": []}

        for key in keys_map:
            out["groups"].append({"label": keys_map[key], "value": item[key]})

        return out

    def reducer(acc, item):
        item_type = get_type(item)
        if not item_type:
            return acc

        # for items with no code, we use 0, otherwise the "sorted" function will not work
        code = item[item_type] or 0
        if item_type != "national":
            label = item[item_type + "__name"]
        else:
            label = "Italia"

        data_item = transform_key_values(item)
        if code not in acc:
            acc[code] = {"meta": {"label": label, "code": code, "type": item_type}, "data": [data_item]}
        else:
            acc[code]["data"] += [data_item]

        return acc

    out_dict = functools.reduce(reducer, history, {})

    def make_entry(dict_entry):
        return {**dict_entry["meta"], "history": dict_entry["data"][1:], "previous": dict_entry["data"][0]}

    # sorting entries with respect to the last value of the "on_wiki" data point (areas with more monuments on wiki are on top)
    def get_max_value(key):
        item = out_dict[key]
        if "data" not in item:
            return inf

        if not len(item["data"]):
            return inf

        if "groups" not in item["data"][-1]:
            return inf

        if not len(item["data"][-1]["groups"]):
            return inf

        if item["data"][-1]["groups"][-1]["value"] is None:
            return inf

        return -item["data"][-1]["groups"][-1]["value"]

    entries = [out_dict[key] for key in sorted(out_dict.keys(), key=get_max_value)]
    out = [make_entry(entry) for entry in entries]
    return out
    return out[0], out[1:]


def get_img_url(title):
    return "https://commons.wikimedia.org/wiki/Special:Filepath/" + title.replace("File:", "")


def get_image_title(url):
    return "File:" + url.replace("https://commons.wikimedia.org/wiki/Special:Filepath/", "")


def monument_prop(monument_data, prop, default=None):
    value = monument_data.get(prop, None)
    if value is None:
        return default

    if isinstance(value, list):
        if not len(value):
            return default
        return min(value) or default

    return value


def update_image(monument, image_data, image_type, is_relevant=False):

    
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
            image_type=image_type,
            monument=monument,
            image_date=image_date,
            image_url=image_url,
            image_title=image_title,
            data=image_data,
            is_relevant=is_relevant,
        )
    except Picture.DoesNotExist:
        picture = Picture.objects.create(
            image_id=image_id,
            image_type=image_type,
            monument=monument,
            image_date=image_date,
            image_url=image_url,
            image_title=image_title,
            data=image_data,
            is_relevant=is_relevant,
        )
    
    return picture


def parse_point(point_str):
    return point_str.upper().replace("POINT(", "").replace(")", "").split(" ")

def get_administrative_areas(position, admin_entity=None):
    """
    
    """
    if admin_entity is not None:
        municipalities = get_wikidata_municipalities()
        if admin_entity in municipalities:
            municipality_istat = int(municipalities[admin_entity])
            try:
                municipality = Municipality.objects.get(
                   code=municipality_istat,
                )
                province = municipality.province
                region = province.region
                logger.info(f"geo areas updated from admin_entity ({admin_entity})")
                return {"municipality":municipality, "province":province, "region":region}

            except Municipality.DoesNotExist:
                pass

    if not position:
        return None

    try:
        municipality_look = MunicipalityLookup.objects.get(
            poly__contains=position,
        )
        municipality = Municipality.objects.get(
            code=municipality_look.code,
        )
        province = municipality.province
        region = province.region
        logger.info(f"geo areas updated from geo lookup (position)")
        return {"municipality":municipality, "province":province, "region":region}
    except MunicipalityLookup.DoesNotExist:
        return None


@transaction.atomic
def update_monument(
    monument_data, category_snapshot, skip_pictures=False, skip_geo=False, category_only=True, reset_pictures=False
):
    category = category_snapshot.category
    
    code = monument_data.get("mon", None)
    if not code:
        raise ValueError("CANNOT UPDATE MONUMENT")

    try:
        monument = Monument.objects.get(q_number=code, snapshot=category_snapshot.snapshot)
        monument.categories.add(category)
        logger.log(logging.INFO, f"Skipping update for monument {code} - already updated in this snapshot")
        return monument

    except Monument.DoesNotExist:
        pass
    
    logger.log(logging.INFO, f"Updating monument {code}")

    label = monument_prop(monument_data, "monLabel", "")
    wlm_n = monument_prop(monument_data, "wlm_n", "")
    start = monument_prop(monument_data, "start_n", None)
    end = monument_prop(monument_data, "end_n", None)
    parent_q_number = monument_prop(monument_data, "parent_n", "")

    relevant_images = monument_data.get("relevantImage_n", [])

    geo_n = monument_prop(monument_data, "geo_n", None)
    try:
        coords = parse_point(geo_n)
        lng = coords[0]
        lat = coords[1]

        position = Point(float(lng), float(lat))
    except Exception as e:
        position = None

    first_revision = get_revision(code)

    approved_by = monument_data.get("approvedBy_n", "")
    article = monument_prop(monument_data, "article", "")
    location = monument_prop(monument_data, "locationLabel", "")
    address = monument_prop(monument_data, "address", "")
    admin_entity = monument_prop(monument_data, "adminEntity", "")
    

    defaults = {
        "label":label,
        "wlm_n":wlm_n,
        "start":start,
        "end":end,
        "position":position,
        "data":monument_data,
        "first_revision":first_revision,
        "snapshot":category_snapshot.snapshot,
        "parent_q_number":parent_q_number,
        "relevant_images":relevant_images,
        "approved_by":approved_by,
        "article":article,
        "location":location,
        "address": address,
        "admin_entity": admin_entity,
    }

    if not skip_geo:
        administrative_areas = get_administrative_areas(position, admin_entity)
        if administrative_areas is not None:
            defaults.update(administrative_areas)

    monument, created = Monument.objects.update_or_create(
        q_number=code,
        defaults=defaults
    )
    
    #categories are cleared by the method update_category
    monument.categories.add(category)

    if reset_pictures:
        logger.info(f"resetting pictures for {code}")
        monument.pictures.all().delete()
        monument.first_image_date = None
        monument.first_image_date_commons = None

    wlm_pics_collected = 0
    commons_pics_collected = 0
    if not skip_pictures:
        logger.info(f"Updating pictures for {code}")
        if monument_data.get("commons_n"):
            for cat in monument_data.get("commons_n"):
                commons_image_data = search_commons_cat(monument.q_number, cat)
                for image in commons_image_data:
                    title = image.get("title", "")
                    if title:
                        title = title.split("File:")[-1]
                    else:
                        continue
                    
                    is_relevant = False
                    for relevant_image_url in relevant_images:
                        file_path = relevant_image_url.split("FilePath/")[-1]
                        if title == file_path:
                            is_relevant = True
                            break
                    update_image(monument, image, "commons", is_relevant)
                    commons_pics_collected += 1

        if wlm_n:
            images = search_commons_wlm(monument.q_number, wlm_n)
            #logger.info(f"found {len(images)} wlm images for {code}")
            for image in images:
                update_image(monument, image, "wlm")
                wlm_pics_collected += 1

        aggregates = monument.pictures.filter(image_type="wlm").aggregate(first_image_date=models.Min("image_date"), last_image_date=models.Max("image_date"))
        monument.first_image_date = aggregates["first_image_date"]
        monument.most_recent_wlm_image_date = aggregates["last_image_date"]

        aggregates = monument.pictures.all().aggregate(first_image_date=models.Min("image_date"), last_image_date=models.Max("image_date"))
        monument.first_image_date_commons = aggregates["first_image_date"]
        monument.most_recent_commons_image_date = aggregates["last_image_date"]

        monument.save()

    # updating current states
    monument.refresh_from_db()
    if monument.first_image_date and monument.first_image_date <= monument.snapshot.created.date():
        monument.current_wlm_state = "photographed"
    elif monument.start and monument.start <= monument.snapshot.created:
        monument.current_wlm_state = "inContest"
    else:
        monument.current_wlm_state = "onWiki"

    if monument.first_image_date_commons and monument.first_image_date_commons <= monument.snapshot.created.date():
        monument.current_commons_state = "withPicture"
    else:
        monument.current_commons_state = "onWikidataOnly"

    if not skip_pictures:
        monument.pictures_wlm_count = wlm_pics_collected
        monument.pictures_commons_count = commons_pics_collected
        monument.pictures_count = monument.pictures.all().count()
        if wlm_pics_collected > 0 and commons_pics_collected == 0:
            monument.to_review = True

    # computing "in_contest" flag
    if not monument.start:
        monument.in_contest = False
    else:
        if not monument.end:
            monument.in_contest = True
        else:
            try:
                today = date.today().isoformat()
                if str(monument.end) >= today:
                    monument.in_contest = True
                else:
                    monument.in_contest = monument.end < monument.start
            except Exception as e:
                monument.in_contest = monument.end < monument.start
    
    monument.save()

    return monument


def update_category(
    monuments, category_snapshot, skip_pictures=False, skip_geo=False, category_only=False, reset_pictures=False
):
    

    def process_monument(monument):
        try:
            update_monument(
                monument,
                category_snapshot,
                skip_pictures=skip_pictures,
                skip_geo=skip_geo,
                category_only=category_only,
                reset_pictures=reset_pictures,
            )
        except Exception as e:
            logger.exception(e)
    Parallel(n_jobs=3, prefer="threads")(delayed(process_monument)(mon) for mon in monuments)
    



@retry(tries=1, delay=45)
def get_category_snapshot_payload(cat_snapshot):
    logger.info(f"get_category_snapshot_payload {cat_snapshot.category.label}")
    if not cat_snapshot.payload:
        logger.info(f"running sparql for {cat_snapshot.category.label}")
        should_run = True
        data = []
        offset = 0
        while should_run:
            logger.info(f"offset {offset}")

            @retry(tries=15, delay=25)
            def inner_call():
                out = execute_query(cat_snapshot.query, limit=5000, offset=offset)
                return out

            results = inner_call()
            
            run_data = results["results"]["bindings"]
            data += run_data

            if len(run_data) < 5000:
                should_run = False
            else:
                offset += 5000
                logger.info("sleeping 15 seconds")
                time.sleep(15)
            
        logger.info("query ok")
        cat_snapshot.payload = data
        cat_snapshot.save()


def process_category_snapshot(
    cat_snapshot, skip_pictures=False, skip_geo=False, category_only=False, reset_pictures=False
):
    logger.info(f"process_category_snapshot {cat_snapshot.category.label}")
    if not cat_snapshot.payload:
        try:
            get_category_snapshot_payload(cat_snapshot)
        except Exception as e:
            logger.exception("Error while getting category snapshot payload")
            CategorySnapshotError.objects.create(
                snapshot = cat_snapshot.snapshot,
                category_name = cat_snapshot.category.label,
                category_query = cat_snapshot.query,
                error = str(e),
                
            )
            raise e
    
    #logger.info("exiting in debug, please remove")
    #return 

    monuments = [format_monument(x) for x in cat_snapshot.payload]
    monuments_q_numbers = [x.get('mon', None) for x in monuments]
    monuments_q_numbers = [x for x in monuments_q_numbers if x is not None]
    logger.info(f"found {len(monuments_q_numbers)} monuments for {cat_snapshot.category.label}")

    logger.info(f"removing category {cat_snapshot.category.label} for not matched monuments")
    Monument.categories.through.objects.filter(
        category=cat_snapshot.category,
    ).exclude(
        monument__q_number__in=monuments_q_numbers
    ).delete()

    
    logger.info(f"adding category {cat_snapshot.category.label} for monuments already updated in the snapshot")
    already_updated_monuments = Monument.objects.filter(
        snapshot=cat_snapshot.snapshot,
        q_number__in=monuments_q_numbers
    )
    for mon in already_updated_monuments:
        mon.categories.add(cat_snapshot.category)

    logger.info(f"filtering new monuments for {cat_snapshot.category.label}")
    already_updated_monuments_q_numbers = [x.q_number for x in already_updated_monuments]
    new_monuments = [x for x in monuments if x.get('mon', None) not in already_updated_monuments_q_numbers]
        
    update_category(
        new_monuments,
        cat_snapshot,
        skip_pictures=skip_pictures,
        skip_geo=skip_geo,
        category_only=category_only,
        reset_pictures=reset_pictures,
    )


def update_geo_from_parents():
    """tries to update missing municipalies, provinces and regions on all the dataset, for monuments with parents"""
    for monument in Monument.objects.filter(models.Q(position=None) | models.Q(municipality=None)).exclude(
        parent_q_number=""
    ):
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


def update_geo_areas(all=False):
    """tries to update missing municipalities, provinces and regions on all the dataset"""
    qs = Monument.objects.all()
    if not all:
        qs = qs.filter(municipality=None)

    logger.info("Updating geo areas for " + str(qs.count()) + " monuments")
    for monument in qs:
        administrative_areas = get_administrative_areas(monument.position, monument.admin_entity)
        if administrative_areas:
            monument.municipality = administrative_areas["municipality"]
            monument.province = administrative_areas["province"]
            monument.region = administrative_areas["region"]
            monument.save()
            logger.info(f"updated {monument.q_number} administrative areas")
        else:
            logger.info(f"no administrative areas for {monument.q_number}")
        


def take_snapshot(skip_pictures=False, skip_geo=False, force_restart=False, category_only=False, reset_pictures=True):
    """
    New monuments + Update to monuments data
    New Approved/Unapproved monuments
    New pictures
    Aggregate data on geographic entities #TODO: evaluate on-the-fly aggregation with aggressive caching (break on import and pre-caching)
    """
    pending_snapshots = Snapshot.objects.filter(complete=False).order_by("-created")
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
    # creating CategorySnapshot
    for item in WLM_QUERIES + WIKI_CANDIDATE_TYPES:

        category = Category.objects.get_or_create(label=item["label"])[0]
        category.q_number = item["q_number"]
        if "group" in item:
            category.group = item["group"]
        category.save()

        if "query_file" in item:
            query = get_wlm_query(item["query_file"])
        else:
            typologies_query = get_query_template_typologies()
            type_to_search = "wd:" + item["q_number"] + " # " + item["label"]
            query = re.sub("wd:Q_NUMBER_TYPE", type_to_search, typologies_query)

        cat_snapshot = CategorySnapshot.objects.get_or_create(category=category, snapshot=snapshot, query=query)[0]
        logger.info(cat_snapshot)
        categories_snapshots.append(cat_snapshot)

    all_q_numbers = []
    
    cats_errors = []
    #trying first to get the payload for all the categories
    for cat_snapshot in categories_snapshots:        
        if not cat_snapshot.payload:
            try:
                get_category_snapshot_payload(cat_snapshot)
            except Exception as e:
                logger.exception("Error while getting category snapshot payload")
                CategorySnapshotError.objects.create(
                    snapshot = cat_snapshot.snapshot,
                    category_name = cat_snapshot.category.label,
                    category_query = cat_snapshot.query,
                    error = str(e),
                    
                )
                cats_errors.append(cat_snapshot.category.label)
    
    # updating categories.
    # the method process_category_snapshot will retry to get payload if not present
    # this is useful for debugging, as it allows to run the method multiple times without restarting all the snapshot
    # by removing the payload by the category snapshots.

    for cat_snapshot in categories_snapshots:        
        if not cat_snapshot.complete:
            try:
                process_category_snapshot(
                    cat_snapshot,
                    skip_pictures=skip_pictures,
                    skip_geo=skip_geo,
                    category_only=category_only,
                    reset_pictures=reset_pictures,
                )
                cat_snapshot.complete = True
                cat_snapshot.save()
                if cat_snapshot.category.label in cats_errors:
                    cats_errors = [x for x in cats_errors if x != cat_snapshot.category.label]
            
            except Exception as e: 
                if cat_snapshot.category.label not in cats_errors:
                    cats_errors.append(cat_snapshot.category.label)
                continue
        
        monuments_data = [format_monument(x) for x in cat_snapshot.payload]
        qs = [x.get('mon', None) for x in monuments_data]
        all_q_numbers += list(set(qs))
        
    has_errors = len(cats_errors) > 0

    if not has_errors:
        #deleting monuments that are not referenced by sparql. 
        #could be a large query but postgres should handle it gracefully
        #monuments_to_delete = Monument.objects.exclude(q_number__in=all_q_numbers)
        logger.info(f"deleting monuments missing in snapshot -- disabled now")
        #monuments_to_delete.delete()
    

    # fixing empty positions
    if not skip_geo and not has_errors:
        logger.info("updating geo")
        update_geo_from_parents()

    if not has_errors:
        snapshot.complete = True
        snapshot.save()
        snapshot.category_snapshots.all().delete()

        #dropping old monuments .. should have be dropped in advance by the previous procedure
        #logger.info(f"deleting monuments missing in snapshot")
        #Monument.objects.exclude(snapshot__pk=snapshot.pk).delete()

        # creating csv and xlsx full exports
        create_export(snapshot)

        # clearing view cache
        caches["views"].clear()


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



class ExtraKwargsLayerMapping(LayerMapping):
    """
    This is an extension to django LayerMapping allowing custom kwargs to be passed to the model constructor
    (as constants as they don't change for each feature). Not really used, but could be useful in the future.
    """
    def __init__(self, *args, **kwargs):
        self.extra_kwargs = kwargs.pop("extra_kwargs", {})
        super().__init__(*args, **kwargs)

    def feature_kwargs(self, feature):
        kwargs = super().feature_kwargs(feature)
        if self.extra_kwargs:
            kwargs.update(self.extra_kwargs)
        return kwargs


def update_regions(shape_path, extra_kwargs=None):
    logger.info(f"updating regions from shapefile {shape_path}")
    mapping = {
        "name": "DEN_REG",
        "code": "COD_REG",
        "poly": "POLYGON",
    }
    lm = ExtraKwargsLayerMapping(Region, shape_path, mapping, extra_kwargs=extra_kwargs)
    qs = Region.objects.all()
    if extra_kwargs:
        qs = qs.filter(**extra_kwargs)
    qs.delete()
    lm.save()


def update_provinces(shape_path, extra_kwargs=None):
    logger.info(f"updating provinces from shapefile {shape_path}")
    mapping = {
        "name": "DEN_UTS",
        "code": "COD_PROV",
        "region_code": "COD_REG",
        "poly": "POLYGON",
    }
    lm = ExtraKwargsLayerMapping(Province, shape_path, mapping, extra_kwargs=extra_kwargs)
    qs = Province.objects.all()
    if extra_kwargs:
        qs = qs.filter(**extra_kwargs)
    qs.delete()
    lm.save()


def update_municipalities(shape_path, extra_kwargs=None):
    logger.info(f"updating municipalities from shapefile {shape_path}")
    mapping = {
        "name": "COMUNE",
        "code": "PRO_COM",
        "province_code": "COD_PROV",
        "region_code": "COD_REG",
        "poly": "POLYGON",
    }
    lm = ExtraKwargsLayerMapping(Municipality, shape_path, mapping, extra_kwargs=extra_kwargs)
    qs = Municipality.objects.all()
    if extra_kwargs:
        qs = qs.filter(**extra_kwargs)
    qs.delete()
    lm.save()


def update_municipalities_lookup(shape_path, extra_kwargs=None):
    logger.info(f"updating municipalities (lookup version) from shapefile {shape_path}")
    mapping = {
        "name": "COMUNE",
        "code": "PRO_COM",
        "province_code": "COD_PROV",
        "region_code": "COD_REG",
        "poly": "POLYGON",
    }
    lm = ExtraKwargsLayerMapping(MunicipalityLookup, shape_path, mapping, extra_kwargs=extra_kwargs)
    qs = MunicipalityLookup.objects.all()
    if extra_kwargs:
        qs = qs.filter(**extra_kwargs)
    qs.delete()
    lm.save()


@transaction.atomic
def update_geo(regions_path, provinces_path, municipalities_path, municipalities_lookup_path, extra_kwargs=None):
    """
    Updates the geographic entities
    No historical tracking of changes
    # TODO: UNDERSTAND HOW TO HANDLE PREVIOUS AGGREGATIONS
    # PROBABLY: we should drop and recompute stats for each snapshot. or use on the-fly aggregation + (pre-)caching.
    Potientially this could "move" a Monument from one municipality (or indirectly province or region) to another.
    """
    update_regions(regions_path, extra_kwargs=extra_kwargs)
    update_provinces(provinces_path, extra_kwargs=extra_kwargs)
    update_municipalities(municipalities_path, extra_kwargs=extra_kwargs)
    update_municipalities_lookup(municipalities_lookup_path, extra_kwargs=extra_kwargs)

    provinces = Province.objects.all()
    if extra_kwargs:
        provinces = provinces.filter(**extra_kwargs)
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
    if extra_kwargs:
        municipalities = municipalities.filter(**extra_kwargs)
    for municipality in municipalities:
        logger.info(f"update municipality {municipality.name}")
        municipality.province = provinces_by_code[municipality.province_code]
        municipality.region = regions_by_code[municipality.region_code]
        updated_municipalities.append(municipality)
    Municipality.objects.bulk_update(updated_municipalities, ["province", "region"])

    # updating centroids
    Region.objects.all().annotate(c=Centroid("poly")).update(centroid=models.F("c"))
    Province.objects.all().annotate(c=Centroid("poly")).update(centroid=models.F("c"))
    Municipality.objects.all().annotate(c=Centroid("poly")).update(centroid=models.F("c"))


def update_geo_cache():
    """ """
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
    first_image = (
        Picture.objects.filter(
            monument__pk=models.OuterRef("pk"),
        )
        .order_by()
        .values("monument__pk")
        .annotate(
            first_image=models.Min("image_date", default=None),
        )
        .values("first_image")[:1]
    )

    monuments = Monument.objects.annotate(
        first_image=models.Subquery(first_image),
    )

    monuments.update(first_image_date=models.F("first_image"))


EXPORT_MONUMENTS_HEADER = [
    "id",
    "pictures",
    "pictures_wlm",
    "label",
    "q_number",
    "wlm_id",
    "wlm_auth_start_date",
    "wlm_auth_end_date",
    "approved_by",
    "position",
    "wikidata_creation_date",
    "first_wlm_image_date",
    "first_commons_image_date",
    "most_recent_wlm_image_date",
    "most_recent_commons_image_date",
    "municipality_code",
    "province_code",
    "region_code",
    "municipality_label",
    "province_label",
    "region_label",
    "current_wlm_state",
    "current_commons_state",
    "categories",
]


class MonumentExportSerializer(serializers.ModelSerializer):

    pictures = serializers.IntegerField(source="pictures_count")
    pictures_wlm = serializers.IntegerField(source="pictures_wlm_count")
    wlm_id = serializers.CharField(source="wlm_n")
    wlm_auth_start_date = serializers.DateTimeField(source="start")
    wlm_auth_end_date = serializers.DateTimeField(source="end")
    position = serializers.SerializerMethodField()

    def get_position(self, obj):
        if obj.position:
            return f"{obj.position.y}, {obj.position.x}"
        return ""

    wikidata_creation_date = serializers.DateTimeField(source="first_revision")
    first_commons_image_date = serializers.DateField(source="first_image_date_commons")
    first_wlm_image_date = serializers.DateField(source="first_image_date")
    municipality_code = serializers.CharField(source="municipality.code", required=False)
    province_code = serializers.CharField(source="province.code", required=False)
    region_code = serializers.CharField(source="region.code", required=False)
    municipality_label = serializers.CharField(source="municipality.name", required=False)
    province_label = serializers.CharField(source="province.name", required=False)
    region_label = serializers.CharField(source="region.name", required=False)

    categories = serializers.SerializerMethodField()
    def get_categories(self, obj):
        cats = list(obj.categories.order_by('label').values_list("label", flat=True))
        return ", ".join(cats)

    class Meta:
        model = Monument
        fields = [
            "id",
            "pictures",
            "pictures_wlm",
            "label",
            "q_number",
            "wlm_id",
            "wlm_auth_start_date",
            "wlm_auth_end_date",
            "approved_by",
            "position",
            "wikidata_creation_date",
            "first_wlm_image_date",
            "first_commons_image_date",
            "most_recent_wlm_image_date",
            "most_recent_commons_image_date",
            "municipality_code",
            "province_code",
            "region_code",
            "municipality_label",
            "province_label",
            "region_label",
            "current_wlm_state",
            "current_commons_state",
            "categories",
        ]


def serialize_monument_for_export(monument):
    serializer = MonumentExportSerializer(monument)
    return serializer.data


def serialize_monuments_for_export(monuments):
    return [{"id":x.id} for x in monuments]
    serializer = MonumentExportSerializer(monuments, many=True)
    return serializer.data

def create_export(snapshot):
    """
    Creates a CSV and XLSX export of the snapshot
    """

    logger.info(f"creating xlsx and csv exports for snapshot {snapshot}")

    with tempfile.TemporaryFile() as xlsx_file:
        with tempfile.TemporaryFile(mode="w+t") as csv_file:
            workbook = xlsxwriter.Workbook(xlsx_file)
            worksheet = workbook.add_worksheet()
            for index, field in enumerate(EXPORT_MONUMENTS_HEADER):
                worksheet.write(0, index, field)

            csv_writer = csv.DictWriter(csv_file, EXPORT_MONUMENTS_HEADER, delimiter=";")
            csv_writer.writeheader()

            monuments = Monument.objects.filter(
                    snapshot=snapshot, 
                    #municipality__isnull=False
                ).select_related("region", "province", "municipality").prefetch_related('categories').order_by("id")
            
            page_size = 100
            for idx, monument in enumerate(monuments.iterator(page_size)):
                row = serialize_monument_for_export(monument)
                csv_writer.writerow(row)
                worksheet.write_row(idx+1, 0, [row.get(field, '') for field in EXPORT_MONUMENTS_HEADER])


            # finalizing exports
            workbook.close()

            xlsx_file.seek(0)
            file_wrapper_xlsx = File(xlsx_file)
            snapshot.xlsx_export.save("monuments.xlsx", file_wrapper_xlsx)

            csv_file.seek(0)
            file_wrapper_csv = File(csv_file)
            snapshot.csv_export.save("monuments.csv", file_wrapper_csv)

    snapshot.save()
    logger.info(f"created xlsx and csv exports for snapshot {snapshot}")




@retry(tries=5, delay=15)
def get_wikidata_municipalities():
    """
    Cached Lookup for municipalities q numbers
    updated once a day
    """

    #last_snapshot = Snapshot.objects.filter(complete=True).order_by("-created").first()
    today = date.today().isoformat()
    cache_key = f"wikidata_monuments-municipalities-{today}"
    cache_value = cache.get(cache_key)
    if cache_value:
        #logger.info(f"Getting muncipalities from cache of {today}")
        return cache_value

    SPARQL_MUNICIPALITIES = """

    SELECT
    ?comune
    ( SAMPLE( ?comuneLabel    ) AS ?comuneLabel    )
    ( SAMPLE( ?comuneIstat    ) AS ?comuneIstat    )
    WHERE
    {

    {
        # i comuni italiani
        ?comune wdt:P31 wd:Q747074.
    } UNION {
        # ed in comuni "sparsi" 
        ?comune wdt:P31 wd:Q954172.
    }

    # solo i comuni con codice ISTAT e posizione
    ?comune wdt:P635 ?comuneIstat;
            wdt:P625 ?position.

    # non voglio i comuni "defunti"
    MINUS { ?comune pq:P582 ?comuneDef }

    ?comune  rdfs:label ?comuneLabel.
    FILTER( LANG( ?comuneLabel  ) = "it" ).

    }
    GROUP BY ?comune
    ORDER BY ?comuneLabel
    
    """
    logger.info("Getting muncipalities from wikidata")
    results = execute_query(SPARQL_MUNICIPALITIES)
    data = results["results"]["bindings"]

    municipalities = {}
    for _result in data:
        result = format_monument(_result)
        q_number = monument_prop(result, "comune", "")
        comuneIstat = int(monument_prop(result, "comuneIstat", ""))
        municipalities[q_number]  = comuneIstat
    
    cache.set(cache_key, municipalities, 60*60*24)
    return municipalities
                            




