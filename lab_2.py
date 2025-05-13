import geopandas as gpd
import matplotlib.pyplot as plt



def calculate_square_of_area(gdf, region_num):
    region = gdf.iloc[[region_num-1]]
    if not region.empty:
        region = region.to_crs(epsg=32644).copy()
        region["square"] = region.geometry.area / 10 ** 6
        print(f"Площа області: {region[["square"]]}")
    else:
        raise Exception("Територія не має такої області")


def calculate_roads_length(gdf, gdf2, region_num):
    # Витягую регіон і дороги в окремі змінні
    region = gdf.iloc[[region_num - 1]].copy()

    region = region.to_crs(epsg=32644)
    roads = gdf2.to_crs(epsg=32644)

    # Вирізаю дороги в межах регіону
    roads_in_region = gpd.clip(roads, region)

    # Обчислюємо довжину в кілометрах
    roads_in_region["length"] = roads_in_region.geometry.length / 1000
    total_sum = roads_in_region["length"].sum()

    print(f"Загальна довжина доріг у області {region_num}: {total_sum:.2f} км")
    return roads_in_region


def filter_points(points_gdf, admin_gdf, region_num):
    region = admin_gdf.iloc[[region_num-1]]
    region = region.to_crs(epsg=32644)
    points_gdf = points_gdf.to_crs(epsg=32644)

    points_in_region = gpd.sjoin(points_gdf, region, predicate='within')



    coords = points_in_region.geometry.apply(lambda geom: (geom.x, geom.y))

    print(f"Знайдено {len(points_in_region)} точок у області '{region_num}'")
    print(coords.to_list())

    return points_in_region


def find_points_near_object(admin_gdf, region_num, points_gdf, object_gdf, object_filter, buffer_distance_km):
    # 1. Фільтрую об’єкт
    for key, value in object_filter.items():
        object_gdf = object_gdf[object_gdf[key] == value]

    if object_gdf.empty:
        print("Об'єкт не знайдено.")
        return

    region_gdf = admin_gdf.iloc[[region_num-1]]
    # 2. Встановив спільну CRS і вибрав об'єкти у межах обраної області
    points_proj = points_gdf.to_crs(epsg=32644)
    object_proj = object_gdf.to_crs(epsg=32644)
    region_gdf = region_gdf.to_crs(epsg=32644)
    object_proj = gpd.clip(object_proj, region_gdf)
    # 3. буфер
    buffer = object_proj.buffer(buffer_distance_km * 1000)

    # 4. Об'єднав всі геометрії буфера в один полігон
    buffer_union = buffer.union_all()

    # 5. точки в межах буфера
    points_near = points_proj[points_proj.geometry.within(buffer_union)]

    points_near = points_near.to_crs(epsg=4326)
    coords = points_near.geometry.apply(lambda geom: (geom.x, geom.y))
    print(f"Знайдено {len(points_near)} точок в радіусі {buffer_distance_km} км:")
    print(coords.to_list())

    return points_near


def plot_multilayer_map(admin_gdf, roads_gdf, points_gdf, result_points_gdf=None, region_num=None):

    admin_gdf = admin_gdf.to_crs(epsg=4326)
    roads_gdf = roads_gdf.to_crs(epsg=4326)
    points_gdf = points_gdf.to_crs(epsg=4326)
    if result_points_gdf is not None:
        result_points_gdf = result_points_gdf.to_crs(epsg=4326)

    fig, ax = plt.subplots(figsize=(10, 10))

    # 1. Адміністративні межі
    admin_gdf.plot(ax=ax, edgecolor='black', facecolor='none', linewidth=1, label='Адміністративні межі')

    # Виділяю конкретну область
    if region_num:
        region = admin_gdf.iloc[[region_num - 1]]
        region.plot(ax=ax, facecolor='lightgray', edgecolor='red', linewidth=2, label='Обрана область')

    # 2. Дороги
    roads_gdf.plot(ax=ax, color='gray', linewidth=0.5, label='Дороги')

    # 3. Всі точки
    points_gdf.plot(ax=ax, color='blue', markersize=5, label='Всі точки')

    # 4. Точки після аналітики
    if result_points_gdf is not None:
        result_points_gdf.plot(ax=ax, color='red', markersize=20, marker='x', label='Результат: точки поруч')

    # Додати легенду та сітку
    plt.legend()
    plt.title('Багатошарова карта з аналітичними результатами')
    plt.xlabel('Довгота')
    plt.ylabel('Широта')
    plt.grid(True)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    admin = gpd.read_file("./geosample-arcgis/shape/admin.shp", encoding='cp1251')
    roads = gpd.read_file("./geosample-arcgis/shape/road-l-osm.shp", encoding='cp1251')
    points = gpd.read_file("./geosample-arcgis/shape/poi-osm.shp", encoding='cp1251')

    #Перевірка на перевизначення проєкцій
    admin_crs = admin.to_crs(epsg=31370)
    print(admin_crs.crs)
    admin_converted = admin_crs.to_crs(epsg=4326)
    print(admin_converted.crs)

    #Номер адміністративної точки(ввести назву в консоль)
    area_name = int(input(f"Введіть номер області від 1 до 4:\n"))

    calculate_square_of_area(admin, area_name)

    roads_in_region = calculate_roads_length(admin,roads, area_name)

    points_in_region = filter_points(points, admin, area_name)

    points_near = find_points_near_object(admin, area_name, points, roads, {"TYPE": "primary"}, buffer_distance_km=5)

    plot_multilayer_map(admin, roads, points_in_region, result_points_gdf=points_near, region_num=area_name)








