import argparse
import os
import sys
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
    
    # 1. Fetching Global Locker Data
    if args.fetch or not os.path.exists("inpost_lockers_global.gpkg"):
        print("\n[1/5] Fetching global locker data...")
        if fetch_all_points() is False:
            print("Error: Stopping process. Failed to fetch locker data.")
            sys.exit(1)
    else:
        print("\n[1/5] Skipping fetch (using existing inpost_lockers_global.gpkg)")

    # 2. Grid Generation
    if args.grid or not os.path.exists("population_grid.gpkg"):
        print("\n[2/5] Generating population grid...")
        if extract_and_grid(args.country, args.census) is False:
            print("Error: Stopping process. Failed to generate population grid.")
            sys.exit(1)
    else:
        print("\n[2/5] Skipping grid generation (using existing population_grid.gpkg)")

# 3. Distance and Score Calculation
    if args.score or not os.path.exists("calculated_score.gpkg"):
        print(f"\n[3/5] Calculating distances and base scores for {args.country}...")
        if calculate_scores(args.country) is False:
            print("Error: Stopping process. Failed to calculate scores.")
            sys.exit(1)
    else:
        print("\n[3/5] Skipping score calculation (using existing calculated_score.gpkg)")

    # 4. Optimization
    print("\n[4/5] Executing optimization algorithm...")
    if optimize_locations(args.radius, args.lockers, args.exclusion) is False:
        print("Error: Stopping process. Optimization algorithm encountered an issue.")
        sys.exit(1)
    
    # 5. Map Visualization
    print("\n[5/5] Generating HTML map...")
    if create_investment_map(args.country) is False:
        print("Error: Stopping process. Failed to generate the map.")
        sys.exit(1)
    
    print("\n--- Process completed successfully ---")
if __name__ == "__main__":
    main()