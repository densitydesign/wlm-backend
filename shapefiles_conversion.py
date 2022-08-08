from shapely.geometry import shape, box, mapping, Point, Polygon, MultiPolygon
import sys
import shapefile
import fiona

shapefiles_list = [
    ["data/Limiti01012022/Reg01012022/Reg01012022_WGS84","DEN_REG"],
    ["data/Limiti01012022/ProvCM01012022/ProvCM01012022_WGS84","DEN_UTS"],
    ["data/Limiti01012022/Com01012022/Com01012022_WGS84","COMUNE"]
]

for shapefile_item in shapefiles_list[:1]:
    filename = shapefile_item[0]
    label = shapefile_item[1]
    print(filename)
    shp_file = shapefile.Reader(filename)
    # print(shp_file.fields)
    # the DeletionFlag field has no real purpose, and should in most cases be ignored
    fieldnames = [f[0] for f in shp_file.fields[1:]]
    print(fieldnames)
    for shp_record in shp_file.shapeRecords()[:1]:
        # Each ShapeRecord instance has a "shape" and "record" attribute
        print(shp_record.record)
        print(shp_record.shape)
        # convert to GeoJSON format
        geo_interface = shp_record.shape.__geo_interface__
        shp_geom = shape(geo_interface)
        print(shp_geom)
        shp_centroid = shp_geom.centroid
        print(shp_centroid)

sys.exit()


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
