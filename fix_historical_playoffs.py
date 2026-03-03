# fix_historical_playoffs.py
import sqlite3
import time
import config
from espn_api.football import League

DB_NAME = 'fantasy_data.db'

def fetch_and_store_historical_playoffs(year):
    """
    Fetches only playoff data for a given historical year and stores it.
    This uses a different league instantiation for historical data.
    """
    print(f"Fetching playoff data for the {year} season...")
    
    try:
        # For historical seasons, it's more reliable to use the 'leagueHistory' endpoint
        # which is what the API does when you pass a past year.
        league = League(
            league_id=config.LEAGUE_ID,
            year=year,
            espn_s2=config.ESPN_S2,
            swid=config.SWID
        )
        print("Successfully connected to the league.")
    except Exception as e:
        print(f"Could not connect to league for year {year}. Error: {e}")
        return False

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Clear any potentially incorrect playoff entries for this year first
    cursor.execute('DELETE FROM matchups WHERE year = ? AND is_playoff = 1', (year,))

    matchups_to_insert = []
    # For historical data, we need to find the playoff weeks
    # The 'playoff_week_start' attribute isn't always present in historical data,
    # so we'll use a common default of 14 if it's not found.
    playoff_start_week = getattr(league.settings, 'playoff_week_start', 14)
    season_end_week = getattr(league.settings, 'week_count', 17) # Default to 17 weeks if not found
    
    for week in range(playoff_start_week, season_end_week + 1):
        try:
            weekly_scoreboard = league.scoreboard(week=week)
            if not weekly_scoreboard:
                break
            for match in weekly_scoreboard:
                if match.away_team: # Skip bye weeks
                    # The is_playoff flag from the API should be reliable here
                    if match.is_playoff:
                        matchups_to_insert.append((
                            year,
                            week,
                            match.home_team.team_id,
                            match.home_score,
                            match.away_team.team_id,
                            match.away_score,
                            True
                        ))
        except Exception as e:
            print(f"Could not fetch scoreboard for week {week} in {year}. Error: {e}")
            continue

    if matchups_to_insert:
        cursor.executemany('''
            INSERT OR IGNORE INTO matchups (year, week, home_team_id, home_score, away_team_id, away_score, is_playoff)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', matchups_to_insert)
        print(f"Stored {len(matchups_to_insert)} playoff matchups for {year}.")
    else:
        print(f"No playoff matchups found for {year}.")

    conn.commit()
    conn.close()
    return True

def main():
    """Loops backwards from 2024 to backfill historical playoff data."""
    print("--- Starting Historical Playoff Data Backfill ---")
    # Loop through the years we know are missing playoff data
    for year in range(2024, 2015, -1):
        fetch_and_store_historical_playoffs(year)
        time.sleep(3) # Be respectful to the API
        
    print("--- Historical Playoff Data Backfill Complete ---")

if __name__ == '__main__':
    main()
