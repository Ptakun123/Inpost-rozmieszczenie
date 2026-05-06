import geopandas as gpd
import pandas as pd
import pydeck as pdk
import webbrowser
import os
import numpy as np

def create_investment_map(target_country):
    print("=============================================")
    print("Map Generator (Eurostat Style / GPU GridLayer)")
    print("=============================================")

    print("Processing grid into point cloud...")
    try:
        pop_gdf = gpd.read_file("population_grid.gpkg", layer="population")
    except Exception as e:
        print(f"Error loading map data: {e}")
        return False

    # Filter out empty grids
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
        gpu_aggregation=True, # Enabled for better performance
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

    print(f"Loading existing infrastructure for {target_country}...")
    try:
        lockers_gdf = gpd.read_file("inpost_lockers_global.gpkg", layer="lockers").to_crs("EPSG:4326")
        
        # Filter the global database by the selected country
        lockers_gdf = lockers_gdf[lockers_gdf['country'] == target_country]
        
    except Exception as e:
        print(f"Error loading locker data: {e}")
        return False

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
    try:
        top_spots_gdf = gpd.read_file("top_investment_spots.gpkg")
    except Exception as e:
        print(f"Error loading target locations: {e}")
        return False

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
    
    # Calculate map center dynamically based on population grid
    center_lat = pop_points['lat'].mean()
    center_lon = pop_points['lon'].mean()
    view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=5.5, pitch=0)

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

    legend_html = """
    <div style="position: fixed; bottom: 30px; right: 30px; width: 250px; background-color: white; 
                z-index: 1000; padding: 15px; border-radius: 5px; box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
                font-family: Arial, sans-serif; font-size: 14px; color: #333333;">
        <h4 style="margin-top: 0; margin-bottom: 12px; font-size: 16px;">Map Legend</h4>
        
        <div style="margin-bottom: 10px; display: flex; align-items: center;">
            <div style="width: 14px; height: 14px; background-color: rgb(144, 238, 144); border-radius: 50%; margin-right: 10px;"></div>
            <span>Existing Lockers</span>
        </div>
        
        <div style="margin-bottom: 15px; display: flex; align-items: center;">
            <div style="width: 14px; height: 14px; background-color: rgba(0, 100, 255, 0.4); border: 2px solid white; border-radius: 50%; margin-right: 10px; box-shadow: 0 0 0 1px #ccc;"></div>
            <span>Target Locations</span>
        </div>
        
        <div>
            <div style="margin-bottom: 6px;">Population Density (persons/km²)</div>
            <div style="height: 12px; width: 100%; background: linear-gradient(to right, rgb(255, 255, 204), rgb(253, 141, 60), rgb(73, 0, 10)); border-radius: 3px;"></div>
            <div style="display: flex; justify-content: space-between; font-size: 11px; margin-top: 4px; color: #666;">
                <span>Low</span>
                <span>High</span>
            </div>
        </div>
    </div>
    """

    r = pdk.Deck(
        layers=[grid_layer, lockers_layer, targets_layer],
        initial_view_state=view_state,
        map_style=pdk.map_styles.LIGHT, 
        tooltip=tooltip,
        description=legend_html
    )
    
    output_file = os.path.abspath("inpost_investment_map.html")
    r.to_html(output_file)

    print(f"\nSuccess! File saved: {output_file}")
    
    try:
        webbrowser.open('file://' + output_file)
    except Exception:
        print("Use 'explorer.exe inpost_investment_map.html' from the WSL terminal.")

    return True