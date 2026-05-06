from sklearn.neighbors import radius_neighbors_graph
from scipy.spatial import cKDTree
import numpy as np
import geopandas as gpd

def optimize_locations(search_radius_meters, number_of_new_lockers, exclusion_radius_meters):
    candidates = gpd.read_file("calculated_score.gpkg", layer="scores").reset_index(drop=True)
    coords = np.column_stack((candidates.geometry.centroid.x, candidates.geometry.centroid.y))
    scores = candidates['score'].values

    sparse_graph = radius_neighbors_graph(
        coords, radius=search_radius_meters, mode='connectivity', include_self=True, n_jobs=-1
    )
    candidates['neighborhood_score'] = sparse_graph.dot(scores)

    tree = cKDTree(coords)
    active_mask = np.ones(len(candidates), dtype=bool)
    active_mask[candidates['population'] <= 0] = False
    sorted_indices = np.argsort(-candidates['neighborhood_score'].values)
    
    selected_indices = []
    for idx in sorted_indices:
        if len(selected_indices) >= number_of_new_lockers: break
        if active_mask[idx]:
            selected_indices.append(idx)
            active_mask[tree.query_ball_point(coords[idx], r=exclusion_radius_meters)] = False

    top_spots_gdf = gpd.GeoDataFrame(candidates.iloc[selected_indices].copy(), geometry='geometry', crs="EPSG:3035")
    top_spots_gdf['search_radius'] = search_radius_meters
    top_spots_gdf.to_file("top_investment_spots.gpkg", driver="GPKG")