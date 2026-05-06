import geopandas as gpd

def calculate_scores():
    print("Loading grid and lockers...")
    population_grid = gpd.read_file("population_grid.gpkg", layer="population")
    population_grid = population_grid[population_grid["population"] > 0]
    lockers = gpd.read_file("inpost_lockers.gpkg", layer="lockers")

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

    population_grid.to_file("calculated_score.gpkg", driver="GPKG",layer="scores")