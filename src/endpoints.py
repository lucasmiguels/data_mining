import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point
from sklearn.preprocessing import MinMaxScaler
from geopy.distance import geodesic
import shapely
import psycopg2
import folium
import warnings
warnings.filterwarnings('ignore')

# Conexão com o banco
conn = psycopg2.connect(
    dbname="geodata",
    user="postgres",
    password="postgres",
    host="localhost",
    port="5432"
)

# Funções auxiliares
def calculate_distance(p1, p2):
    return geodesic(p1, p2).meters

def normalize_column(df, col):
    scaler = MinMaxScaler()
    df[[col]] = scaler.fit_transform(df[[col]])
    return df

def create_grid(bounds, n_cells=1500, crs="EPSG:4326"):
    xmin, ymin, xmax, ymax = bounds
    cell_size = (xmax - xmin) / n_cells
    grid_cells = []
    for x0 in np.arange(xmin, xmax + cell_size, cell_size):
        for y0 in np.arange(ymin, ymax + cell_size, cell_size):
            x1, y1 = x0 - cell_size, y0 + cell_size
            grid_cells.append(shapely.geometry.box(x0, y0, x1, y1))
    return gpd.GeoDataFrame(grid_cells, columns=["geometry"], crs=crs)

def stat_day_per_line(gdf, grid):
    gdf = gdf.set_geometry('geometry')
    gdf['hour'] = gdf['datahora'].dt.hour
    gdf['save_geometry'] = gdf['geometry']
    joined = gpd.sjoin(grid, gdf, predicate='contains', how='inner')
    stats = joined.groupby(['grid_id', 'geometry']).agg(
        count=('geometry', 'size'),
        median_time=('hour', 'median'),
        median_velocidade=('velocidade', 'median'),
        centroid=('save_geometry', lambda x: Point(x.x.mean(), x.y.mean()))
    ).reset_index()
    return stats

def choose_endpoints(stats):
    candidates = stats[
        (stats['median_velocidade'] == 0)    
        ]
    if candidates.empty:
        return None, None

    initial = candidates.sort_values('count', ascending=False).iloc[0]
    start = initial['centroid']
    candidates = candidates[candidates['grid_id'] != initial['grid_id']]
    candidates['dist'] = candidates['centroid'].apply(lambda x: calculate_distance((x.y, x.x), (start.y, start.x)))
    candidates = normalize_column(candidates, 'count')
    candidates = normalize_column(candidates, 'dist')
    candidates['score'] = candidates['count'] + candidates['dist']

    if candidates.empty:
        return start, None

    end = candidates.sort_values('score', ascending=False).iloc[0]['centroid']
    return start, end
def plot_endpoints_map(linha_id, gdf, grid_filtered, start, end):
    map_center = [gdf['geometry'].y.mean(), gdf['geometry'].x.mean()]
    m = folium.Map(location=map_center, zoom_start=14)

    # Grade filtrada com pontos significativos
    for _, row in grid_filtered.iterrows():
        folium.GeoJson(row.geometry).add_to(m)
        folium.Circle(location=[row.centroid.y, row.centroid.x],
                      radius=3, color='red', fill=True).add_to(m)

    # Start point
    folium.Circle(location=[start.y, start.x],
                  radius=30, color='green', fill=True, fill_color='green',
                  popup='Start Point').add_to(m)

    # End point
    folium.Circle(location=[end.y, end.x],
                  radius=30, color='purple', fill=True, fill_color='purple',
                  popup='End Point').add_to(m)

    m.save(f"../maps/endpoints_map_{linha_id}.html")

# Área de cobertura (RJ)
rio_bounds = (-43.7955, -23.0824, -43.1039, -22.7448)
grid = create_grid(rio_bounds, n_cells=1500).reset_index(names='grid_id')

linhas = [
    '3', '100', '108', '138', '232', '2336', '2803', '292', '298', '309', '315',
    '324', '328', '343', '355', '371', '388', '397', '399', '415', '422', '457',
    '483', '497', '550', '553', '554', '557', '565', '606', '624', '629', '634',
    '638', '639', '665', '756', '759', '774', '779', '803', '838', '852', '864',
    '867', '878', '905', '917', '918'
]
# linhas = ['100']

for linha in linhas:
    print(f"Processando linha: {linha}")
    query = f"""
        SELECT *, geom AS geometry 
        FROM vw_gps_filtrado 
        WHERE linha = '{linha}'
    """
    gdf = gpd.read_postgis(query, conn, geom_col='geometry', crs='EPSG:4326')
    if gdf.empty:
        print("Sem dados.")
        continue

    stats = stat_day_per_line(gdf, grid)
    start, end = choose_endpoints(stats)
    if not start or not end:
        print("Não foi possível determinar os terminais.")
        continue

    print(f"Início: {start.wkt}, Fim: {end.wkt}")
    grid_filtered = stats[
    (stats['count'] > stats['count'].quantile(0.5)) &
    (stats['median_velocidade'] > 0)
    ]
    # Salvar mapa .html
    plot_endpoints_map(linha, gdf, grid_filtered, start, end)

    # with conn.cursor() as cur:
    #     cur.execute("""
    #         INSERT INTO bus_end_points (linha, start_point, end_point)
    #         VALUES (%s, ST_GeomFromText(%s, 4326), ST_GeomFromText(%s, 4326))
    #         ON CONFLICT (linha) DO UPDATE 
    #         SET start_point = EXCLUDED.start_point,
    #             end_point = EXCLUDED.end_point
    #     """, (linha, start.wkt, end.wkt))
    #     conn.commit()
