from sklearn.neighbors import radius_neighbors_graph
from scipy.spatial import cKDTree
import numpy as np
import pandas as pd
import geopandas as gpd

print("Running Ultra-Optimized Focal Statistics (Sparse Matrix Math)...")

# 1. Filter candidates
candidates = gpd.read_file("calculated_score.gpkg")


if candidates.empty:
    raise ValueError("No grids left. Adjust your base distance filter.")

#Reset index to ensure matrix rows align perfectly with DataFrame indices
candidates = candidates.reset_index(drop=True)

# 2. Extract coordinates and scores
print("Extracting coordinates...")
coords = np.column_stack((candidates.geometry.centroid.x, candidates.geometry.centroid.y))
scores = candidates['score'].values

# 3. Parameters
search_radius_meters = 2000  
number_of_new_lockers = 20
exclusion_radius_meters = 5000 

print(f"Building C-level sparse graph for {len(candidates)} grids (Radius: {search_radius_meters/1000}km)...")

# 4. Create a Sparse Connectivity Matrix
# This avoids Python lists entirely. It builds a highly compressed memory structure.
# n_jobs=-1 uses all CPU threads to build it instantly.
sparse_graph = radius_neighbors_graph(
    coords, 
    radius=search_radius_meters, 
    mode='connectivity', 
    include_self=True, 
    n_jobs=-1
)

print("Calculating 3.5 million neighborhood sums using Matrix Multiplication...")
# 5. The Magic Trick: Matrix Dot Product
# Multiplying the sparse graph by the scores array instantly calculates the neighborhood sum 
# for every single point simultaneously without any loops.
neighborhood_scores = sparse_graph.dot(scores)
candidates['neighborhood_score'] = neighborhood_scores

# 6. Greedy Selection with Non-Maximum Suppression (NMS)
print("Running fast Non-Maximum Suppression...")

# We only build the KD-Tree for the suppression phase, querying ONLY the top spots, not all 3.5M
tree = cKDTree(coords)
active_mask = np.ones(len(candidates), dtype=bool)

active_mask[candidates['population'] <= 0] = False
# Sort descending
sorted_indices = np.argsort(-neighborhood_scores)
selected_indices = []

for idx in sorted_indices:
    if len(selected_indices) >= number_of_new_lockers:
        break
        
    if active_mask[idx]:
        selected_indices.append(idx)
        
        # Query the tree ONLY for the single winning coordinate
        eliminated_indices = tree.query_ball_point(coords[idx], r=exclusion_radius_meters)
        
        # Suppress grids inside the 5km exclusion zone
        active_mask[eliminated_indices] = False

# 7. Format results
top_spots_df = candidates.iloc[selected_indices].copy()
top_spots_df['search_radius'] = search_radius_meters # <-- Przekazanie promienia

print("\n=== TOP 20 LOCATIONS (CHOSEN BY NEIGHBORHOOD POTENTIAL) ===")
print(top_spots_df[['SPATIAL', 'population', 'score', 'neighborhood_score', 'distance_km']].to_string(index=False))


print("\nZapisywanie rekomendowanych lokalizacji do pliku...")

top_spots_gdf = gpd.GeoDataFrame(top_spots_df, geometry='geometry', crs="EPSG:3035")

top_spots_gdf.to_file("top_investment_spots.gpkg", driver="GPKG")
print("Zapisano plik: top_investment_spots.gpkg")
