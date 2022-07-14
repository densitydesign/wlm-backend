import requests
import json
import os
import re
import time

# Check whether the destination path exists
path = 'data/'  # where to store the data
if not os.path.exists(path):
    # Create a new directory because it does not exist
    os.makedirs(path)
    print("Created new directory:", path)

url = 'https://query.wikidata.org/sparql'
query = ''
with open('SPARQL-typologies.txt', 'r') as f:
    query = f.read()
    f.close()

# Retrieves monuments in contest
print("Retrieves monuments in contest")
query_wlm = ''
with open('SPARQL-contest.txt', 'r') as f:
    query_wlm = f.read()
    f.close()

# performs request
r = requests.get(
    url, params={'format': 'json', 'query': query_wlm})
data = r.json()

# stores data as it is
with open('data/Q0-monuments-in-contest.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
    f.close()
    
print("Sleeps 5 seconds...")
time.sleep(5)

# Preparing requests
print("Preparing requests...")
with open('types_to_search.json') as json_file:
    data = json.load(json_file)

    for entity in data:
        print(entity["q_number"], entity["label"])

        # prepares SPARQL query
        type_to_search = 'wd:'+entity["q_number"] + " # " + entity["label"]
        compiled_query = re.sub("wd:Q_NUMBER_TYPE", type_to_search, query)

        # performs request
        r = requests.get(
            url, params={'format': 'json', 'query': compiled_query})
        data = r.json()

        # stores data as it is
        with open('data/'+entity["q_number"]+'-'+entity["label"]+'.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            f.close()
            
        print("Sleeps 5 seconds...")
        time.sleep(5)
    
    json_file.close()
    print("done!")
