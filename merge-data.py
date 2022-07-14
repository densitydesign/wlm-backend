import json
import requests

all_monuments = []
all_monuments_q_numbers = []
monuments_count = 0
search_commons = True
commons_url = "https://commons.wikimedia.org/w/api.php"
request_delay = 0.1


def format_monument(monument):
    for key in monument:
        value = monument[key]["value"]
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
        monument[key] = value
    return monument


def search_commons(wlm_id):
    params = {
        "action": "query",
        "format": "json",
        "prop": "imageinfo",
        "generator": "search",
        "iiprop": "extmetadata",
        "gsrsearch": '"' + wlm_id + '"',
        "gsrnamespace": "6"
    }
    print("\tRetrieves photos from Commons using WLM id:", wlm_id)
    r = requests.get(commons_url, params)
    data = r.json()
    if "query" in data and "pages" in data["query"] and len(data["query"]["pages"]) > 0:
        images_data_clean = []
        for pageid in data["query"]["pages"]:
            image = data["query"]["pages"][str(pageid)]
            temp_obj = {}
            if "pageid" in image:
                temp_obj["pageid"] = image["pageid"]
            if "title" in image:
                temp_obj["title"] = image["title"]
            if "imageinfo" in image and len(image["imageinfo"]) > 0 and "extmetadata" in image["imageinfo"][0]:
                extmetadata = image["imageinfo"][0]["extmetadata"]
                if "DateTimeOriginal" in extmetadata and "value" in extmetadata["DateTimeOriginal"]:
                    temp_obj["DateTimeOriginal"] = extmetadata["DateTimeOriginal"]["value"]
                if "DateTime" in extmetadata and "value" in extmetadata["DateTime"]:
                    temp_obj["DateTime"] = extmetadata["DateTime"]["value"]

            images_data_clean.append(temp_obj)
        print("\tFound", len(images_data_clean), "photos")
        return images_data_clean
    else:
        print("\tFound no photos")
        return []

print("Merging and formatting data...")
with open('types_to_search.json') as types_to_search:
    data = json.load(types_to_search)

    # Include monuments participating into the contest
    data.append({"q_number": "Q0", "label": "monuments-in-contest"})

    for entity_searched in data:
        # e.g., { "q_number": "Q2232001", "label": "grotta turistica" }
        q_number = entity_searched["q_number"]
        label = entity_searched["label"]
        file_path = 'data/' + q_number + '-' + label + '.json'
        
        print("Items in",q_number,file_path)
        print("Total monuments parsed up to now:",monuments_count)
        with open('data/' + q_number + '-' + label + '.json') as json_file:
            data = json.load(json_file)
            monuments = data["results"]["bindings"]

            for monument in monuments:
                monuments_count += 1

                # print(monuments_count, monument["monLabel"]["value"])

                mon_q_number = monument["mon"]["value"].replace("http://www.wikidata.org/entity/", "")

                # add to all_mouments list, or update element if exists already
                if mon_q_number not in all_monuments_q_numbers:
                    # clean moument data
                    monument = format_monument(monument)
                    monument["groups"] = [(q_number+"-"+label)]

                    # retrieves WLM photos from Commons
                    monument["commonsPicturesWLM"] = []
                    if search_commons == True and len(monument["wlm_n"]):
                        for wlm_id in monument["wlm_n"]:
                            monument["commonsPicturesWLM"] = search_commons(
                                wlm_id)

                    all_monuments_q_numbers.append(mon_q_number)
                    all_monuments.append(monument)

                else:
                    print("\tupdating", mon_q_number)
                    index = all_monuments_q_numbers.index(mon_q_number)
                    matching_monument = all_monuments[index]
                    matching_monument["groups"].append((q_number+"-"+label))

            json_file.close()
    types_to_search.close()

    # Check duplicates VS unique values
    print("all_monuments", monuments_count)
    print("collected_monuments", len(all_monuments_q_numbers))

    fileName = 'data/all_monuments.json'

    with open(fileName, 'w', encoding='utf-8') as f:
        json.dump(all_monuments, f, ensure_ascii=False, indent=4)

    print("data saved in", fileName)
