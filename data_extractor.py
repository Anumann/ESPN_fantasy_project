# data_extractor.py
import os
import sqlite3
import json
import config
from espn_api.football import League

DB_FILENAME = 'fantasy_data.db'

def anonymize_name(name):
    """Capitalizes and formats a full name to omit the last name, with an exception for 'Alex'."""
    if not isinstance(name, str):
        return str(name)
    parts = name.title().split()
    if parts[0] == 'Alex' and len(parts) > 1:
        return f"Alex {parts[-1][0]}."
    if len(parts) > 1:
        return ' '.join(parts[:-1])
    return name.title()

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_FILENAME)
        return sqlite3.connect(db_path)
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def get_owner_map():
    """Loads the owner name mapping from the JSON file."""
    try:
        map_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'owner_map.json')
        with open(map_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {} # Return an empty map if the file doesn't exist

def fetch_and_store_data(year):
    """Fetches league data, applies name merging and anonymization, and stores it in the SQLite database."""
    print(f"Fetching data for the {year} season...")
    
    try:
        league = League(league_id=config.LEAGUE_ID, year=year, espn_s2=config.ESPN_S2, swid=config.SWID)
    except Exception as e:
        print(f"Could not connect to league for year {year}. Error: {e}")
        return False
    
    conn = get_db_connection()
    if not conn:
        print("Could not establish database connection. Aborting.")
        return False

    cursor = conn.cursor()
    print(f"Connected to database. Storing data for {year}...")
    
    owner_map = get_owner_map()

    # --- 1. Insert Season Data ---
    cursor.execute('''
        INSERT OR IGNORE INTO seasons (year, league_name, num_teams)
        VALUES (?, ?, ?);
    ''', (year, league.settings.name, len(league.teams)))
    print(f"Stored season info for {year}: {league.settings.name}")

    # --- 2. Insert Team Data ---
    teams_to_insert = []
    for team in league.teams:
        owner_name = " ".join([team.owners[0]['firstName'], team.owners[0]['lastName']]) if team.owners and team.owners[0] else 'Unknown'
        
        # Apply name merging and anonymization
        owner_name = owner_map.get(owner_name, owner_name) # Merge names first
        anonymized_owner = anonymize_name(owner_name) # Then anonymize
        
        owner_id = team.owners[0]['id'] if team.owners and team.owners[0] and 'id' in team.owners[0] else 'UNKNOWN_ID'
        teams_to_insert.append((team.team_id, year, team.team_name, anonymized_owner, owner_id))
    
    cursor.executemany('''
        INSERT INTO teams (team_id, year, team_name, owner, owner_id)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT (team_id, year) DO UPDATE 
        SET team_name = excluded.team_name, owner = excluded.owner, owner_id = excluded.owner_id;
    ''', teams_to_insert)
    print(f"Stored {len(teams_to_insert)} teams for {year} with anonymized owners.")

    # --- 3. Insert Matchup Data ---
    cursor.execute('DELETE FROM matchups WHERE year = ?', (year,))
    
    matchups_to_insert = []
    for week in range(1, 18):
        try:
            weekly_scoreboard = league.scoreboard(week=week)
            if not weekly_scoreboard: break
        except Exception: break
            
        for match in weekly_scoreboard:
            if match.away_team:
                matchups_to_insert.append((
                    year, week,
                    match.home_team.team_id, match.home_score,
                    match.away_team.team_id, match.away_score,
                    1 if match.is_playoff else 0,
                    match.matchup_type if match.is_playoff else 'REGULAR_SEASON'
                ))

    if matchups_to_insert:
        cursor.executemany('''
            INSERT INTO matchups (year, week, home_team_id, home_score, away_team_id, away_score, is_playoff, matchup_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', matchups_to_insert)
        print(f"Stored {len(matchups_to_insert)} matchups for {year}.")

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Data extraction and storage for {year} complete.")
    return True
