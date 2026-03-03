# run_full_history_fix.py
import time
from final_extractor import fetch_and_store_season_data

def main():
    """
    Loops through all historical years that are known to be incomplete
    and runs the final, corrected extractor for each.
    """
    print("--- Starting Full Historical Data Repair ---")
    
    # Years 2023 down to 2016 are incomplete. 2025 and 2024 are now correct.
    for year in range(2023, 2015, -1):
        fetch_and_store_season_data(year)
        time.sleep(5) # API delay
        
    print("--- Full Historical Data Repair Complete ---")

if __name__ == '__main__':
    main()
