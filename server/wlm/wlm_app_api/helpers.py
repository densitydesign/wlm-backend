import requests
import re
import datetime
from main.helpers import execute_query, monument_prop, format_monument
from main.models import Monument
from .como_q_numbers import COMO_Q_NUMBERS
from django.core.cache import cache
from retry import retry
import logging
import datetime

logger = logging.getLogger(__name__)


def normalize_value(value):
    v = str(value)
    if v == "" or v.startswith("_:"):
        return None
    else:
        return v


SPARQL_MONUMENT = """
SELECT DISTINCT  ?item ?itemLabel ?itemDescription ?coords ?wlmid ?image ?sitelink ?commons ?regioneLabel ?enddate ?unit ?unitLabel ?address ?approvedby ?endorsedby ?year ?instanceof
    WHERE {

      VALUES ?item { wd:%s } .
      
      ?item p:P2186 ?wlmst .
      ?wlmst ps:P2186 ?wlmid .
      OPTIONAL { ?wlmst pq:P790 ?approvedby . }
      OPTIONAL { ?wlmst pq:P8001 ?endorsedby . }

      ?item wdt:P17 wd:Q38 . 
      ?item wdt:P131 ?unit .
      
      MINUS {?item wdt:P31 wd:Q747074.}
      MINUS {?item wdt:P31 wd:Q954172.}
      MINUS {?item wdt:P31 wd:Q1549591.}
      
      OPTIONAL {?item wdt:P31 ?instanceof }
      OPTIONAL {?item wdt:P625 ?coords. }
      OPTIONAL { ?wlmst pqv:P582 [ wikibase:timeValue ?enddate ] .}
      OPTIONAL { ?wlmst pqv:P585 [ wikibase:timeValue ?year ] .}
      OPTIONAL { ?item wdt:P373 ?commons. }
      OPTIONAL { ?item wdt:P18 ?image. }
      OPTIONAL { ?item wdt:P6375 ?address.}
      OPTIONAL {?sitelink schema:isPartOf <https://it.wikipedia.org/>;schema:about ?item. }
      VALUES ?typeRegion { wd:Q16110 wd:Q1710033 }.

      ?item wdt:P131* ?regione.
      ?regione wdt:P31 ?typeRegion.

      # esclude i monumenti che hanno una data di inizio successiva al termine del concorso
      MINUS {
        ?wlmst pqv:P580 [ wikibase:timeValue ?start ; wikibase:timePrecision ?sprec ] .
        FILTER (
          # precisione 9 è anno
          ( ?sprec >  9 && ?start >= "2023-10-01T00:00:00+00:00"^^xsd:dateTime ) ||
          ( ?sprec < 10 && ?start >= "2023-01-01T00:00:00+00:00"^^xsd:dateTime )
        )
      }
      
      SERVICE wikibase:label { bd:serviceParam wikibase:language "it" }
      }

      LIMIT 1

"""


SPARQL_COMO = """
SELECT DISTINCT ?item
    WHERE {
    ?item wdt:P2186 ?wlmid ;
              wdt:P17 wd:Q38 ;
          VALUES ?lakecomo { wd:Q16161 wd:Q16199} .
    ?item wdt:P131* ?lakecomo .

        MINUS { ?item p:P2186 [ pq:P582 ?end ] .
        FILTER ( ?end <= "2023-09-01T00:00:00+00:00"^^xsd:dateTime )
              }
    SERVICE wikibase:label { bd:serviceParam wikibase:language "it" }
    }

"""


@retry(tries=3, delay=0)
def get_monument_data(q_number):
    monument_data = execute_query(SPARQL_MONUMENT % q_number)
    if len(monument_data["results"]["bindings"]) == 0:
        return None
    monument_data = monument_data["results"]["bindings"][0]
    monument_data = format_monument(monument_data)

    data = {
        "item": monument_prop(monument_data, "item"),
        "regione": monument_prop(monument_data, "regioneLabel"),
        "is_religious": bool(monument_prop(monument_data, "endorsedby")),
        "city_item": normalize_value(monument_prop(monument_data, "unit")),
    }

    return data


