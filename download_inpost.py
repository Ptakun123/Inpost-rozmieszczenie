import requests
import json
import time

API_URL = "https://api-global-points.easypack24.net/v1/points"
PER_PAGE = 5000

def fetch_all_points():
    all_points = []
    page = 1
    total_pages = 1

    print(f"Rozpoczynam pobieranie (paczki po {PER_PAGE} rekordów)...")

    # Utrzymanie jednej sesji TCP przyspiesza kolejne zapytania
    with requests.Session() as session:
        while page <= total_pages:
            try:
                response = session.get(API_URL, params={"page": page, "per_page": PER_PAGE}, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if page == 1:
                    total_pages = data.get("total_pages", 1)
                    total_records = data.get("count", 0)
                    print(f"Znaleziono {total_records} rekordów. Stron do pobrania: {total_pages}")

                items = [
                    {
                        "country": item.get("country"),
                        "location": item.get("location")
                    }
                    for item in data.get("items", [])
                ]
                all_points.extend(items)
                
                print(f"Pobrano stronę {page}/{total_pages} ({len(items)} obiektów)")
                page += 1
                
                # Delikatny sleep, aby nie triggerować zabezpieczeń anty-scrapingowych
                time.sleep(0.1)

            except requests.exceptions.RequestException as e:
                print(f"Błąd przy stronie {page}: {e}. Ponawiam próbę za 5 sekund...")
                time.sleep(5)

    print(f"\nZakończono. Całkowita liczba pobranych rekordów: {len(all_points)}")

    with open("inpost_points.json", "w", encoding="utf-8") as f:
        json.dump(all_points, f, ensure_ascii=False, indent=2)

fetch_all_points()
