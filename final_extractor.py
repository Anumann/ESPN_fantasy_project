# final_extractor.py
import sqlite3
import time
import config
from espn_api.football import League

DB_NAME = 'fantasy_data.db'

def fetch_and_store_season_data(year):
    """
    A single, robust function to fetch all data for a given year.
    """
    print(f"--- Processing year: {year} ---")
    
    try:
        league = League(league_id=config.LEAGUE_ID, year=year, espn_s2=config.ESPN_S2, swid=config.SWID)
        print(f"Successfully connected to league for {year}.")
    except Exception as e:
        print(f"Could not connect to league for year {year}. Error: {e}")
        return False

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # == Step 1: Wipe existing data for this year to ensure a clean slate ==
    cursor.execute('DELETE FROM teams WHERE year = ?', (year,))
    cursor.execute('DELETE FROM matchups WHERE year = ?', (year,))
    cursor.execute('DELETE FROM seasons WHERE year = ?', (year,))
    print(f"Cleared existing data for {year}.")

    # == Step 2: Insert Season Data ==
    league_name = league.settings.name
    num_teams = len(league.teams)
    cursor.execute('INSERT OR IGNORE INTO seasons (year, league_name, num_teams) VALUES (?, ?, ?)', (year, league_name, num_teams))
    print(f"Stored season info for {year}: {league_name}")

    # == Step 3: Insert Team Data ==
    teams_to_insert = []
    for team in league.teams:
        owner_name = " ".join([owner['firstName'], owner['lastName']]) if (owner := team.owners[0] if team.owners else None) else 'Unknown'
        owner_id = (owner := team.owners[0] if team.owners else None) and owner.get('id') or 'UNKNOWN_ID'
        teams_to_insert.append((team.team_id, year, team.team_name, owner_name, owner_id))
    cursor.executemany('INSERT INTO teams (team_id, year, team_name, owner, owner_id) VALUES (?, ?, ?, ?, ?)', teams_to_insert)
    print(f"Stored {len(teams_to_insert)} teams.")

    # == Step 4: Insert Matchup Data ==
    matchups_to_insert = []
    # Loop through every week to get all games. A season won't have more than 18 weeks.
    for week in range(1, 18):
        try:
            weekly_scoreboard = league.scoreboard(week=week)
            if not weekly_scoreboard:
                break
            for match in weekly_scoreboard:
                if match.away_team: # Skip bye weeks
                    matchups_to_insert.append((year, week, match.home_team.team_id, match.home_score, match.away_team.team_id, match.away_score, match.is_playoff, match.matchup_type))
        except Exception:
            break
    
    cursor.executemany('INSERT INTO matchups (year, week, home_team_id, home_score, away_team_id, away_score, is_playoff, matchup_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', matchups_to_insert)
    print(f"Stored {len(matchups_to_insert)} matchups.")

    conn.commit()
    conn.close()
    print(f"--- Successfully processed year: {year} ---\n")
    return True

if __name__ == '__main__':
    YEAR_TO_FIX = 2024
    fetch_and_store_season_data(YEAR_TO_FIX)
