# data_extractor.py
import sqlite3
import config
from espn_api.football import League

DB_NAME = 'fantasy_data.db'

def fetch_and_store_data(year):
    """Fetches league data for a given year and stores it in the SQLite database."""
    print(f"Fetching data for the {year} season...")
    
    try:
        league = League(
            league_id=config.LEAGUE_ID,
            year=year,
            espn_s2=config.ESPN_S2,
            swid=config.SWID
        )
        print(f"Data extraction for {year} complete.")
        return True
    except Exception as e:
        print(f"Could not connect to league for year {year}. It might not exist. Error: {e}")
        return False

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # --- 1. Insert Season Data ---
    league_name = league.settings.name
    num_teams = len(league.teams)
    cursor.execute('''
        INSERT OR IGNORE INTO seasons (year, league_name, num_teams)
        VALUES (?, ?, ?)
    ''', (year, league_name, num_teams))
    print(f"Stored season info for {year}: {league_name}")

    # --- 2. Insert Team Data ---
    # Clear existing teams for the year before inserting new ones
    cursor.execute('DELETE FROM teams WHERE year = ?', (year,))
    
    teams_to_insert = []
    for team in league.teams:
        owner_name = " ".join([team.owners[0]['firstName'], team.owners[0]['lastName']]) if team.owners and team.owners[0] else 'Unknown'
        # The owner_id is a guid in the format {GUID}, accessed directly from the owner dict
        owner_id = team.owners[0]['id'] if team.owners and team.owners[0] and 'id' in team.owners[0] else 'UNKNOWN_ID'
        teams_to_insert.append((team.team_id, year, team.team_name, owner_name, owner_id))
    
    cursor.executemany('''
        INSERT OR IGNORE INTO teams (team_id, year, team_name, owner, owner_id)
        VALUES (?, ?, ?, ?, ?)
    ''', teams_to_insert)
    print(f"Stored {len(teams_to_insert)} teams for {year}.")

    # --- 3. Insert Matchup Data ---
    # Clear existing matchups for the year to prevent duplicates on re-run
    cursor.execute('DELETE FROM matchups WHERE year = ?', (year,))
    
    matchups_to_insert = []
    # Loop through each week of the season to ensure all data is fetched
    # Assuming a 17-week season (regular season + playoffs)
    for week in range(1, 18):
        try:
            weekly_scoreboard = league.scoreboard(week=week)
            if not weekly_scoreboard:
                # This can happen if a season has fewer than 17 weeks.
                print(f"No data for week {week}. Assuming season ended.")
                break
        except Exception:
            # Some historical seasons might have fewer than 17 weeks
            print(f"No data for week {week}. Season may have ended.")
            break
            
        for match in weekly_scoreboard:
            # Skip bye weeks where away_team is None
            if match.away_team:
                matchups_to_insert.append((
                    year,
                    week,
                    match.home_team.team_id,
                    match.home_score,
                    match.away_team.team_id,
                    match.away_score,
                    match.is_playoff
                ))

    cursor.executemany('''
        INSERT OR IGNORE INTO matchups (year, week, home_team_id, home_score, away_team_id, away_score, is_playoff)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', matchups_to_insert)
    print(f"Stored {len(matchups_to_insert)} matchups for {year}.")

    conn.commit()
    conn.close()
    print(f"Data extraction for {year} complete.")
    return True


if __name__ == '__main__':
    # We will run this for a single year to test and verify the fix.
    YEAR_TO_FIX = 2024
    fetch_and_store_data(YEAR_TO_FIX)
