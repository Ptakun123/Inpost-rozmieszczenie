import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
import re
import os

def extract_and_grid(country_code, input_csv):
    temp_csv = f"{country_code}_temp_filtered.csv"
    search_pattern = f"{country_code}_"

    print(f"Filtering {input_csv} for {country_code} using Python line-reader...")
    
    try:
        with open(input_csv, 'r', encoding='utf-8') as infile, \
             open(temp_csv, 'w', encoding='utf-8') as outfile:
            
            header = infile.readline()
            outfile.write(header)
            
            for line in infile:
                if search_pattern in line:
                    outfile.write(line)
                    
        print("Filtering done. Loading matched data into memory...")
        
        df = pd.read_csv(temp_csv, low_memory=False)
        df = df[df['OBS_VALUE'] > 0]
        
        if os.path.exists(temp_csv):
            os.remove(temp_csv)
            
    except FileNotFoundError:
        print(f"Error: File {input_csv} not found. Please check the path.")
        return False
    except Exception as e:
        print(f"Error during filtering: {e}")
        return False

    if df.empty:
        print(f"Error: No population data found for country '{country_code}'.")
        return False

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

    if df.empty:
        print("Error: Failed to generate grid geometries.")
        return False

    grid_gdf = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:3035")
    population_grid = grid_gdf[['SPATIAL', 'OBS_VALUE', 'geometry']].copy()
    population_grid.rename(columns={'OBS_VALUE': 'population'}, inplace=True)

    print("Saving to population_grid.gpkg...")
    population_grid.to_file("population_grid.gpkg", driver="GPKG", layer="population")
    print("Done.")
    
    return True