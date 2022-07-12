import requests
import json
import os
import re
import time

# Check whether the specified path exists or not
path = 'data/'  # where to store the data
if not os.path.exists(path):
    # Create a new directory because it does not exist
    os.makedirs(path)
    print("Created new directory:", path)

url = 'https://query.wikidata.org/sparql'
query = ''
with open('SPARQL-query.txt', 'r') as f:
    query = f.read()
    f.close()

with open('types_to_search.json') as json_file:
    data = json.load(json_file)
    # data = data[16:]  # use this to limit items to process for dev purposes
    print("Requesting...")

    for entity in data:
        print(entity["q_number"], entity["label"])
        # prepares SPARQL query
        type_to_search = 'wd:'+entity["q_number"] + " # " + entity["label"]
        print(type_to_search)
        compiled_query = re.sub("wd:Q_NUMBER_TYPE", type_to_search, query)
        # print(compiled_query)

        # performs request
        r = requests.get(
            url, params={'format': 'json', 'query': compiled_query})
        data = r.json()
        # stores data
        with open('data/'+entity["q_number"]+'-'+entity["label"]+'.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            f.close()
        print("Sleeps 5 seconds...")
        time.sleep(5)
    
    json_file.close()
    print("done!")
