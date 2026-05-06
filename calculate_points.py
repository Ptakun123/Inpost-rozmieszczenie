import geopandas as gpd

def calculate_scores(target_country):
    print(f"Loading grid and global lockers, filtering for {target_country}...")
    try:
        population_grid = gpd.read_file("population_grid.gpkg", layer="population")
        lockers = gpd.read_file("inpost_lockers_global.gpkg", layer="lockers")
    except Exception as e:
        print(f"Error: Missing input files: {e}")
        return False

    # Filter lockers by the requested country
    lockers = lockers[lockers['country'] == target_country]

    population_grid = population_grid[population_grid["population"] > 0]

    if population_grid.empty:
        print("Error: Population grid is empty.")
        return False
    if lockers.empty:
        print(f"Error: Lockers table is empty for country '{target_country}'.")
        return False

    centroids_gdf = population_grid.copy()
    centroids_gdf['geometry'] = centroids_gdf.geometry.centroid

    nearest_lockers = gpd.sjoin_nearest(
        centroids_gdf, 
        lockers, 
        how="left", 
        distance_col="distance_meters"
    )
    nearest_lockers = nearest_lockers[~nearest_lockers.index.duplicated(keep='first')]

    population_grid['distance_km'] = nearest_lockers['distance_meters'] / 1000
    population_grid = population_grid[population_grid["distance_km"] > 1]
    population_grid['score'] = population_grid['population'] * population_grid['distance_km']

    population_grid.to_file("calculated_score.gpkg", driver="GPKG", layer="scores")
    
    return True