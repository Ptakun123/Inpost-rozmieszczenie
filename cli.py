import argparse
import os
from download_inpost import fetch_all_points
from prepare_grid import extract_and_grid
from calculate_points import calculate_scores
from algorithm import optimize_locations
from generate_map import create_investment_map

def main():
    parser = argparse.ArgumentParser(description="InPost Locker Location Optimization CLI")
    
    # Logic Switches
    parser.add_argument("--fetch", action="store_true", help="Download latest locker data from InPost API")
    parser.add_argument("--grid", action="store_true", help="Extract population and generate grid (Slow, requires Census CSV)")
    parser.add_argument("--score", action="store_true", help="Recalculate distance scores (Required if lockers or grid changed)")
    
    # Parameters
    parser.add_argument("--country", type=str, default="PL", help="Target country code (default: PL)")
    parser.add_argument("--census", type=str, default="ESTAT_Census_2021_V2.csv", help="Path to Eurostat Census CSV")
    parser.add_argument("--radius", type=int, default=2000, help="Search radius in meters (default: 2000)")
    parser.add_argument("--lockers", type=int, default=20, help="Number of new lockers to place (default: 20)")
    parser.add_argument("--exclusion", type=int, default=5000, help="Exclusion radius in meters (default: 5000)")

    args = parser.parse_args()

    print(f"\n--- Initiating pipeline for country: {args.country} ---")
    
    # 1. Fetching Locker Data
    if args.fetch or not os.path.exists("inpost_lockers.gpkg"):
        print("\n[1/5] Fetching locker data...")
        fetch_all_points(target_country=args.country)
    else:
        print("\n[1/5] Skipping fetch (using existing inpost_lockers.gpkg)")

    # 2. Grid Generation
    if args.grid or not os.path.exists("population_grid.gpkg"):
        print("\n[2/5] Generating population grid...")
        extract_and_grid(args.country, args.census)
    else:
        print("\n[2/5] Skipping grid generation (using existing population_grid.gpkg)")

    # 3. Distance and Score Calculation
    if args.score or not os.path.exists("calculated_score.gpkg"):
        print("\n[3/5] Calculating distances and base scores...")
        calculate_scores()
    else:
        print("\n[3/5] Skipping score calculation (using existing calculated_score.gpkg)")

    # 4. Optimization (Always runs as it is fast and depends on CLI params)
    print("\n[4/5] Executing optimization algorithm...")
    optimize_locations(args.radius, args.lockers, args.exclusion)
    
    # 5. Map Visualization
    print("\n[5/5] Generating HTML map...")
    create_investment_map()
    
    print("\n--- Process completed successfully ---")

if __name__ == "__main__":
    main()