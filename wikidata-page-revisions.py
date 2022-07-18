import json
import requests
from itertools import groupby

url = 'https://www.wikidata.org/w/api.php'

# Yield successive n-sized
# chunks from l.
def divide_chunks(l, n):
    # looping till length l
    for i in range(0, len(l), n):
        yield l[i:i + n]

def nest_data(data, key="title"):
    group_sorted = sorted(data, key=lambda d: d[key])
    nested = []
    for k, g in groupby(group_sorted, lambda d: d[key]):
        nested.append(list(g))
    return nested

with open('data/all_monuments_places.json') as f:
    data = json.load(f)
    f.close()

    for index, monument in enumerate(data):
      print(index, monument["mon"], monument["monLabel"])

      params = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "titles": monument["mon"],
        "rvprop": "timestamp",
        "rvlimit": "1",
        "rvdir":"newer"
      }
      r = requests.get(url, params)
      results = r.json()
      # print(json.dumps(results, indent=4))

      pages = results["query"]["pages"]

      revisions = []
      for key in pages:
        revision = pages[str(key)]["revisions"][0]["timestamp"]
        monument["first_wd_rev"] = revision
    
    with open('data/all_monuments_places_first_revs.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)