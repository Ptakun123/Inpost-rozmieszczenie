import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
import re

print("Loading data...")

df = pd.read_csv("PL_population.csv", low_memory=False)

df = df[df['OBS_VALUE'] > 0]

print(f"Remaining {len(df)} populated grid cells to process.")
def create_grid_polygon(spatial_id):
    match = re.search(r'N(\d+)E(\d+)', str(spatial_id))
    if match:
        y_bottom = int(match.group(1)) # Northing
        x_left = int(match.group(2))   # Easting
        
        size = 1000
        
        return Polygon([
            (x_left, y_bottom),               
            (x_left + size, y_bottom),        
            (x_left + size, y_bottom + size), 
            (x_left, y_bottom + size)
        ])
    return None

print("Generating geometries (this may take a moment)...")
df['geometry'] = df['SPATIAL'].apply(create_grid_polygon)

df = df.dropna(subset=['geometry'])

print("Converting to map layer...")
grid_gdf = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:3035")

final_grid = grid_gdf[['SPATIAL', 'OBS_VALUE', 'geometry']].copy()
final_grid.rename(columns={'OBS_VALUE': 'population'}, inplace=True)

print("Saving final grid to GeoPackage...")
final_grid.to_file("calculated_grid.gpkg", driver="GPKG")
print("Saved successfully.")
