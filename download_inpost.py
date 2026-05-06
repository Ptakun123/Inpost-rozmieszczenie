import requests
import json
import time

API_URL = "https://api-global-points.easypack24.net/v1/points"
PER_PAGE = 5000

def fetch_all_points():
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

    with open("inpost_points.json", "w", encoding="utf-8") as f:
        json.dump(all_points, f, ensure_ascii=False, indent=2)

fetch_all_points()