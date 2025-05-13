import geopandas as gpd
import matplotlib.pyplot as plt
from pyproj import Geod
from shapely import Point, LineString, Polygon, MultiPolygon

#Зчитую файл і формую мапу
poland_part = gpd.read_file("./poland_Provinces_level_1/poland_Provinces_level_1.shp")
ax = poland_part.plot(color='lightblue', edgecolor='black')



def find_west_east(gdf):
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
    return Point(west_point), Point(east_point)


def find_distance_between_centroids(gdf):
    index1 = int(input(f"Оберіть область для якої знайти центральну точку від 1 до {len(poland_part)}\n"))
    area1 = poland_part.iloc[index1 - 1]
    centroid = area1.geometry.centroid

    index2 = int(input(f"Оберіть область для якої знайти центральну точку від 1 до {len(poland_part)}\n"))
    area2 = poland_part.iloc[index2 - 1]
    centroid2 = area2.geometry.centroid

    geod = Geod(ellps="WGS84")
    distance = geod.inv(centroid.x, centroid.y, centroid2.x, centroid2.y)[2] / 1000  # в кілометрах
    print("Центральна точка області 1:", centroid)
    print("Центральна точка області 2:", centroid2)
    print(f"Відстань між облястю 1 і областю 2: {distance:.2f} км")

    return centroid, centroid2

def build_map(gdf, west_point, east_point, centroid, centroid2):
    line = LineString([centroid, centroid2])
    centroid_gdf = gpd.GeoDataFrame(geometry=[centroid, centroid2, west_point, east_point, line], crs=gdf.crs)
    centroid_gdf.plot(ax=ax, color='red', markersize=50)

    plt.show()

if __name__ == "__main__":
    # Зчитую файл і формую мапу
    poland_part = gpd.read_file("./poland_Provinces_level_1/poland_Provinces_level_1.shp")
    ax = poland_part.plot(color='lightblue', edgecolor='black')

    #Найсхідніша та найзахідніша точки
    west_point, east_point = find_west_east(poland_part)

    #2 центроїди на вибір(вводити номер з консолі) і відстань між ними
    centroid, centroid2 = find_distance_between_centroids(poland_part)

    #Побудова мапи і розтсановка точок
    build_map(poland_part, west_point, east_point, centroid, centroid2)

