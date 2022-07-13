from shapely.geometry import shape, box, mapping, Point, Polygon, MultiPolygon
import geopandas as gpd
import json
import sys
import numpy as np

slice_left = None
slice_right = None

if len(sys.argv) == 3:
    slice_left = int(sys.argv[1])
    slice_right = int(sys.argv[2])
    print("Process items from", slice_left, "to", slice_right)

# load all shapefiles
print("Load all shapefiles")
reg = gpd.read_file(
    "data/Limiti01012022/Reg01012022/Reg01012022_WGS84.shp")
reg = reg.to_crs(epsg=4326)
print("Reg01012022_WGS84 (regioni) loaded.")
# print(reg)

prov = gpd.read_file(
    "data/Limiti01012022/ProvCM01012022/ProvCM01012022_WGS84.shp")
prov = prov.to_crs(epsg=4326)
print("ProvCM01012022_WGS84 (province) loaded.")
# print(prov)

com = gpd.read_file(
    "data/Limiti01012022/Com01012022/Com01012022_WGS84.shp")
com = com.to_crs(epsg=4326)
print("Com01012022_WGS84 (comuni) loaded.\n")
# print(com)

with open('data/all_monuments.json') as monuments_json:
    all_monuments = json.load(monuments_json)
    monuments_json.close()

    # remove monuments with no coordinates
    monuments_no_coordinates = list(filter(lambda d: len(
        d['geo_n']) == 0, all_monuments))
    print(len(monuments_no_coordinates),
          "monuments have no coordinates nor parents monuments, so will be skipped")
    with open('data/nomunents_no_coordinates_nor_parents.json', 'w', encoding='utf-8') as f:
        json.dump(monuments_no_coordinates, f, ensure_ascii=False, indent=4)

    # compile list of monuments with coordinates
    monuments = list(filter(lambda d: len(d['geo_n']) > 0, all_monuments))
    print(len(monuments), "monuments have coordinates and can be located in municipality, province and region")

    if (slice_left != None and slice_right != None):
        monuments = monuments[slice_left:slice_right]
        print("Process", len(monuments), "monuments")
    
    for monument in monuments:
        index = monuments.index(monument)
        print(index, "/", len(monuments))
        # print(monument["mon"], monument["monLabel"])
        if len(monument["geo_n"]) == 0:
            print("Missing coordinates for", monument["monLabel"])
            continue
        coordinates = monument["geo_n"][0]
        coordinates = coordinates.replace("Point(", "")
        coordinates = coordinates.replace(")", "")
        coordinates = coordinates.split(" ")
        np_coordinates = np.array(coordinates)
        np_coordinates = np_coordinates.astype(float)
        coordinates = list(np_coordinates)
        monument["coordinates"] = coordinates

        _point = Point(coordinates[0], coordinates[1])

        # defaults
        monument["municipality"] = "unknown_municipality"
        monument["province"] = "unknown_province"
        monument["region"] = "unknown_region"
        monument["municipality_cod"] = "unknown_municipality_code"
        monument["province_cod"] = "unknown_province_code"
        monument["region_cod"] = "unknown_code"

        for i, row in com.iterrows():
            area = shape(row['geometry'])
            minx, miny, maxx, maxy = area.bounds
            bounding_box = box(minx, miny, maxx, maxy)
            if bounding_box.contains(_point):
                isInside = _point.within(area)
                if (isInside):
                    pro_com = row["PRO_COM"]
                    municipality = row["COMUNE"]

                    cod_prov = row["COD_PROV"]
                    index = prov.index[prov['COD_PROV'] == cod_prov].tolist()[0]
                    province = prov.iloc[index]['DEN_UTS']

                    cod_reg = row["COD_REG"]
                    index = reg.index[reg['COD_REG'] == cod_reg].tolist()[0]
                    region = reg.iloc[index]['DEN_REG']

                    monument["municipality"] = municipality
                    monument["province"] = province
                    monument["region"] = region
                    monument["municipality_cod"] = pro_com
                    monument["province_cod"] = cod_prov
                    monument["region_cod"] = cod_reg
                    print("\t", monument["monLabel"],
                        "is inside", municipality, province, region)
                    continue

with open('data/all_monuments_places'+str(slice_left)+'_'+str(slice_right-1)+'.json', 'w', encoding='utf-8') as f:
    json.dump(monuments, f, ensure_ascii=False, indent=4)
