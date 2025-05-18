import os
import time
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from PIL import Image
from folium.raster_layers import ImageOverlay
from rasterio.shutil import copy as rio_copy
from skimage.metrics import mean_squared_error
from sqlalchemy import create_engine
import geoalchemy2
import folium



#ВАРІАНТ 1.

def test_access_speed(file_path):
    start_time = time.time()
    with rasterio.open(file_path) as src:
        img = src.read(1)
    end_time = time.time()
    return end_time - start_time

def compute_rmse(file1, file2):
    with rasterio.open(file1) as src1, rasterio.open(file2) as src2:
        img1 = src1.read(1)
        img2 = src2.read(1)
        mask = (img1 != src1.nodata) & (img2 != src2.nodata)
        mse = mean_squared_error(img1[mask], img2[mask])
        rmse = np.sqrt(mse)
        return rmse


import geopandas as gpd
import time
from shapely.geometry import box


def test_performance(filepath, format_name):
    print(f"\n=== {format_name} ===")

    # Час повного завантаження
    start = time.time()
    gdf = gpd.read_file(filepath)
    load_time = time.time() - start
    print(f"Завантаження: {load_time:.3f} сек")

    # Час вибірки по геобоксу
    bbox = box(30.4, 50.4, 30.6, 50.6)
    start = time.time()
    selected = gdf[gdf.geometry.intersects(bbox)]
    selection_time = time.time() - start
    print(f"Просторова вибірка: {selection_time:.3f} сек")

    # Час буферизації (просторова операція)
    start = time.time()
    gdf_proj = gdf.to_crs(epsg=3857)  # Web Mercator, метри
    gdf_proj['buffer'] = gdf_proj.geometry.buffer(100)  # 100 метрів
    buffer_time = time.time() - start
    print(f"Буферизація: {buffer_time:.3f} сек")

def space_test(file1, file2, format_name):
    print(f"\n=== {format_name} ===")
    orig = gpd.read_file(file1)
    converted = gpd.read_file(file2)

    orig['diff'] = orig.geometry.distance(converted.geometry)
    print("Середнє відхилення (м):", orig['diff'].mean() * 111000)

def radio_test(file1, file2, format_name):
    print(f"\n=== {format_name} ===")
    with rasterio.open(file1) as src1, rasterio.open(file2) as src2:
        band1=src1.read(1)
        band2 = src2.read(1)

        diff = np.abs(band1 - band2)
        print("Середнє відхилення пікселів:", np.mean(diff))
        print("Максимальне відхилення:", np.max(diff))

