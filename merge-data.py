import json
import requests
import time

all_monuments = []
all_monuments_q_numbers = []
monuments_count = 0
search_commons = False
commons_url = "https://commons.wikimedia.org/w/api.php"
request_delay = 0.1

with open('types_to_search.json') as types_to_search:
    data = json.load(types_to_search)
    # data = data[:8]  # limit items for dev purposes
    # print(data)

    for entity_searched in data:
        # e.g., { "q_number": "wd:Q2232001", "label": "grotta turistica" }
        q_number = entity_searched["q_number"]
        label = entity_searched["label"]
        file_path = 'data/' + q_number + '-' + label + '.json'
        # print(q_number, label, file_path)

        with open('data/' + q_number + '-' + label + '.json') as json_file:
            data = json.load(json_file)
            monuments = data["results"]["bindings"]
            # use this to limit items for dev purposes
            # monuments = monuments[:25]
            for monument in monuments:
                monuments_count += 1

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

                monument["groups"] = [(q_number+"-"+label)]

                # retrieves WLM photos from Commons
                monument["commonsPicturesWLM"] = []
                if search_commons and len(monument["wlm_n"]):
                    for wlm_id in monument["wlm_n"]:
                        params = {
                            'action': 'query',
                            'list': 'search',
                            'srnamespace': '6',
                            'srsearch': '"' + wlm_id + '"',
                            'format': 'json'
                        }
                        print("\tRetrieves photos from Commons using WLM id:", wlm_id)
                        r = requests.get(commons_url, params)
                        print("\t" + r.url)
                        commons_data = r.json()
                        totalhits = commons_data["query"]["searchinfo"]["totalhits"]
                        if totalhits > 0:
                            search_results = commons_data["query"]["search"]
                            for _result in search_results:
                                del _result["wordcount"]
                                del _result["snippet"]
                                del _result["size"]
                            monument["commonsPicturesWLM"] = search_results
                            print("\tAdded " + str(totalhits) +
                                  " items to commonsPicturesWLM")
                        else:
                            print("\tFound no photos")
                        print("\tSleeps " + str(request_delay) + " sec...")
                        time.sleep(request_delay)

                print(monuments_count, monument["monLabel"])

                if monument["mon"] not in all_monuments_q_numbers:
                    all_monuments_q_numbers.append(monument["mon"])
                    all_monuments.append(monument)
                else:
                    print("\tupdating", monument["mon"])
                    matching_monument = list(filter(
                        lambda existing_monument: existing_monument['mon'] == monument["mon"], all_monuments))[0]
                    matching_monument["groups"].append((q_number+"-"+label))
            json_file.close()
    types_to_search.close()

    print("all_monuments", monuments_count)
    print("collected_monuments", len(all_monuments_q_numbers))

    with open('data/all_monuments.json', 'w', encoding='utf-8') as f:
        json.dump(all_monuments, f, ensure_ascii=False, indent=4)

    print("data saved in 'data/merged.json'")
