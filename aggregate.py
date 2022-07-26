import json
from itertools import groupby
import sys
import datetime

# datetime.datetime(Y, M, D)

dates = [
    [2012, 1, 1],
    [2012, 6, 1],
    [2012, 9, 1],
    [2012, 9, 11],
    [2012, 9, 21],
    [2012, 10, 1],

    [2013, 1, 1],
    [2013, 6, 1],
    [2013, 9, 1],
    [2013, 9, 11],
    [2013, 9, 21],
    [2013, 10, 1],

    [2014, 1, 1],
    [2014, 6, 1],
    [2014, 9, 1],
    [2014, 9, 11],
    [2014, 9, 21],
    [2014, 10, 1],

    [2015, 1, 1],
    [2015, 6, 1],
    [2015, 9, 1],
    [2015, 9, 11],
    [2015, 9, 21],
    [2015, 10, 1],

    [2016, 1, 1],
    [2016, 6, 1],
    [2016, 9, 1],
    [2016, 9, 11],
    [2016, 9, 21],
    [2016, 10, 1],

    [2017, 1, 1],
    [2017, 6, 1],
    [2017, 9, 1],
    [2017, 9, 11],
    [2017, 9, 21],
    [2017, 10, 1],

    [2018, 1, 1],
    [2018, 6, 1],
    [2018, 9, 1],
    [2018, 9, 11],
    [2018, 9, 21],
    [2018, 10, 1],

    [2019, 1, 1],
    [2019, 6, 1],
    [2019, 9, 1],
    [2019, 9, 11],
    [2019, 9, 21],
    [2019, 10, 1],

    [2020, 1, 1],
    [2020, 6, 1],
    [2020, 9, 1],
    [2020, 9, 11],
    [2020, 9, 21],
    [2020, 10, 1],

    [2021, 1, 1],
    [2021, 6, 1],
    [2021, 9, 1],
    [2021, 9, 11],
    [2021, 9, 21],
    [2021, 10, 1],

    [2022, 1, 1],
    [2022, 6, 1],
    [2022, 9, 1],
    [2022, 9, 11],
    [2022, 9, 21],
    [2022, 10, 1],
]

