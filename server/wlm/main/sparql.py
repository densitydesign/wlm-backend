import re
import os
from pathlib import Path
import requests
import time

CURRENT_DIR = Path(__file__).resolve().parent
SPARQL_URL = "https://query.wikidata.org/sparql"
COMMONS_URL = "https://commons.wikimedia.org/w/api.php"
API_URL = "https://www.wikidata.org/w/api.php"

WIKI_CANDIDATE_TYPES = [
    {"q_number": "Q3950", "label": "villa"},
    # {"q_number": "Q12518", "label": "torre"},
    # {"q_number": "Q57821", "label": "Fortificazione"},
    # {"q_number": "Q179049", "label": "area naturale protetta"},
    # {"q_number": "Q333109", "label": "Überrest"},
    # {"q_number": "Q811534", "label": "pianta monumentale"},
    # {"q_number": "Q1291195", "label": "luogo di scoperta (comprende siti archeologici)"},
    # {"q_number": "Q2065736", "label": "bene culturale"},
    # {"q_number": "Q2232001", "label": "grotta turistica"},
    # {"q_number": "Q4989906", "label": "monumento"},
    # {"q_number": "Q11331347", "label": "sacro monte"},
    # {"q_number": "Q15069452", "label": "area protetta Natura 2000"},
    # {"q_number": "Q35112127", "label": "edificio storico"},
    # {"q_number": "Q57660343", "label": "performing art buildings"},
    # {"q_number": "Q1030034", "label": "GLAM"},
    # {"q_number": "Q16560", "label": "Palazzo"},
    #{"q_number": "Q24398318", "label": "edificio religioso"},
]


def get_query_template_typologies():
    SPARQL_TYPOLOGIES_PATH = CURRENT_DIR / "SPARQL-typologies.txt"
    with open(SPARQL_TYPOLOGIES_PATH, "r") as f:
        QUERY_TEMPLATE = f.read()
        f.close()
    return QUERY_TEMPLATE


def get_query_template_contest():
    SPARQL_CONTEST_PATH = CURRENT_DIR / "SPARQL-contest.txt"
    with open(SPARQL_CONTEST_PATH, "r") as f:
        QUERY_TEMPLATE = f.read()
        f.close()
    return QUERY_TEMPLATE


def execute_query(query):
    r = requests.get(SPARQL_URL, params={"format": "json", "query": query}, timeout=40)
    
    try:
        return r.json()
    except Exception as e:
        raise e


def get_wlm_monuments():
    wlm_query = get_query_template_contest()
    results = execute_query(wlm_query)
    return results["results"]["bindings"]


def get_wiki_monuments_entity(entity):
    
    typologies_query = get_query_template_typologies()
    type_to_search = "wd:" + entity["q_number"] + " # " + entity["label"]
    compiled_query = re.sub("wd:Q_NUMBER_TYPE", type_to_search, typologies_query)

    # performs request
    entity_results = execute_query(compiled_query)

    # stores data as it is
    if "results" not in entity_results:
        return []
    return entity_results["results"]["bindings"]


def get_wiki_monuments():
    out = []
    for entity in WIKI_CANDIDATE_TYPES:
        entity_results = get_wiki_monuments_entity(entity)
        out = out + entity_results
        time.sleep(5)

    return out


def get_monuments():
    wlm_monuments = [format_monument(mon) for mon in  get_wlm_monuments()]
    wiki_monuments = [format_monument(mon) for mon in  get_wiki_monuments()]
    return wlm_monuments + wiki_monuments
    return wiki_monuments
    


def format_monument(monument):
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
        monument[key] = value
    return monument


def search_commons(wlm_id):
    params = {
        "action": "query",
        "format": "json",
        "prop": "imageinfo",
        "generator": "search",
        "iiprop": "extmetadata",
        "gsrsearch": '"' + wlm_id + '"',
        "gsrnamespace": "6",
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