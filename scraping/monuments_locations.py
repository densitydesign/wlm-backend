from shapely.geometry import shape, box, mapping, Point, Polygon, MultiPolygon
import geopandas as gpd
import json

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


def get_coordinates(coordinates):
    coordinates = coordinates.replace("Point(", "")
    coordinates = coordinates.replace(")", "")
    coordinates = coordinates.split(" ")
    coordinates[0] = float(coordinates[0])
    coordinates[1] = float(coordinates[1])
    return coordinates


def container_index(point, polygons):
    for i, row in polygons.iterrows():
        area = shape(row['geometry'])
        isInside = point.within(area)
        if (isInside):
            return i
    print("Container area not found")


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

    for monument in monuments:
        index = monuments.index(monument)
        print(index, "/", len(monuments),
              monument["mon"], monument["monLabel"])
        if len(monument["geo_n"]) == 0:
            print("Missing coordinates for", monument["monLabel"])
            continue
        # defaults
        monument["municipality"] = "unknown_municipality"
        monument["province"] = "unknown_province"
        monument["region"] = "unknown_region"
        monument["municipality_cod"] = "unknown_municipality_code"
        monument["province_cod"] = "unknown_province_code"
        monument["region_cod"] = "unknown_code"
        # check area
        monument["coordinates"] = get_coordinates(monument["geo_n"][0])
        _point = Point(monument["coordinates"][0], monument["coordinates"][1])

        reg_index = container_index(_point, reg)
        if reg_index==None:
            print("No container region")
            continue
        cod_reg = reg.iat[reg_index, 1]
        region = reg.iat[reg_index, 2]
        # print("regione", cod_reg, region)

        selected_prov = prov.loc[prov['COD_REG'] == cod_reg]
        # print(selected_prov)
        prov_index = container_index(_point, selected_prov)
        if prov_index==None:
            print("No container province")
            continue
        cod_prov = prov.iat[prov_index, 2]
        province = prov.iat[prov_index, 7]
        # print("provincia", cod_prov, province)

        selected_com = com.loc[com['COD_PROV'] == cod_prov]
        # print(selected_com)
        com_index = container_index(_point, selected_com)
        if com_index==None:
            print("No container municipality")
            continue
        pro_com = com.iat[com_index, 5]
        municipality = com.iat[com_index, 7]
        # print("municipality", pro_com, municipality)

        # print(pro_com, municipality, cod_prov, province, cod_reg, region)
        monument["municipality"] = municipality
        monument["province"] = province
        monument["region"] = region
        monument["municipality_cod"] = str(pro_com)
        monument["province_cod"] = str(cod_prov)
        monument["region_cod"] = str(cod_reg)

with open('data/all_monuments_places.json', 'w', encoding='utf-8') as f:
    json.dump(monuments, f, ensure_ascii=False, indent=4)