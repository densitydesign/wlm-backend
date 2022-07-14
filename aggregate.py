import json
from itertools import groupby
from rdflib import PROV
import sys

fileName = 'data/all_monuments_places.json'
outputName = 'data'
if len(sys.argv) == 2:
    fileName = sys.argv[1]
    outputName += '-'+fileName.split("/")[-1]
    print("Loading data from", fileName)

final_data = {}  # the final data

with open(fileName) as f:
    data = json.load(f)
    f.close()

    for m in data:
        m["category"] = "mapped"
        if len(m['wlm_n']) > 0:
            m["category"] = "authorized"
            if len(m["commonsPicturesWLM"]) > 0:
                m["category"] = "photographed"

    data2check = list(filter(lambda d: not 'region' in d, data))
    # print(data2check)

    data = list(filter(lambda d: (
        'region' in d and 'province' in d and 'municipality' in d), data))

    def nest_categories(data, counted=True, key="category"):
        result = {}
        group_sorted = sorted(data, key=lambda d: d[key])
        for k, g in groupby(group_sorted, lambda d: d[key]):
            nested = list(g)
            if counted:
                result[k] = len(nested)
            else:
                result[k] = nested
        return result

    final_data["regions"] = {}
    final_data["aggregated"] = nest_categories(data)

    # Nest regions
    data_sorted = sorted(data, key=lambda d: d['region'])
    for k, g in groupby(data_sorted, lambda d: d['region']):
        # print(k) # region
        nested = list(g)
        final_data["regions"][k] = {}
        final_data["regions"][k]["aggregated"] = nest_categories(nested)
        final_data["regions"][k]["provinces"] = {}

        # Nest provinces
        data_sorted = sorted(nested, key=lambda d: d['province'])
        for kk, gg in groupby(data_sorted, lambda d: d['province']):
            # print("\t", kk) # province
            nested = list(gg)
            final_data["regions"][k]["provinces"][kk] = {}
            final_data["regions"][k]["provinces"][kk]["aggregated"] = nest_categories(
                nested)
            final_data["regions"][k]["provinces"][kk]["municipalities"] = {}

            # Nest municipalities
            data_sorted = sorted(nested, key=lambda d: d['municipality'])
            for kkk, ggg in groupby(data_sorted, lambda d: d['municipality']):
                # print("\t\t", kkk)
                nested = list(ggg)
                final_data["regions"][k]["provinces"][kk]["municipalities"][kkk] = {}
                final_data["regions"][k]["provinces"][kk]["municipalities"][kkk]["aggregated"] = nest_categories(
                    nested)
                final_data["regions"][k]["provinces"][kk]["municipalities"][kkk]["monuments"] = nest_categories(
                    nested, False)

with open('data/aggregated/'+outputName+'.json', 'w', encoding='utf-8') as f:
    json.dump(final_data, f, ensure_ascii=False, indent=4)

print("Saved in data/aggregated")
