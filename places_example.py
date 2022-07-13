from shapely.geometry import shape, mapping, Point, Polygon, MultiPolygon
import geopandas as gpd

turin = Point(7.7, 45.066667) # Turin
milan = Point(9.19, 45.466944) # Milan

shpf = gpd.read_file("data/Limiti01012022/Reg01012022/Reg01012022_WGS84.shp")
shpf = shpf.to_crs(epsg=4326)
print(shpf)

for i, row in shpf.iterrows():
  area = shape(row['geometry'])
  name = row[2]
  print(name)
  print("Turin",turin.within(area))
  print("Milan",milan.within(area))