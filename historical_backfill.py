# historical_backfill.py
import time
from data_extractor import fetch_and_store_data

START_YEAR = 2024
# A reasonable earliest year for fantasy football on this platform
END_YEAR_CUTOFF = 2010 
# Delay between requests to avoid rate-limiting
DELAY_SECONDS = 5

def main():
    """Loops backwards from START_YEAR to backfill historical data."""
    print("--- Starting Historical Data Backfill ---")
    for year in range(START_YEAR, END_YEAR_CUTOFF - 1, -1):
        print("-" * 40)
        success = fetch_and_store_data(year)
        
        if not success:
            print(f"Stopping backfill. No data found for year {year} or an error occurred.")
            break
        
        print(f"Successfully processed {year}. Waiting for {DELAY_SECONDS} seconds.")
        time.sleep(DELAY_SECONDS)
        
    print("-" * 40)
    print("--- Historical Data Backfill Complete ---")

if __name__ == '__main__':
    main()
