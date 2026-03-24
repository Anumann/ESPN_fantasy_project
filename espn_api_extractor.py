import os
import sqlite3
import config
from espn_api.football import League

DB_PATH = 'fantasy_data.db'

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def extract_year(year):
    print(f"==================================================")
    print(f"Extracting ESPN Data for Year {year}")
    print(f"==================================================")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        league = League(league_id=config.LEAGUE_ID, year=year, espn_s2=config.ESPN_S2, swid=config.SWID)
    except Exception as e:
        print(f"❌ Failed to connect to ESPN API for {year}. Error: {e}")
        return

    # --- 1. DRAFT PICKS ---
    if hasattr(league, 'draft') and league.draft:
        print(f"📝 Found {len(league.draft)} draft picks. Ingesting...")
        
        # Clear existing draft data for this year to prevent duplicates
        cursor.execute("DELETE FROM draft_picks WHERE year = ?", (year,))
        
        draft_inserts = []
        for pick in league.draft:
            # Upsert Player
            cursor.execute('''
                INSERT OR IGNORE INTO players (player_id, name, default_position)
                VALUES (?, ?, ?)
            ''', (pick.playerId, pick.playerName, 'UNKNOWN')) # Basic info, updated later
            
            draft_inserts.append((
                year, 
                pick.team.team_id, 
                pick.playerId, 
                pick.round_num, 
                pick.round_pick, 
                pick.keeper_status
            ))
            
        cursor.executemany('''
            INSERT INTO draft_picks (year, team_id, player_id, round_num, pick_num, keeper_status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', draft_inserts)
        print("✅ Draft picks ingested successfully.")
    else:
        print("⚠️ No draft data found for this year.")

    # --- 2. WEEKLY ROSTERS (BOX SCORES) ---
    max_week = league.current_week
    print(f"📅 Ingesting box scores up to Week {max_week}...")
    
    # Clear existing weekly rosters for this year to prevent duplicates
    cursor.execute("DELETE FROM weekly_rosters WHERE year = ?", (year,))
    
    roster_inserts = []
    
    for week in range(1, max_week + 1):
        try:
            box_scores = league.box_scores(week)
        except Exception as e:
            print(f"⚠️ Could not fetch box scores for Week {week}: {e}")
            continue
            
        for matchup in box_scores:
            # Process Home Team Lineup
            if matchup.home_team:
                for player in matchup.home_lineup:
                    # Upsert Player to ensure they exist (and update position)
                    cursor.execute('''
                        INSERT OR IGNORE INTO players (player_id, name, default_position)
                        VALUES (?, ?, ?)
                    ''', (player.playerId, player.name, player.position))
                    
                    # Also update default_position if it was UNKNOWN from the draft
                    cursor.execute('''
                        UPDATE players SET default_position = ? 
                        WHERE player_id = ? AND default_position = 'UNKNOWN'
                    ''', (player.position, player.playerId))
                    
                    roster_inserts.append((
                        year,
                        week,
                        matchup.home_team.team_id,
                        player.playerId,
                        player.slot_position,
                        player.projected_points,
                        player.points
                    ))
            
            # Process Away Team Lineup (if it exists)
            if matchup.away_team:
                for player in matchup.away_lineup:
                    cursor.execute('''
                        INSERT OR IGNORE INTO players (player_id, name, default_position)
                        VALUES (?, ?, ?)
                    ''', (player.playerId, player.name, player.position))
                    
                    cursor.execute('''
                        UPDATE players SET default_position = ? 
                        WHERE player_id = ? AND default_position = 'UNKNOWN'
                    ''', (player.position, player.playerId))
                    
                    roster_inserts.append((
                        year,
                        week,
                        matchup.away_team.team_id,
                        player.playerId,
                        player.slot_position,
                        player.projected_points,
                        player.points
                    ))
                    
    if roster_inserts:
        cursor.executemany('''
            INSERT INTO weekly_rosters (year, week, team_id, player_id, lineup_slot, projected_points, actual_points)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', roster_inserts)
        print(f"✅ Ingested {len(roster_inserts)} individual weekly player performances.")
    
    conn.commit()
    conn.close()
    print("✅ Year processing complete.\n")

if __name__ == "__main__":
    # Loop through all historical years
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT year FROM seasons ORDER BY year")
    years = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    for year in years:
        extract_year(year)