def build_map():
    # Вхідні шляхи
    vector_path = './data_lab_3/my_village.osm'
    raster_path = './data_lab_3/my_village.tiff'


    layers = ['points', 'lines', 'multilinestrings', 'multipolygons']

    gdfs = []
    for layer in layers:
        try:
            gdf = gpd.read_file(vector_path, layer=layer)
            gdfs.append(gdf)
        except Exception as e:
            print(f"Не вдалося прочитати шар {layer}: {e}")

    gdf_all = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs='EPSG:4326')

    with rasterio.open(raster_path) as src:
        bounds = src.bounds
        raster_crs = src.crs

    gdf_all = gdf_all.to_crs(raster_crs)

    from shapely.geometry import box
    raster_bbox = box(bounds.left, bounds.bottom, bounds.right, bounds.top)
    bbox_gdf = gpd.GeoDataFrame(geometry=[raster_bbox], crs=raster_crs)

    # Кліпінг векторних даних
    gdf_all = gdf_all.clip(bbox_gdf)

    # Центр карти
    centroid = gdf_all.geometry.unary_union.centroid
    map_center = [centroid.y, centroid.x]

    # Створення карти
    m = folium.Map(location=map_center, zoom_start=15, control_scale=True, tiles=None)

    # Растрова підложка
    with rasterio.open(raster_path) as src:
        img = src.read([1, 2, 3])  # RGB
        bounds = src.bounds
        img = np.moveaxis(img, 0, -1)  # CxHxW -> HxWxC
        img = (img - img.min()) / (img.max() - img.min()) * 255
        img = img.astype(np.uint8)

        image = Image.fromarray(img)
        image.save("temp_raster.png")

    ImageOverlay(
        name="Растрова підложка",
        image="temp_raster.png",
        bounds=[[bounds.bottom, bounds.left], [bounds.top, bounds.right]],
        opacity=0.6,
    ).add_to(m)

    # Векторні шари
    vector_layer = folium.FeatureGroup(name="Векторні об'єкти")

    for _, row in gdf_all.iterrows():
        geom = row.geometry
        tooltip = str(row.get('name', '') or "")

        popup = folium.Popup(f"<b>Назва:</b> {tooltip}", max_width=200)

        if geom.geom_type == 'Point':
            folium.Marker(
                location=[geom.y, geom.x],
                tooltip=tooltip,
                popup=popup,
                icon=folium.Icon(color='green')
            ).add_to(vector_layer)

        elif geom.geom_type in ['Polygon', 'MultiPolygon']:
            gj = folium.GeoJson(data=geom.__geo_interface__,
                                tooltip=tooltip,
                                popup=popup,
                                name="Полігон",
                                style_function=lambda x: {
                                    'fillColor': 'blue',
                                    'color': 'blue',
                                    'weight': 1,
                                    'fillOpacity': 0.3
                                })
            gj.add_to(vector_layer)

        elif geom.geom_type in ['LineString', 'MultiLineString']:
            gj = folium.GeoJson(data=geom.__geo_interface__,
                                tooltip=tooltip,
                                popup=popup,
                                name="Лінія",
                                style_function=lambda x: {
                                    'color': 'red',
                                    'weight': 2
                                })
            gj.add_to(vector_layer)

    vector_layer.add_to(m)

    # Легенда
    legend_html = '''
    <div style="position: fixed; bottom: 40px; left: 40px; width: 220px; background-color: white;
         padding: 10px; z-index:9999; box-shadow: 0 0 10px rgba(0,0,0,0.3); font-size: 14px;">
    <b>Легенда</b><br>
    🟢 Точки (POI)<br>
    🔴 Лінії (дороги)<br>
    🔵 Полігони (будівлі/землі)<br>
    🖼️ Растрова підложка
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    # Перемикач шарів
    folium.LayerControl().add_to(m)


    m.save("my_village_map.html")
    print("Карту збережено як my_village_map.html")


src_path = './data_lab_3/my_village.tiff'

rio_copy(src_path, './data_lab_3/my_village_lzw.tiff', driver='GTiff', compress='LZW')
rio_copy(src_path, './data_lab_3/my_village_deflate.tiff', driver='GTiff', compress='DEFLATE')

rio_copy(src_path, './data_lab_3/my_village_cog.tiff', driver='COG', compress='LZW',
         blocksize=256, tiled=True)
rio_copy('./data_lab_3/my_village_16.tiff', './data_lab_3/my_village_jp2.tiff', driver='JP2OpenJPEG', quality=16)

print("SIZE:")
print(f"Original: {(os.path.getsize('./data_lab_3/my_village.tiff')/1048576):.2}MB\n"
      f"LZW: {(os.path.getsize('./data_lab_3/my_village_lzw.tiff')/1048576):.2}MB\n"
      f"DEFLATE: {(os.path.getsize('./data_lab_3/my_village_deflate.tiff')/1048576):.2}MB\n"
      f"COG: {(os.path.getsize('./data_lab_3/my_village_cog.tiff')/1048576):.2}MB\n"
      f"JP2: {(os.path.getsize('./data_lab_3/my_village_jp2.tiff')/1048576):.2}MB")

print("RMSE:")
print(f"LZW: {compute_rmse('./data_lab_3/my_village.tiff', './data_lab_3/my_village_lzw.tiff'):.2f}\n")
print(f"DEFLATE: {compute_rmse('./data_lab_3/my_village.tiff', './data_lab_3/my_village_deflate.tiff'):.2f}\n")
print(f"COG: {compute_rmse('./data_lab_3/my_village.tiff', './data_lab_3/my_village_cog.tiff'):.2f}\n")
print(f"JP2: {compute_rmse('./data_lab_3/my_village.tiff', './data_lab_3/my_village_jp2.tiff'):.2f}")

print("ACCESS SPEED:")
print(f"Original: {test_access_speed('./data_lab_3/my_village.tiff'):.2f}s\n"
      f"LZW: {test_access_speed('./data_lab_3/my_village_lzw.tiff'):.2f}s\n"
      f"DEFLATE: {test_access_speed('./data_lab_3/my_village_deflate.tiff'):.2f}s\n"
      f"COG: {test_access_speed('./data_lab_3/my_village_cog.tiff'):.2f}s\n"
      f"JP2: {test_access_speed('./data_lab_3/my_village_jp2.tiff'):.2f}s")


#ВЕКТОРНА МАПА


gdf = gpd.read_file('./data_lab_3/my_village.osm')

#Обмеження на імена полів, кілька шарів мапи
gdf.to_file('./data_lab_3/my_village.shp', driver='ESRI Shapefile', layer='multipolygons')
#Відсутня індексація
gdf.to_file('./data_lab_3/my_village.geojson', driver='GeoJSON')
#На відміну від шейп-файлу містить в собі декілька шарів мапи
gdf.to_file('./data_lab_3/my_village.gpkg', driver='GPKG')
user = "postgres"
password = "postgres"
host = "localhost"
port = "5432"
db = "geo_base"
table_name = "my_layer"

engine = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{db}")

# Збереження в таблицю PostGIS потребує бази даних, але це дозволить виконувати SQL-запити
gdf.to_postgis(table_name, engine, if_exists="replace", index=False)

print("SIZE:")
print(f"OSM: {(os.path.getsize('./data_lab_3/my_village.shp')/1048576):.2}MB\n"
      f"GeoJSON: {(os.path.getsize('./data_lab_3/my_village.geojson')/1048576):.2}MB\n"
      f"GeoPackage: {(os.path.getsize('./data_lab_3/my_village.gpkg')/1048576):.2}MB\n")

test_performance('./data_lab_3/my_village.shp', 'Shapefile')
test_performance('./data_lab_3/my_village.geojson', 'GeoJSON')
test_performance('./data_lab_3/my_village.gpkg', 'GeoPackage')
test_performance("postgresql://{user}:{password}@{host}/{db}".format(user=user, password=password, host=host, port=port, db=db), 'PostGIS')

print("Просторова точність:")
space_test('./data_lab_3/my_village.osm', './data_lab_3/my_village.shp', "Shapefile")
space_test('./data_lab_3/my_village.osm', './data_lab_3/my_village.geojson', "GeoJSON")
space_test('./data_lab_3/my_village.osm', './data_lab_3/my_village.gpkg', "GeoPackage")

print("Радіометрична точність")
radio_test('./data_lab_3/my_village.tiff', './data_lab_3/my_village_lzw.tiff', "LZW")
radio_test('./data_lab_3/my_village.tiff', './data_lab_3/my_village_deflate.tiff', "Deflate")
radio_test('./data_lab_3/my_village.tiff', './data_lab_3/my_village_cog.tiff', "COG")
radio_test('./data_lab_3/my_village.tiff', './data_lab_3/my_village_jp2.tiff', "JP2")

build_map()