dates2 = [
    [2012, 1, 1],
    [2012, 2, 1],
    [2012, 3, 1],
    [2012, 4, 1],
    [2012, 5, 1],
    [2012, 6, 1],
    [2012, 7, 1],
    [2012, 8, 1],
    [2012, 9, 1],
    [2012, 11, 1],
    [2012, 11, 1],
    [2012, 12, 1],

    [2013, 1, 1],
    [2013, 2, 1],
    [2013, 3, 1],
    [2013, 4, 1],
    [2013, 5, 1],
    [2013, 6, 1],
    [2013, 7, 1],
    [2013, 8, 1],
    [2013, 9, 1],
    [2013, 11, 1],
    [2013, 11, 1],
    [2013, 12, 1],

    [2014, 1, 1],
    [2014, 2, 1],
    [2014, 3, 1],
    [2014, 4, 1],
    [2014, 5, 1],
    [2014, 6, 1],
    [2014, 7, 1],
    [2014, 8, 1],
    [2014, 9, 1],
    [2014, 11, 1],
    [2014, 11, 1],
    [2014, 12, 1],

    [2015, 1, 1],
    [2015, 2, 1],
    [2015, 3, 1],
    [2015, 4, 1],
    [2015, 5, 1],
    [2015, 6, 1],
    [2015, 7, 1],
    [2015, 8, 1],
    [2015, 9, 1],
    [2015, 11, 1],
    [2015, 11, 1],
    [2015, 12, 1],

    [2016, 1, 1],
    [2016, 2, 1],
    [2016, 3, 1],
    [2016, 4, 1],
    [2016, 5, 1],
    [2016, 6, 1],
    [2016, 7, 1],
    [2016, 8, 1],
    [2016, 9, 1],
    [2016, 11, 1],
    [2016, 11, 1],
    [2016, 12, 1],

    [2017, 1, 1],
    [2017, 2, 1],
    [2017, 3, 1],
    [2017, 4, 1],
    [2017, 5, 1],
    [2017, 6, 1],
    [2017, 7, 1],
    [2017, 8, 1],
    [2017, 9, 1],
    [2017, 11, 1],
    [2017, 11, 1],
    [2017, 12, 1],

    [2018, 1, 1],
    [2018, 2, 1],
    [2018, 3, 1],
    [2018, 4, 1],
    [2018, 5, 1],
    [2018, 6, 1],
    [2018, 7, 1],
    [2018, 8, 1],
    [2018, 9, 1],
    [2018, 11, 1],
    [2018, 11, 1],
    [2018, 12, 1],

    [2019, 1, 1],
    [2019, 2, 1],
    [2019, 3, 1],
    [2019, 4, 1],
    [2019, 5, 1],
    [2019, 6, 1],
    [2019, 7, 1],
    [2019, 8, 1],
    [2019, 9, 1],
    [2019, 11, 1],
    [2019, 11, 1],
    [2019, 12, 1],

    [2020, 1, 1],
    [2020, 2, 1],
    [2020, 3, 1],
    [2020, 4, 1],
    [2020, 5, 1],
    [2020, 6, 1],
    [2020, 7, 1],
    [2020, 8, 1],
    [2020, 9, 1],
    [2020, 11, 1],
    [2020, 11, 1],
    [2020, 12, 1],

    [2021, 1, 1],
    [2021, 2, 1],
    [2021, 3, 1],
    [2021, 4, 1],
    [2021, 5, 1],
    [2021, 6, 1],
    [2021, 7, 1],
    [2021, 8, 1],
    [2021, 9, 1],
    [2021, 11, 1],
    [2021, 11, 1],
    [2021, 12, 1],

    [2022, 1, 1],
    [2022, 2, 1],
    [2022, 3, 1],
    [2022, 4, 1],
    [2022, 5, 1],
    [2022, 6, 1],
    [2022, 7, 1],
    [2022, 8, 1],
    [2022, 9, 1],
    [2022, 11, 1],
    [2022, 11, 1],
    [2022, 12, 1],
]

datetimes = list(map(lambda d: datetime.datetime(d[0], d[1], d[2]), dates))
# print(datetimes)

with open('data/all_monuments_places_first_revs.json') as f:
    data = json.load(f)
    f.close()

for m in data:
    m["category"] = "mapped"
    if len(m['wlm_n']) > 0:
        m["category"] = "authorized"
        if len(m["commonsPicturesWLM"]) > 0:
            m["category"] = "photographed"

def format_data(data):
    for monument in data:

        if monument['first_wd_rev']:
            d = monument['first_wd_rev']
            d = d.split('T')[0].split('-')
            date_mapped = datetime.datetime(int(d[0]), int(d[1]), int(d[2]))
            monument["date_mapped"] = date_mapped

        if len(monument['start_n']):
            dates = sorted(monument['start_n'])
            d = dates[0].split('T')[0].split('-')
            date_authorinzation = datetime.datetime(int(d[0]), int(d[1]), int(d[2]))
            monument["date_authorization"] = date_authorinzation
        if len(monument['commonsPicturesWLM']):
            try:
                dates = list(
                    map(lambda d: d["DateTimeOriginal"], monument['commonsPicturesWLM']))
                dates.sort()
                d = dates[0].split(' ')[0].split('-')
                date_first_pic = datetime.datetime(
                    int(d[0]), int(d[1]), int(d[2]))
            except:
                dates = list(
                    map(lambda d: d["DateTime"], monument['commonsPicturesWLM']))
                dates.sort()
                d = dates[0].split(' ')[0].split('-')
                date_first_pic = datetime.datetime(
                    int(d[0]), int(d[1]), int(d[2]))
            monument["date_first_pic"] = date_first_pic
    return data

def nest_categories(data, counted=True, key="category"):
    results = []
    group_sorted = sorted(data, key=lambda d: d[key])
    for k, g in groupby(group_sorted, lambda d: d[key]):
        print(k)
        nested = list(g)
        if counted:
            nested =  len(nested)
        temp = {
            "key": k,
            "values": nested
        }
        results.append(temp)
    return results


