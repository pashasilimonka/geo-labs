import geopandas as gpd
import matplotlib.pyplot as plt
from pyproj import Geod
from shapely import Point, LineString, Polygon, MultiPolygon

gdf = gpd.read_file("./poland_Provinces_level_1/poland_Provinces_level_1.shp")
ax = gdf.plot(color='lightblue', edgecolor='black')



all_geoms = gdf.union_all()

if isinstance(all_geoms, Polygon):
    coords = list(all_geoms.exterior.coords)
elif isinstance(all_geoms, MultiPolygon):
    coords = []
    for poly in all_geoms.geoms:
        coords.extend(list(poly.exterior.coords))

west_point = min(coords, key=lambda x: x[0])
east_point = max(coords, key=lambda x: x[0])

print(f"Найсхідніша точка: ${east_point}")
print(f"Найзахідніша точка: ${west_point}")


area = int(input(f"Оберіть область для якої знайти центральну точку від 1 до ${len(gdf)}"))
obj1 = gdf.iloc[area-1]
centroid = obj1.geometry.centroid


area2 = int(input(f"Оберіть область для якої знайти центральну точку від 1 до ${len(gdf)}"))
obj2 = gdf.iloc[area2-1]
centroid2 = obj2.geometry.centroid

geod = Geod(ellps="WGS84")
distance = geod.inv(centroid.x, centroid.y, centroid2.x, centroid2.y)[2] / 1000  # в кілометрах
print("Центральна точка області 1:", centroid)
print("Центральна точка області 2:", centroid2)
print(f"Відстань між облястю 1 і областю 2: {distance:.2f} км")


line = LineString([centroid, centroid2])
centroid_gdf = gpd.GeoDataFrame(geometry=[centroid, centroid2, Point(west_point), Point(east_point), line], crs=gdf.crs)
centroid_gdf.plot(ax=ax, color='red', markersize=50)

plt.show()


