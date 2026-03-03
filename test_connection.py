# test_connection.py
import config
from espn_api.football import League

def main():
    """
    Connects to the ESPN Fantasy Football league and prints team names.
    """
    try:
        league = League(
            league_id=config.LEAGUE_ID,
            year=config.YEAR,
            espn_s2=config.ESPN_S2,
            swid=config.SWID
        )
        print("Successfully connected to the league.")
        print("Fetching teams...")
        print(f"League Name: {league.settings.name}")
        print("-" * 30)
        
        teams = league.teams
        if not teams:
            print("No teams found. Please check your league ID and year.")
            return

        for team in teams:
            print(f"Team ID: {team.team_id}, Name: {team.team_name}")
            
        print("-" * 30)
        print("Connection test successful.")

    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please verify your credentials in config.py and ensure the league is active for the specified year.")

if __name__ == "__main__":
    main()