formatted_data = format_data(data)

filter_area = {
    "area_type": "region",
    "area_name": "Lombardia"
}

aggregation_type = "municipality"

if filter_area:
    print(filter_area)
    formatted_data = list(filter(lambda d: d[filter_area["area_type"]] == filter_area["area_name"], formatted_data))

nested_data = nest_categories(formatted_data, False, aggregation_type)
# print(json.dumps(nested_data, indent=4, default=str))

snapshots = []
snapshots_incremental = []

# data = [
#     {
#         "key": "Italy",
#         "values": nested_data
#     }
# ]
data = nested_data

# print(json.dumps(data, indent=4, default=str))
# sys.exit()

for date in datetimes:
    print(date)
    for region in data:
        region_name = region["key"]
        region_data = region["values"]
        print(region_name)
        # count photographed monuments
        not_p = []
        p = []
        # print("Tot monuments", len(data))
        for monument in region_data:
            try:
                if monument["date_first_pic"] <= date:
                    p.append(monument)
                else:
                    not_p.append(monument)
            except:
                not_p.append(monument)
        # print("photographed", len(p), len(not_p), len(p)+len(not_p) == len(data))
        # count authorized monuments
        not_a = []
        a = []
        for monument in not_p:
            # if type(monument["date_authorization"]) is datetime.datetime:
            #     print(monument["date_authorization"])
            try:
                if monument["date_authorization"] <= date:
                    a.append(monument)
                else:
                    not_a.append(monument)
            except:
                not_a.append(monument)
        # print("authorized", len(a), len(not_a), len(a)+len(not_a) == len(not_p))
        # count mapped monuments
        not_m = []
        m = []
        for monument in not_a:
            # print(monument["date_mapped"], type(monument["date_mapped"]), date, type(date), monument["date_mapped"] <= date)
            # print(type(monument["date_mapped"]), date, monument["date_mapped"] <= date)
            try:
                if monument["date_mapped"] <= date:
                    m.append(monument)
                else:
                    not_m.append(monument)
            except:
                not_m.append(monument)
        # print("mapped", len(m), len(not_m))
        # print(date, "Monuments: photos:", str(len(p)), "authorized", str(len(a)), "mapped", str(len(m)), "others", str(len(not_m)))

        # temp = {
        #     "date": date,
        #     "area": "Italia",
        #     "admin_level": "nation",
        #     "total": len(p) + len(a) + len(m),
        #     "aggregated": {
        #         "mapped": len(m),
        #         "authorized": len(a),
        #         "photographed": len(p)
        #     }
        # }

        temp = {
            "date": date,
            "area": region_name,
            "group": "mapped",
            "value": len(m)
        }
        snapshots.append(temp)
        temp = {
            "date": date,
            "area": region_name,
            "group": "authorized",
            "value": len(a)
        }
        snapshots.append(temp)
        temp = {
            "date": date,
            "area": region_name,
            "group": "photographed",
            "value": len(p)
        }
        snapshots.append(temp)

        temp = {
            "date": date,
            "area": region_name,
            "group": "mapped",
            "value": len(m) + len(a) + len(p)
        }
        snapshots_incremental.append(temp)
        temp = {
            "date": date,
            "area": region_name,
            "group": "authorized",
            "value": len(a) + len(p)
        }
        snapshots_incremental.append(temp)
        temp = {
            "date": date,
            "area": region_name,
            "group": "photographed",
            "value": len(p)
        }
        snapshots_incremental.append(temp)

with open('data/aggregated/timeline-'+aggregation_type+filter_area["area_name"]+'.json', 'w', encoding='utf-8') as f:
    json.dump(snapshots, f, ensure_ascii=False, indent=4, default=str)

with open('data/aggregated/timeline-'+aggregation_type+filter_area["area_name"]+'-incremental.json', 'w', encoding='utf-8') as f:
    json.dump(snapshots_incremental, f, ensure_ascii=False, indent=4, default=str)

sys.exit()
