import json
from itertools import groupby
import sys
import datetime

# variables
dateInterval = "12months"
print("date interval", dateInterval)
aggregation_type = "municipality"
print("aggregation by", aggregation_type)
filter_area = {
    "area_type": "province",
    "area_name": "Milano"
}
collect_monuments = True

years = [2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022]

intervals = [
    [1, 31],
    [2, 28],
    [3, 31],
    [4, 30],
    [5, 31],
    [6, 30],
    [7, 31],
    [8, 31],
    [9, 30],
    [10, 31],
    [11, 30],
    [12, 31],
]

timeDetails = {
    "12months": 1,
    "6months": 2,
    "4months": 3,
    "3months": 4,
    "1months": 12,
}
interval = int(len(intervals)/timeDetails[dateInterval])

dates = []
for year in years:
    for i in range(0, len(intervals), interval):
        date = [year, intervals[i-1][0], intervals[i-1][1]]
        dates.append(date)

datetimes = list(map(lambda d: datetime.datetime(d[0], d[1], d[2]), dates))

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
            date_authorinzation = datetime.datetime(
                int(d[0]), int(d[1]), int(d[2]))
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
        nested = list(g)
        if counted:
            nested = len(nested)
        temp = {
            "key": k,
            "values": nested
        }
        results.append(temp)
    return results


formatted_data = format_data(data)

if filter_area:
    print("filter:", filter_area["area_type"], filter_area["area_name"])
    formatted_data = list(filter(
        lambda d: d[filter_area["area_type"]] == filter_area["area_name"], formatted_data))
else:
    print("no filter set")

nested_data = nest_categories(formatted_data, False, aggregation_type)

snapshots = []
snapshots_incremental = []

data = []

# print(json.dumps(nested_data[0], indent=4, default=str))

for region in nested_data[0:1]:
    region_name = region["key"]
    region_values = region["values"]

    temp_monument = region_values[0]

    region_data = [region_name, [], aggregation_type, [
        temp_monument["region"], temp_monument["province"], temp_monument["municipality"]]]
    # print("region_name", region_name)

    for date in datetimes:

        snapshot_data = [date.strftime('%Y-%m-%d'), []]
        # print("date", date.strftime('%Y-%m-%d'))

        not_p = []
        p = []
        # print("Tot monuments", len(data))
        for monument in region_values:
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

        temp_mapped = {
            # "date": date,
            # "area": region_name,
            "group": "mapped",
            "valueIncremental": len(m) + len(a) + len(p),
            "valueDistinct": len(m)
        }
        if (collect_monuments):
            temp_mapped["monuments"] = m

        temp_authorized = {
            # "date": date,
            # "area": region_name,
            "group": "mapped",
            "group": "authorized",
            "valueIncremental": len(a) + len(p),
            "valueDistinct": len(a)
        }
        if (collect_monuments):
            temp_authorized["monuments"] = a

        temp_photographed = {
            # "date": date,
            # "area": region_name,
            "group": "mapped",
            "group": "photographed",
            "valueIncremental": len(p),
            "valueDistinct": len(p)
        }
        if (collect_monuments):
            temp_photographed["monuments"] = p

        snapshot_data[1].append(temp_mapped)
        snapshot_data[1].append(temp_authorized)
        snapshot_data[1].append(temp_photographed)

        region_data[1].append(snapshot_data)

    data.append(region_data)

# print("data", json.dumps(data, indent=4))

filename = 'data/aggregated/interval-' + \
    dateInterval + '.aggregation-' + aggregation_type
if filter_area:
    filename += '.filter-' + filter_area["area_name"]
if collect_monuments:
    filename += '.withMonuments'
filename += '.json'

with open(filename, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4, default=str)

print("Saved in", filename)

sys.exit()
