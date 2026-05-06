import json
from shapely.geometry import Point
import geopandas as gpd

print("Loading pre-calculated grid...")

population_grid = gpd.read_file("population_grid.gpkg")
population_grid = population_grid[population_grid["population"] > 0]
lockers = gpd.read_file("inpost_lockers.gpkg")



print("Calculating distances to nearest lockers (using spatial indexing)...")

centroids_gdf = population_grid.copy()
centroids_gdf['geometry'] = centroids_gdf.geometry.centroid

nearest_lockers = gpd.sjoin_nearest(
    centroids_gdf, 
    lockers, 
    how="left", 
    distance_col="distance_meters"
)

nearest_lockers = nearest_lockers[~nearest_lockers.index.duplicated(keep='first')]

print("Calculating prioritization score...")
population_grid['distance_meters'] = nearest_lockers['distance_meters']
population_grid['distance_km'] = population_grid['distance_meters'] / 1000
# Only counting grids where distance > 1km due to resolution of the population map
population_grid = population_grid[population_grid["distance_km"] > 1]

# Formula: Score = Population * Distance (in kilometers)
population_grid['score'] = population_grid['population'] * population_grid['distance_km']

top_spots = population_grid.sort_values(by="score", ascending=False)

population_grid.to_file("calculated_score.gpkg", driver="GPKG")

#print("\n=== TOP 10 PRIORITY ZONES (White Spots) ===")
#print(top_spots[['SPATIAL', 'population', 'distance_km', 'score']].head(10).to_string(index=False))
