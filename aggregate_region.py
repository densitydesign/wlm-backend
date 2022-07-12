import json
from tempfile import tempdir

with open('data/all_monuments.json') as monuments_json:
    monuments_data = json.load(monuments_json)
    monuments_json.close()

# print(monuments_data)

temp = list(filter(lambda d: d['provincia_n'] == [] and d['metroarea_n'] == [], monuments_data))

print(json.dumps(temp, indent=4))