def get_como_data():
    como_data = execute_query(SPARQL_COMO)
    como_data = como_data["results"]["bindings"]
    como_data = [format_monument(x) for x in como_data]
    como_data = [monument_prop(x, "item") for x in como_data]
    banned_como = ["Q28375375", "Q24937411", "Q21592570", "Q3862651", "Q3517634", "Q24052892", "Q533156"]
    como_data = [x for x in como_data if x not in banned_como]

    return como_data


VALLE_DEL_PRIMO_PRESEPE = [
    "Q223423",
    "Q223427",
    "Q223434",
    "Q223459",
    "Q223472",
    "Q223476",
    "Q223509",
    "Q224039",
    "Q224043",
    "Q118085",
    "Q224109",
    "Q224144",
    "Q224149",
    "Q224172",
    "Q224211",
    "Q224264",
    "Q224300",
    "Q224333",
    "Q13396",
    "Q224405",
]

TERRE_DELLA_UFITA = ["Q55007", "Q55008", "Q55016", "Q55033", "Q55036", "Q55042", "Q55085", "Q55121", "Q55139"]


def _get_upload_categories(q_number):
    regioni = {
        "Abruzzo": ["Abruzzo", True],
        "Basilicata": ["Basilicata", False],
        "Calabria": ["Calabria", False],
        "Campania": ["Campania", False],
        "Emilia-Romagna": ["Emilia-Romagna", False],
        "Friuli-Venezia Giulia": ["Friuli-Venezia Giulia", True],
        "Lazio": ["Lazio", False],
        "Liguria": ["Liguria", True],
        "Lombardia": ["Lombardy", True],
        "Marche": ["Marche", True],
        "Molise": ["Molise", False],
        "Piemonte": ["Piedmont", True],
        "Puglia": ["Apulia", True],
        "Sardegna": ["Sardinia", False],
        "Sicilia": ["Sicily", False],
        "Toscana": ["Tuscany", True],
        "Trentino-Alto Adige": ["Trentino-South Tyrol", False],
        "Umbria": ["Umbria", True],
        "Valle d'Aosta": ["Aosta Valley", True],
        "Veneto": ["Veneto", False],
    }

    today = datetime.date.today()
    base_cat = f"Images+from+Wiki+Loves+Monuments+{today.year}+in+Italy"

    WIKI_API_URL = f"https://it.wikipedia.org/w/api.php?action=parse&text={{{{%23invoke:WLM|upload_url|{q_number}}}}}&contentmodel=wikitext&format=json"

    response = requests.get(WIKI_API_URL)
    data = response.json()
    baselink = data["parse"]["externallinks"][0]

    mon_url = baselink.replace("(", "%28").replace(")", "%29")
    try:
        monument_data = get_monument_data(q_number)
    except Exception as e:
        return None

    if not monument_data:
        return None
    regarr = regioni.get(monument_data["regione"])

    if monument_data["is_religious"]:
        newstring = "+-+" + regarr[0] + "+-+religious+building"
    else:
        newstring = "+-+" + regarr[0]

    # GETTING monument like here https://github.com/ferdi2005/wikilovesmonuments/blob/319e7b257898fe44d33e1e10868cfb3fb70ed561/app/jobs/import_job.rb

    # como_q_numbers = get_como_data()
    como_q_numbers = COMO_Q_NUMBERS

    if (
        regarr[1] == False
        and monument_data["item"] not in como_q_numbers
        and monument_data.get("city_item", None) not in VALLE_DEL_PRIMO_PRESEPE
        and monument_data.get("city_item", None) not in TERRE_DELLA_UFITA
    ):
        newstring = newstring + "%7C" + base_cat + "+-+" + "without+local+award"

    if monument_data["item"] in como_q_numbers:
        newstring = newstring + "%7C" + base_cat + "+-+" + "Lake+Como"

    if monument_data.get("city_item", None) in VALLE_DEL_PRIMO_PRESEPE:
        newstring = newstring + "%7C" + base_cat + "+-+" + "Valle+del+Primo+Presepe"

    # Terre dell'Uftia
    if monument_data.get("city_item", None) in TERRE_DELLA_UFITA:
        newstring = newstring + "%7C" + base_cat + "+-+" + "Terre+dell%27Ufita"

    mon_url = mon_url.replace("+-+unknown+region", newstring)

    notwlm = baselink
    notwlm = notwlm.replace("(", "%28")  # fix parentesi (
    notwlm = notwlm.replace(")", "%29")  # fix parentesi )
    notwlm = notwlm.replace(" ", "")
    notwlm = notwlm.replace("+-+unknown+region", "")
    notwlm = notwlm.replace("&campaign=wlm-it", "")
    wlm_id = monument_data.get("wlmid", "")
    notwlm = notwlm.replace(f"&id=#{wlm_id}", "")

    # link non partecipante al concorso
    notwlm = re.sub("%7CImages\+from\+Wiki\+Loves\+Monuments\+\d{4}\+in\+Italy", "", notwlm)

    return {
        "uploadurl": mon_url,
        "nonwlmuploadurl": notwlm,
    }


