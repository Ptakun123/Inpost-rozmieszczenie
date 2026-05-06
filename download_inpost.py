import requests
import time
import geopandas as gpd
from shapely.geometry import Point

API_URL = "https://api-global-points.easypack24.net/v1/points"
PER_PAGE = 5000

def fetch_all_points(target_country="PL"):
    all_points = []
    page = 1
    total_pages = 1

    print(f"Starting download (batches of {PER_PAGE} records)...")

    # Maintaining a single TCP session speeds up subsequent requests
    with requests.Session() as session:
        while page <= total_pages:
            try:
                response = session.get(API_URL, params={"page": page, "per_page": PER_PAGE}, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if page == 1:
                    total_pages = data.get("total_pages", 1)
                    total_records = data.get("count", 0)
                    print(f"Found {total_records} records. Pages to download: {total_pages}")

                items = [
                    {
                        "country": item.get("country"),
                        "location": item.get("location")
                    }
                    for item in data.get("items", [])
                ]
                all_points.extend(items)
                
                print(f"Downloaded page {page}/{total_pages} ({len(items)} items)")
                page += 1
                
                # Gentle sleep to avoid triggering anti-scraping protections
                time.sleep(0.1)

            except requests.exceptions.RequestException as e:
                print(f"Error at page {page}: {e}. Retrying in 5 seconds...")
                time.sleep(5)

    print(f"\nFinished. Total records downloaded: {len(all_points)}")
    
    lockers = []
    
    for item in all_points:
        if item.get("country") == target_country and item.get("location"):
            lon = item["location"].get("longitude")
            lat = item["location"].get("latitude")
            
            if lon and lat and lon != 0.0 and lat != 0.0:
                lockers.append(Point(lon, lat))

    print(f"Loaded {len(lockers)} valid locker locations for {target_country}.")

    if not lockers:
        print("No data to save. Exiting.")
        return

    lockers_gdf = gpd.GeoDataFrame(geometry=lockers, crs="EPSG:4326")

    print("Reprojecting InPost data to EPSG:3035...")
    lockers_gdf = lockers_gdf.to_crs("EPSG:3035")
    
    output_filename = "inpost_lockers.gpkg"
    
    lockers_gdf.to_file(output_filename, driver="GPKG", layer="lockers")
    print(f"Successfully saved spatial data to: {output_filename}")
