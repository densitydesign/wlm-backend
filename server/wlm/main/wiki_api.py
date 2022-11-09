import re
import os
from pathlib import Path
import requests
import time
import csv
import urllib.parse

CURRENT_DIR = Path(__file__).resolve().parent
SPARQL_URL = "https://query.wikidata.org/sparql"
COMMONS_URL = "https://commons.wikimedia.org/w/api.php"
API_URL = "https://www.wikidata.org/w/api.php"


def load_wiki_candidate_types():
    file_path = CURRENT_DIR / "WIKI_CANDIDATE_TYPES.csv"
    with open(file_path, "r") as f:
        reader = csv.DictReader(f, delimiter=",")
        return list(reader)


WIKI_CANDIDATE_TYPES = load_wiki_candidate_types()

WLM_QUERIES = [
    {"label": "in contest", "query_file" : "SPARQL-contest.txt", "q_number": "W0", "group": "Contest"},
    {"label": "municipality overview picture", "query_file" : "SPARQL-municipalities-views.txt", "q_number": "W1", "group": "Contest"},
    {"label": "fortificazioni (IIC 2022)", "query_file" : "SPARQL-fortifications.txt", "q_number": "W2", "group": "Contest"},
]

def get_wlm_query(query_file):
    SPARQL_CONTEST_PATH = CURRENT_DIR / query_file
    with open(SPARQL_CONTEST_PATH, "r") as f:
        QUERY_TEMPLATE = f.read()
        f.close()
    return QUERY_TEMPLATE


def get_query_template_typologies():
    SPARQL_TYPOLOGIES_PATH = CURRENT_DIR / "SPARQL-typologies.txt"
    with open(SPARQL_TYPOLOGIES_PATH, "r") as f:
        QUERY_TEMPLATE = f.read()
        f.close()
    return QUERY_TEMPLATE


def execute_query(query):
    r = requests.get(SPARQL_URL, params={"format": "json", "query": query}, timeout=200)
    
    try:
        return r.json()
    except Exception as e:
        raise e


def format_monument(monument):
    out = {}
    for key in monument:
        value = monument[key]["value"]
        # clean q_numbers
        if "http://www.wikidata.org/entity/" in value:
            value = value.replace("http://www.wikidata.org/entity/", "")
        # split lists into arrays
        if key.endswith("_n"):
            if value == "":
                value = []
            else:
                value = value.split(";")
        out[key] = value
    return out


def search_commons_url(url):    

    filename = url.split("FilePath/")[-1]
    payload = {
        "action": "query",
        "format": "json",
        "prop": "imageinfo",
        "generator": "search",
        "iiprop": "extmetadata",
        "gsrsearch": f"prefix:file:{filename}"
        
    }
    params = "&".join("%s=%s" % (k,v) for k,v in payload.items())
    r = requests.get(COMMONS_URL, params)
    data = r.json()
    
    if "query" in data and "pages" in data["query"] and len(data["query"]["pages"]) > 0:
        images_data_clean = []
        for pageid in data["query"]["pages"]:
            image = data["query"]["pages"][str(pageid)]
            temp_obj = {}
            if "pageid" in image:
                temp_obj["pageid"] = image["pageid"]
            if "title" in image:
                temp_obj["title"] = image["title"]
            if "imageinfo" in image and len(image["imageinfo"]) > 0 and "extmetadata" in image["imageinfo"][0]:
                extmetadata = image["imageinfo"][0]["extmetadata"]
                if "DateTimeOriginal" in extmetadata and "value" in extmetadata["DateTimeOriginal"]:
                    temp_obj["DateTimeOriginal"] = extmetadata["DateTimeOriginal"]["value"]
                if "DateTime" in extmetadata and "value" in extmetadata["DateTime"]:
                    temp_obj["DateTime"] = extmetadata["DateTime"]["value"]

            images_data_clean.append(temp_obj)
        return images_data_clean
    else:
        return []


def search_commons_wlm(wlm_id):
    params = {
        "action": "query",
        "format": "json",
        "prop": "imageinfo",
        "generator": "search",
        "iiprop": "extmetadata",
        "gsrsearch": '"' + wlm_id + '"',
        "gsrnamespace": "6",
        "gsrlimit": "500",
    }
    r = requests.get(COMMONS_URL, params)
    data = r.json()
    if "query" in data and "pages" in data["query"] and len(data["query"]["pages"]) > 0:
        images_data_clean = []
        for pageid in data["query"]["pages"]:
            image = data["query"]["pages"][str(pageid)]
            temp_obj = {}
            if "pageid" in image:
                temp_obj["pageid"] = image["pageid"]
            if "title" in image:
                temp_obj["title"] = image["title"]
            if "imageinfo" in image and len(image["imageinfo"]) > 0 and "extmetadata" in image["imageinfo"][0]:
                extmetadata = image["imageinfo"][0]["extmetadata"]
                if "DateTimeOriginal" in extmetadata and "value" in extmetadata["DateTimeOriginal"]:
                    temp_obj["DateTimeOriginal"] = extmetadata["DateTimeOriginal"]["value"]
                if "DateTime" in extmetadata and "value" in extmetadata["DateTime"]:
                    temp_obj["DateTime"] = extmetadata["DateTime"]["value"]

            images_data_clean.append(temp_obj)
        return images_data_clean
    else:
        return []



def search_commons(id, is_commons=False):
    params = {
        "action": "query",
        "format": "json",
        "prop": "imageinfo",
        "generator": "search",
        "iiprop": "extmetadata",    
        "gsrnamespace": "6",
    }

    if not is_commons:
        params["gsrsearch"] = '"' + id + '" "Wiki Loves Monuments Italia"',
    else:
        params["titles"] = '"' + id + '" "Wiki Loves Monuments Italia"',
        

    r = requests.get(COMMONS_URL, params)
    data = r.json()
    if "query" in data and "pages" in data["query"] and len(data["query"]["pages"]) > 0:
        images_data_clean = []
        for pageid in data["query"]["pages"]:
            image = data["query"]["pages"][str(pageid)]
            temp_obj = {}
            if "pageid" in image:
                temp_obj["pageid"] = image["pageid"]
            if "title" in image:
                temp_obj["title"] = image["title"]
            if "imageinfo" in image and len(image["imageinfo"]) > 0 and "extmetadata" in image["imageinfo"][0]:
                extmetadata = image["imageinfo"][0]["extmetadata"]
                if "DateTimeOriginal" in extmetadata and "value" in extmetadata["DateTimeOriginal"]:
                    temp_obj["DateTimeOriginal"] = extmetadata["DateTimeOriginal"]["value"]
                if "DateTime" in extmetadata and "value" in extmetadata["DateTime"]:
                    temp_obj["DateTime"] = extmetadata["DateTime"]["value"]

            images_data_clean.append(temp_obj)
        #print("\tFound", len(images_data_clean), "photos")
        
        return images_data_clean
    else:
        #print("\tFound no photos")
        return []


def get_revision(q):
    
    params = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "titles": q,
        "rvprop": "timestamp",
        "rvlimit": "1",
        "rvdir":"newer"
      }
    r = requests.get(API_URL, params)
    results = r.json()
    pages = results["query"]["pages"]
    keys = list(pages.keys())
    if not len(keys):
        return None
    
    return pages[keys[0]]["revisions"][0]["timestamp"]