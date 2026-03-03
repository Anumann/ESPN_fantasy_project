# debug_owner_data.py
import config
from espn_api.football import League
import json

def main():
    """
    Connects to the league for a single year and prints the raw data
    structure for the 'owners' attribute of the first team found.
    """
    try:
        league = League(
            league_id=config.LEAGUE_ID,
            year=2025,
            espn_s2=config.ESPN_S2,
            swid=config.SWID
        )
        
        if not league.teams:
            print("Could not fetch any teams.")
            return

        # Get the first team for inspection
        first_team = league.teams[0]
        
        print("--- Inspecting Team Object ---")
        print(f"Team Name: {first_team.team_name}")
        
        print("\n--- Raw 'owners' Attribute ---")
        # The 'owners' attribute is a list of dicts. We'll print it.
        print(json.dumps(first_team.owners, indent=2))
        
        # This confirms that the owner ID is under the 'id' key.
        # Let's test the access directly.
        if first_team.owners and isinstance(first_team.owners, list) and len(first_team.owners) > 0:
            owner_info = first_team.owners[0]
            if isinstance(owner_info, dict):
                owner_id = owner_info.get('id')
                print(f"\n--- Direct Access Test ---")
                print(f"Successfully accessed owner ID: {owner_id}")
            else:
                print("\n'owners' list does not contain a dictionary as expected.")
        else:
            print("\n'owners' attribute is empty or not in the expected format.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
