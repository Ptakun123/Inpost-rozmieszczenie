import json
from shapely.geometry import Point
import geopandas as gpd

print("Loading pre-calculated grid...")

final_grid = gpd.read_file("calculated_grid.gpkg")


print("Loading InPost lockers data...")
with open("inpost_points.json", "r", encoding="utf-8") as f:
    inpost_data = json.load(f)

lockers = []
for item in inpost_data:
    if item.get("country") == "PL" and item.get("location"):
        lon = item["location"].get("longitude")
        lat = item["location"].get("latitude")
        
        # Omit missing data and test locations (0.0, 0.0)
        if lon and lat and lon != 0.0 and lat != 0.0:
            lockers.append(Point(lon, lat))

print(f"Loaded {len(lockers)} valid locker locations.")

lockers_gdf = gpd.GeoDataFrame(geometry=lockers, crs="EPSG:4326")

print("Reprojecting InPost data to EPSG:3035...")
lockers_gdf = lockers_gdf.to_crs("EPSG:3035")

print("Calculating distances to nearest lockers (using spatial indexing)...")

centroids_gdf = final_grid.copy()
centroids_gdf['geometry'] = centroids_gdf.geometry.centroid

nearest_lockers = gpd.sjoin_nearest(
    centroids_gdf, 
    lockers_gdf, 
    how="left", 
    distance_col="distance_meters"
)

nearest_lockers = nearest_lockers[~nearest_lockers.index.duplicated(keep='first')]

print("Calculating prioritization score...")
final_grid['distance_meters'] = nearest_lockers['distance_meters']
final_grid['distance_km'] = final_grid['distance_meters'] / 1000
# Only counting grids where distance > 1km due to resolution of the population map
final_grid = final_grid[final_grid["distance_km"] > 1]

# Formula: Score = Population * Distance (in kilometers)
final_grid['score'] = final_grid['population'] * final_grid['distance_km']

top_spots = final_grid.sort_values(by="score", ascending=False)

final_grid.to_file("calculated_score.gpkg", driver="GPKG")

#print("\n=== TOP 10 PRIORITY ZONES (White Spots) ===")
#print(top_spots[['SPATIAL', 'population', 'distance_km', 'score']].head(10).to_string(index=False))
