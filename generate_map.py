import geopandas as gpd
import pandas as pd
import pydeck as pdk
import webbrowser
import os
import numpy as np

def create_investment_map():
    print("=============================================")
    print("Map Generator (Eurostat Style / GPU GridLayer)")
    print("=============================================")

    print("Processing grid into point cloud...")
    pop_gdf = gpd.read_file("population_grid.gpkg")
    pop_gdf = pop_gdf[pop_gdf['population'] > 0].copy()

    pop_centroids_gps = pop_gdf.centroid.to_crs("EPSG:4326")
    
    pop_points = pd.DataFrame({
        'lon': pop_centroids_gps.x,
        'lat': pop_centroids_gps.y,
        'population': pop_gdf['population']
    })
    pop_points['pop_log'] = np.log10(pop_points['population'] + 1)

    print(f"Generated a cloud of {len(pop_points):,} points for rendering.")

    grid_layer = pdk.Layer(
        "GridLayer",
        pop_points,
        pickable=True,         
        extruded=False,
        cell_size=1000,
        get_position="[lon, lat]",
        get_color_weight="pop_log", 
        color_aggregation=pdk.types.String("MAX"),
        color_domain=[1.0, 4.5],
        get_elevation_weight="population",
        elevation_aggregation=pdk.types.String("MAX"),
        gpu_aggregation=False,
        opacity=0.75,
        color_range=[
            [255, 255, 204, 160],
            [255, 237, 160, 160],
            [254, 217, 118, 160],
            [254, 178, 76, 160], 
            [253, 141, 60, 160], 
            [252, 78, 42, 160],  
            [227, 26, 28, 160],  
            [189, 0, 38, 160],   
            [128, 0, 38, 160],   
            [73, 0, 10, 160]     
        ],
    )

    print("Loading existing infrastructure...")
    lockers_gdf = gpd.read_file("inpost_lockers.gpkg").to_crs("EPSG:4326")
    lockers_df = pd.DataFrame({
        'lon': lockers_gdf.geometry.x,
        'lat': lockers_gdf.geometry.y
    })

    lockers_layer = pdk.Layer(
        "ScatterplotLayer",
        lockers_df,
        get_position="[lon, lat]",
        get_color="[144, 238, 144, 160]",
        get_radius=200,
        radius_max_pixels=5,
        pickable=False,
    )

    print("Loading target locations...")
    top_spots_gdf = gpd.read_file("top_investment_spots.gpkg")
    top_spots_gps = top_spots_gdf.centroid.to_crs("EPSG:4326")
    
    dynamic_radius = top_spots_gdf['search_radius'].iloc[0] if 'search_radius' in top_spots_gdf.columns else 2000

    targets_df = pd.DataFrame({
        'lon': top_spots_gps.x,
        'lat': top_spots_gps.y,
        'score': top_spots_gdf.get('neighborhood_score', top_spots_gdf.get('score', 0)),
        'population': top_spots_gdf['population']
    })

    targets_layer = pdk.Layer(
        "ScatterplotLayer",
        targets_df,
        get_position="[lon, lat]",
        get_fill_color="[0, 100, 255, 100]", 
        get_line_color="[255, 255, 255, 200]",
        stroked=True,
        line_width_min_pixels=3,
        get_radius=int(dynamic_radius),
        radius_min_pixels=13,
        pickable=False,
    )

    print("Generating HTML file...")
    view_state = pdk.ViewState(latitude=52.0693, longitude=19.4803, zoom=5.5, pitch=0)

    tooltip = {
        "html": "<b style='font-size: 15px;'>{elevationValue}</b> persons/km2",
        "style": {
            "backgroundColor": "white",
            "color": "#333333",
            "font-family": "Arial, sans-serif",
            "font-size": "14px",
            "padding": "6px 10px",
            "box-shadow": "2px 2px 6px rgba(0,0,0,0.3)",
            "border": "none",
            "border-radius": "2px"
        }
    }

    r = pdk.Deck(
        layers=[grid_layer, lockers_layer, targets_layer],
        initial_view_state=view_state,
        map_style=pdk.map_styles.LIGHT, 
        tooltip=tooltip
    )
    output_file = os.path.abspath("inpost_investment_map_optimized.html")
    r.to_html(output_file)

    print(f"\nSuccess! File saved: {output_file}")
    
    try:
        webbrowser.open('file://' + output_file)
    except Exception:
        print("Use 'explorer.exe inpost_investment_map.html' from the WSL terminal.")

if __name__ == "__main__":
    create_investment_map()