def get_upload_categories(q_number):
    regioni = {
        "Abruzzo": ["Abruzzo", True],
        "Basilicata": ["Basilicata", False],
        "Calabria": ["Calabria", False],
        "Campania": ["Campania", False],
        "Emilia-Romagna": ["Emilia-Romagna", False],
        "Friuli Venezia Giulia": ["Friuli-Venezia Giulia", True],
        "Lazio": ["Lazio", False],
        "Liguria": ["Liguria", True],
        "Lombardia": ["Lombardy", True],
        "Marche": ["Marche", True],
        "Molise": ["Molise", False],
        "Piemonte": ["Piedmont", True],
        "Puglia": ["Apulia", True],
        "Sardegna": ["Sardinia", False],
        "Sicilia": ["Sicily", False],
        "Toscana": ["Tuscany", True],
        "Trentino-Alto Adige": ["Trentino-South Tyrol", False],
        "Umbria": ["Umbria", True],
        "Valle d'Aosta": ["Aosta Valley", True],
        "Veneto": ["Veneto", False],
    }

    today = datetime.date.today()
    wlm_categories = []
    non_wlm_categories = []

    try:
        monument_data = get_monument_data(q_number)
    except Exception as e:
        logger.info("cannot get monument data")
        monument_data = None

    # also look in our db
    monument = Monument.objects.get(q_number=q_number)
    monument_categories = monument.categories.all().values_list("label", flat=True)
    # print(monument_categories)

    # print(monument.data)
    if monument.data and monument.data.get("commons_n", []):
        non_wlm_categories += monument.data.get("commons_n", [])
    elif monument.data and monument.data.get("place_n", []):
        place_n = monument.data.get("place_n")[0]
        cat_sparql = (
            """
        SELECT 
            ?x  
            (group_concat(DISTINCT ?commonsCat; separator=";") as ?commons_s)
            WHERE {
            VALUES  ?x { wd:%s }
            OPTIONAL { ?x wdt:P373 ?commonsCat }
            }

            GROUP BY ?x
        """
            % place_n
        )
        res_cat = execute_query(cat_sparql)
        commons_cats = format_monument(res_cat["results"]["bindings"][0])
        if commons_cats.get("commons_s", None):
            non_wlm_categories += commons_cats["commons_s"].split(";")

    wlm_categories = [x for x in non_wlm_categories]

    base_category = f"Images from Wiki Loves Monuments {today.year} in Italy"
    wlm_categories.append(base_category)

    # WIKI_API_URL = f"https://it.wikipedia.org/w/api.php?action=parse&text={{{{%23invoke:WLM|upload_url|{q_number}}}}}&contentmodel=wikitext&format=json"

    # response = requests.get(WIKI_API_URL)
    # data = response.json()
    # baselink = data["parse"]["externallinks"][0]

    # mon_url = baselink.replace("(", "%28").replace(")", "%29")
    # print(mon_url)

    if "monumental tree" in monument_categories:
        wlm_categories.append(base_category + " - veteran trees")
        non_wlm_categories.append("veteran trees")

    elif "municipality overview picture" in monument_categories:
        wlm_categories.append(base_category + " - cityscapes")
        non_wlm_categories.append("cityscapes")

    elif monument_data and monument_data["is_religious"]:
        wlm_categories.append(base_category + " - religious buildings")
        non_wlm_categories.append("religious buildings")

    else:
        wlm_categories.append(base_category + " - traditional contest")
        non_wlm_categories.append("traditional contest")

    # print (monument.region.name)
    if monument.region:
        region_name = monument.region.name
    else:
        region_name = None
    regarr = regioni.get(region_name, None)
    if regarr:
        regione_category = base_category + " - " + regarr[0]
        wlm_categories.append(regione_category)

        banned_como = ["Q28375375", "Q24937411", "Q21592570", "Q3862651", "Q3517634", "Q24052892", "Q533156"]
        como_q_numbers = [x for x in COMO_Q_NUMBERS if x not in banned_como]

        is_como = q_number.upper() in como_q_numbers or (monument_data and monument_data["item"] in como_q_numbers)
        # is_terre_ufita = q_number.upper() in TERRE_DELLA_UFITA or (monument_data and monument_data['city_item'] in TERRE_DELLA_UFITA)
        is_valle_primo_presepe = q_number.upper() in VALLE_DEL_PRIMO_PRESEPE or (
            monument_data and monument_data["city_item"] in VALLE_DEL_PRIMO_PRESEPE
        )

        avellino_q_numbers = get_wikidata_avellino()
        is_avellino = q_number.upper() in avellino_q_numbers

        if monument_data and monument_data["is_religious"]:
            wlm_categories.append(regione_category + " - religious buildings")

        if regarr[1] == False and not is_como and not is_avellino and not is_valle_primo_presepe:
            wlm_categories.append(base_category + " - without local award")

        if is_como:
            wlm_categories.append(base_category + " - Lake Como")

        if is_valle_primo_presepe:
            wlm_categories.append(base_category + " - Valle del Primo Presepe")

        # Terre dell'Uftia
        # if is_terre_ufita:
        #    wlm_categories.append(base_category + " - Terre dell'Ufita")

        if is_avellino:
            wlm_categories.append(base_category + " - Avellino")

    return {
        "wlm_categories": wlm_categories,
        "non_wlm_categories": non_wlm_categories,
    }


