import json
import requests
import re
import time

# compile lists of places
municipalities_list = set([])
provinces_list = set([])
metropolitan_areas_list = set([])
with open('data/all_monuments.json') as monuments_json:
    monuments_data = json.load(monuments_json)
    for monument in monuments_data:
        municipalities = monument["comune_n"]
        for _m in municipalities:
          municipalities_list.add(_m)

        provinces = monument["provincia_n"]
        for _p in provinces:
          provinces_list.add(_p)

        metropolitan_areas = monument["metroarea_n"]
        for _a in metropolitan_areas:
          metropolitan_areas_list.add(_a)
monuments_json.close()

requests_delay = 5
url = 'https://query.wikidata.org/sparql'
query = ''
with open('SPARQL-places.txt', 'r') as f:
    query = f.read()
    f.close()

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def query_places(places_type, places_set):
  print("Retrieving", places_type)
  places_list = list(places_set)

  # store list of places
  with open('data/'+places_type+'-q_numbers.json', 'w', encoding='utf-8') as f:
    json.dump(places_list, f, ensure_ascii=False, indent=4)
    f.close()

  # Retrieve further info from wikidata
  paginated_lists = list(chunks(places_list, 25))
  # print("paginated_lists",json.dumps(paginated_lists, indent=4))
  final_data = []
  for _list in paginated_lists:
    ids = ''
    for id in _list:
      ids += 'wd:'+id+'\n'
    compiled_query = re.sub("wd:Q-NUMBERS-1-EACH-LINE", ids, query)

    # performs request
    print("\tRequesting from WikiData...")
    r = requests.get(url, params={'format': 'json', 'query': compiled_query})
    data = r.json()
    data = data["results"]["bindings"]
    print("\tdata length", len(data))
    for item in data:
      for key in item:
          value = item[key]["value"]
          # clean q_numbers
          if "http://www.wikidata.org/entity/" in value:
              value = value.replace(
                  "http://www.wikidata.org/entity/", "")
          # split lists into arrays
          if key.endswith('_n'):
              if value == '':
                  value = []
              else:
                  value = value.split(";")
          item[key] = value
      final_data.append(item)

    if paginated_lists.index(_list) != len(paginated_lists)-1:
      print("\tSleeps "+str(requests_delay)+" secs...")
      time.sleep(requests_delay)
  
  # store data of places
  with open('data/'+places_type+'-data.json', 'w', encoding='utf-8') as f:
    json.dump(final_data, f, ensure_ascii=False, indent=4)
    f.close()

  print("Done", places_type, len(places_set))

query_places("provinces", provinces_list)
query_places("metropolitan_areas", metropolitan_areas_list)
query_places("municipalities", municipalities_list)


print("Done!")