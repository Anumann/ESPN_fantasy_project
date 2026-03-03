# name_merger.py
import config
import time
from espn_api.football import League
from thefuzz import process, fuzz
import json
import itertools

# Delay between API requests to avoid rate-limiting
DELAY_SECONDS = 3

def get_all_owners():
    """
    Loops backwards from the current year to fetch all unique owners
    from all historical seasons of the league.
    """
    all_owners = set()
    current_year = 2025 # Starting year, could be dynamic

    print("--- Starting to Fetch All Historical Owners ---")
    
    while True:
        try:
            print(f"Fetching data for the {current_year} season...")
            league = League(
                league_id=config.LEAGUE_ID,
                year=current_year,
                espn_s2=config.ESPN_S2,
                swid=config.SWID
            )
            
            if not league.teams:
                print(f"No teams found for {current_year}. Assuming end of league history.")
                break

            season_owners = set()
            for team in league.teams:
                # Construct owner name, handling cases with no owner info
                owner_name = " ".join([
                    team.owners[0].get('firstName', ''), 
                    team.owners[0].get('lastName', '')
                ]).strip() if team.owners and team.owners[0] else None

                if owner_name:
                    season_owners.add(owner_name)
            
            if not season_owners:
                print(f"No owners found for {current_year}. Stopping.")
                break

            print(f"Found {len(season_owners)} owners in {current_year}.")
            all_owners.update(season_owners)
            
            current_year -= 1
            time.sleep(DELAY_SECONDS)

        except Exception as e:
            print(f"Could not retrieve league data for year {current_year}. Likely end of history. Error: {e}")
            break
            
    print(f"\n--- Found a total of {len(all_owners)} unique historical owners ---")
    return sorted(list(all_owners))

def generate_owner_map(owners, similarity_threshold=85):
    """
    Compares all owner names and generates a mapping for similar names.
    Selects the shortest name in a similar group as the canonical name.
    """
    print(f"\n--- Generating Owner Map (Similarity Threshold: {similarity_threshold}%) ---")
    owner_map = {}
    processed_owners = set()

    for owner1, owner2 in itertools.combinations(owners, 2):
        if owner1 in processed_owners or owner2 in processed_owners:
            continue

        # Use token_sort_ratio for better matching of names with middle initials
        score = fuzz.token_sort_ratio(owner1, owner2)
        
        if score >= similarity_threshold:
            # Group all similar names together
            similar_group = {owner1, owner2}
            
            # Find the shortest name in the group to be the canonical name
            canonical_name = min(similar_group, key=len)
            
            print(f"Found similar group: {similar_group} -> Canonical: '{canonical_name}' (Score: {score})")
            
            for name in similar_group:
                if name != canonical_name:
                    owner_map[name] = canonical_name
                processed_owners.add(name)

    print("\n--- Generated Name Mapping ---")
    if not owner_map:
        print("No similar names found that met the threshold.")
    else:
        print(json.dumps(owner_map, indent=2))
        
    return owner_map

def save_map_to_file(owner_map, filename="owner_map.json"):
    """Saves the generated owner map to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(owner_map, f, indent=2)
    print(f"\n--- Mapping saved to {filename} ---")

if __name__ == "__main__":
    historical_owners = get_all_owners()
    if historical_owners:
        # Lowering threshold to 80 to catch names with middle names/suffixes
        name_map = generate_owner_map(historical_owners, similarity_threshold=80)
        save_map_to_file(name_map)
