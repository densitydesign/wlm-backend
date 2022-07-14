import json
from itertools import groupby

with open('data/all_monuments.json') as f:
    data = json.load(f)
    f.close()

    print("All monuments",len(data))

    for m in data:
        m["category"] = "mapped"
        if len(m['wlm_n']) > 0:
            m["category"] = "contest"
            if len(m["commonsPicturesWLM"]) > 0:
                m["category"] = "covered"
    
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

    aggregates = nest_categories(data)

    print("Aggregations", aggregates)
    print("In contest", aggregates["contest"]+aggregates["covered"])