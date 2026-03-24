import sys
try:
    from espn_api.football import League
except ImportError:
    print("Error: Could not import 'espn_api'. Make sure you are in the virtual environment.")
    sys.exit(1)
import config

def test_api():
    year = 2023
    print(f"Connecting to ESPN Fantasy API for League {config.LEAGUE_ID}, Year {year}...")
    
    try:
        league = League(league_id=config.LEAGUE_ID, year=year, espn_s2=config.ESPN_S2, swid=config.SWID)
        
        print("\n✅ Success! Authentication is valid and data was fetched.")
        print("-" * 40)
        print(f"League Name: {league.settings.name}")
        print(f"Total Teams: {len(league.teams)}")
        print(f"Total Draft Picks Logged: {len(league.draft)}")
        
        if league.teams:
            sample_team = league.teams[0]
            print(f"\nSample Team: {sample_team.team_name} (Manager: {sample_team.owners[0].get('firstName', 'Unknown')})")
            
            roster = sample_team.roster
            print(f"Current Roster Size: {len(roster)}")
            if roster:
                print(f"Sample Player: {roster[0].name} ({roster[0].position})")
                
        print("-" * 40)
        print("Ready for Phase 3 ingestion!")
        
    except Exception as e:
        print(f"\n❌ Connection or Fetch Error: {e}")
        print("Check if the SWID/ESPN_S2 cookies have expired.")

if __name__ == "__main__":
    test_api()