@retry(tries=5, delay=15)
def get_wikidata_avellino():
    """
    Cached Lookup per concorso avellinop
    """

    # last_snapshot = Snapshot.objects.filter(complete=True).order_by("-created").first()
    today = datetime.date.today().isoformat()
    cache_key = f"wikidata_avellino-{today}"
    cache_value = cache.get(cache_key)
    if cache_value:
        return cache_value

    SPARQL_AVELLINO = """

    SELECT DISTINCT ?item
    WHERE {
        ?item wdt:P2186 ?wlmid ;
              wdt:P17 wd:Q38.
        ?item wdt:P131* wd:Q16120 .

        MINUS { 
            ?item p:P2186 [ pq:P582 ?end ] .
            FILTER ( ?end <= "2023-09-01T00:00:00+00:00"^^xsd:dateTime )
        }
        SERVICE wikibase:label { bd:serviceParam wikibase:language "it" }
    }
    
    """
    logger.info("Getting muncipalities from wikidata")
    results = execute_query(SPARQL_AVELLINO)
    data = results["results"]["bindings"]

    avellino_q_numbers = []
    for _result in data:
        result = format_monument(_result)
        q_number = monument_prop(result, "item")
        avellino_q_numbers.append(q_number)

    cache.set(cache_key, avellino_q_numbers, 60 * 60 * 24)
    return avellino_q_numbers
