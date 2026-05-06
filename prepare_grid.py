import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
import re
import subprocess
import os

def extract_and_grid(country_code, input_csv):
    temp_csv = f"{country_code}_temp_filtered.csv"
    search_pattern = f"{country_code}_"

    print(f"Filtering {input_csv} for {country_code} to temporary file...")
    
    try:
        # Zapisujemy nagłówek do pliku tymczasowego
        with open(temp_csv, 'w') as f:
            subprocess.run(['head', '-n', '1', input_csv], stdout=f)
        
        # Dopisujemy przefiltrowane dane (strumieniowo, bez wczytywania do RAMu)
        with open(temp_csv, 'a') as f:
            subprocess.run(['grep', search_pattern, input_csv], stdout=f)
            
        print(f"Filtering done. Processing temporary file in chunks...")
        
        # Wczytujemy przefiltrowany (znacznie mniejszy) plik w kawałkach
        chunksize = 100000
        matched_chunks = []
        for chunk in pd.read_csv(temp_csv, chunksize=chunksize, low_memory=False):
            matched = chunk[chunk['OBS_VALUE'] > 0]
            matched_chunks.append(matched)
            
        df = pd.concat(matched_chunks)
        
        # Usuwamy plik tymczasowy po wczytaniu
        if os.path.exists(temp_csv):
            os.remove(temp_csv)
            
    except Exception as e:
        print(f"Fast-filtering failed: {e}")
        return

    print(f"Remaining {len(df)} grid cells. Generating geometries...")

    def create_grid_polygon(spatial_id):
        match = re.search(r'N(\d+)E(\d+)', str(spatial_id))
        if match:
            y_bottom = int(match.group(1))
            x_left = int(match.group(2))
            size = 1000
            return Polygon([
                (x_left, y_bottom),               
                (x_left + size, y_bottom),        
                (x_left + size, y_bottom + size), 
                (x_left, y_bottom + size)
            ])
        return None

    df['geometry'] = df['SPATIAL'].apply(create_grid_polygon)
    df = df.dropna(subset=['geometry'])

    grid_gdf = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:3035")
    population_grid = grid_gdf[['SPATIAL', 'OBS_VALUE', 'geometry']].copy()
    population_grid.rename(columns={'OBS_VALUE': 'population'}, inplace=True)

    # Zapis z jawną warstwą, o którą prosiłeś wcześniej
    print("Saving to population_grid.gpkg...")
    population_grid.to_file("population_grid.gpkg", driver="GPKG", layer="population")
    print("Done.")