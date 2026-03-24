import sqlite3
import os

DB_PATH = 'fantasy_data.db'

def run_migration():
    print(f"Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Create players table
        print("Creating 'players' table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            player_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            default_position TEXT
        )
        ''')

        # Create draft_picks table
        print("Creating 'draft_picks' table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS draft_picks (
            pick_id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            team_id INTEGER NOT NULL,
            player_id INTEGER NOT NULL,
            round_num INTEGER,
            pick_num INTEGER,
            keeper_status BOOLEAN DEFAULT 0,
            FOREIGN KEY (year) REFERENCES seasons(year),
            FOREIGN KEY (team_id, year) REFERENCES teams(team_id, year),
            FOREIGN KEY (player_id) REFERENCES players(player_id)
        )
        ''')

        # Create weekly_rosters table
        print("Creating 'weekly_rosters' table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS weekly_rosters (
            roster_entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            week INTEGER NOT NULL,
            team_id INTEGER NOT NULL,
            player_id INTEGER NOT NULL,
            lineup_slot TEXT NOT NULL,
            projected_points REAL,
            actual_points REAL,
            FOREIGN KEY (year) REFERENCES seasons(year),
            FOREIGN KEY (team_id, year) REFERENCES teams(team_id, year),
            FOREIGN KEY (player_id) REFERENCES players(player_id)
        )
        ''')

        conn.commit()
        print("Migration successful! New tables added.")

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    run_migration()
