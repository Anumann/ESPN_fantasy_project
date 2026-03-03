# data_extractor.py
import os
import psycopg2
import config
from espn_api.football import League

# The DATABASE_URL will be provided by Render's environment for the cron job.
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("WARNING: DATABASE_URL not found for data_extractor. This script is intended for production.")

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        if DATABASE_URL:
            return psycopg2.connect(DATABASE_URL)
        else:
            # This script is not intended for local SQLite use, so we don't provide a fallback.
            return None
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def fetch_and_store_data(year):
    """Fetches league data for a given year and stores it in the PostgreSQL database."""
    print(f"Fetching data for the {year} season...")
    
    try:
        league = League(
            league_id=config.LEAGUE_ID,
            year=year,
            espn_s2=config.ESPN_S2,
            swid=config.SWID
        )
    except Exception as e:
        print(f"Could not connect to league for year {year}. It might not exist. Error: {e}")
        return False
    
    conn = get_db_connection()
    if not conn:
        print("Could not establish database connection. Aborting.")
        return False

    cursor = conn.cursor()
    print(f"Connected to database. Storing data for {year}...")

    # --- 1. Insert Season Data ---
    league_name = league.settings.name
    num_teams = len(league.teams)
    # Use PostgreSQL's ON CONFLICT clause to handle existing entries
    cursor.execute('''
        INSERT INTO seasons (year, league_name, num_teams)
        VALUES (%s, %s, %s)
        ON CONFLICT (year) DO NOTHING;
    ''', (year, league_name, num_teams))
    print(f"Stored season info for {year}: {league_name}")

    # --- 2. Insert Team Data ---
    # In PostgreSQL, it's often safer to insert and then update, or use ON CONFLICT.
    # We will use ON CONFLICT to update team_name and owner if the record exists.
    teams_to_insert = []
    for team in league.teams:
        owner_name = " ".join([team.owners[0]['firstName'], team.owners[0]['lastName']]) if team.owners and team.owners[0] else 'Unknown'
        owner_id = team.owners[0]['id'] if team.owners and team.owners[0] and 'id' in team.owners[0] else 'UNKNOWN_ID'
        teams_to_insert.append((team.team_id, year, team.team_name, owner_name, owner_id))
    
    # This command inserts a new team or updates the name/owner if the (team_id, year) composite key already exists.
    cursor.executemany('''
        INSERT INTO teams (team_id, year, team_name, owner, owner_id)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (team_id, year) DO UPDATE 
        SET team_name = EXCLUDED.team_name, owner = EXCLUDED.owner, owner_id = EXCLUDED.owner_id;
    ''', teams_to_insert)
    print(f"Stored {len(teams_to_insert)} teams for {year}.")

    # --- 3. Insert Matchup Data ---
    # Clear existing matchups for the year to prevent issues with partial data on re-runs.
    cursor.execute('DELETE FROM matchups WHERE year = %s', (year,))
    
    matchups_to_insert = []
    for week in range(1, 18):
        try:
            weekly_scoreboard = league.scoreboard(week=week)
            if not weekly_scoreboard:
                print(f"No data for week {week}. Assuming season ended.")
                break
        except Exception:
            print(f"No data for week {week}. Season may have ended.")
            break
            
        for match in weekly_scoreboard:
            if match.away_team:
                matchups_to_insert.append((
                    year, week,
                    match.home_team.team_id, match.home_score,
                    match.away_team.team_id, match.away_score,
                    match.is_playoff
                ))

    if matchups_to_insert:
        cursor.executemany('''
            INSERT INTO matchups (year, week, home_team_id, home_score, away_team_id, away_score, is_playoff)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', matchups_to_insert)
        print(f"Stored {len(matchups_to_insert)} matchups for {year}.")

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Data extraction and storage for {year} complete.")
    return True

if __name__ == '__main__':
    # This script is intended to be run for a specific year, often via a cron job.
    # For testing, we can manually set a year.
    YEAR_TO_RUN = 2025 # Example year
    fetch_and_store_data(YEAR_TO_RUN)
