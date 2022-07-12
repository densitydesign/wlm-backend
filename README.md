These are scripts to retrieve data about Wiki Loves Monuments IT from WikiData.

###### 1. types_to_search.json
Contains entities types to search on wikidata, formatted as follows: `{ "q_number": "Q57821", "label": "Fortificazione" },`

###### 2. SPARQL-query.txt
Contains the template for the SPARQL query to be performed on WikiData. You need to replace `wd:Q_NUMBER_TYPE` with the Q-number corresponding to the entity you are searching for (e.g., `wd: Q57821 # Fortificazione`)

###### 3. query.py
This is th first script to run. It takes every item from `types_to_search.json` and compiles a SPARQL query. Query are performed individually to avoid hitting timeouts of the WD query service. Results of each query are stored individually in the `data` folder as `.json` files.

Every monument is stored as a dictionary. Properties ending with `"_n"` contain semicolumn-separated values. Example:
````
{
    "mon": {
        "type": "uri",
        "value": "http://www.wikidata.org/entity/Q1759446"
    },
    "monLabel": {
        "xml:lang": "it",
        "type": "literal",
        "value": "Villa del Balbianello"
    },
    "parent_n": {
        "type": "literal",
        "value": ""
    },
    "geo_n": {
        "type": "literal",
        "value": "Point(9.202466 45.965112);Point(9.196551 45.970142)"
    },
    "comune_n": {
        "type": "literal",
        "value": "http://www.wikidata.org/entity/Q47633;http://www.wikidata.org/entity/Q14914180"
    },
    "provincia_n": {
        "type": "literal",
        "value": "http://www.wikidata.org/entity/Q16161"
    },
    "metroarea_n": {
        "type": "literal",
        "value": ""
    },
    "wlm_n": {
        "type": "literal",
        "value": ""
    },
    "start_n": {
        "type": "literal",
        "value": ""
    },
    "end_n": {
        "type": "literal",
        "value": ""
    },
    "approvedBy_n": {
        "type": "literal",
        "value": ""
    },
    "relevantImage_n": {
        "type": "literal",
        "value": "http://commons.wikimedia.org/wiki/Special:FilePath/Villa%20Balbianello%20a%20Lenno.jpg;http://commons.wikimedia.org/wiki/Special:FilePath/Villa-balbianello.jpg;http://commons.wikimedia.org/wiki/Special:FilePath/30VillaBalbianello.jpg;http://commons.wikimedia.org/wiki/Special:FilePath/16VillaBalbianello.jpg;http://commons.wikimedia.org/wiki/Special:FilePath/Villa%20Balbianello%203674.jpg;http://commons.wikimedia.org/wiki/Special:FilePath/31VillaBalbianello.jpg"
    },
    "commons_n": {
        "type": "literal",
        "value": "Villa Balbianello (Lenno)"
    }
}
````

###### 4. merge-data.py
The script merges the data created by the previous script and produce a more compact version. It indicates if a monument occurred in more queries in the `groups` properties. Example:
````
{
    "mon": "Q1759446",
    "monLabel": "Villa del Balbianello",
    "parent_n": [],
    "geo_n": [
        "Point(9.202466 45.965112)",
        "Point(9.196551 45.970142)"
    ],
    "comune_n": [
        "Q47633",
        "Q14914180"
    ],
    "provincia_n": [
        "Q16161"
    ],
    "metroarea_n": [],
    "wlm_n": [],
    "start_n": [],
    "end_n": [],
    "approvedBy_n": [],
    "relevantImage_n": [
        "http://commons.wikimedia.org/wiki/Special:FilePath/Villa%20Balbianello%20a%20Lenno.jpg",
        "http://commons.wikimedia.org/wiki/Special:FilePath/Villa-balbianello.jpg",
        "http://commons.wikimedia.org/wiki/Special:FilePath/30VillaBalbianello.jpg",
        "http://commons.wikimedia.org/wiki/Special:FilePath/16VillaBalbianello.jpg",
        "http://commons.wikimedia.org/wiki/Special:FilePath/Villa%20Balbianello%203674.jpg",
        "http://commons.wikimedia.org/wiki/Special:FilePath/31VillaBalbianello.jpg"
    ],
    "commons_n": [
        "Villa Balbianello (Lenno)"
    ],
    "groups": [
        "Q3950-villa",
        "Q35112127-edificio storico",
        "Q1030034-GLAM",
        "Q24398318-edificio religioso"
    ],
    "commonsPicturesWLM": []
    }
````