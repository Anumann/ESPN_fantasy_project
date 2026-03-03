# database_setup.py
import sqlite3

DB_NAME = 'fantasy_data.db'

def create_tables():
    """Creates the database tables if they don't already exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Seasons Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seasons (
            year INTEGER PRIMARY KEY,
            league_name TEXT NOT NULL,
            num_teams INTEGER NOT NULL
        )
    ''')

    # Teams Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            team_id INTEGER NOT NULL,
            year INTEGER NOT NULL,
            team_name TEXT NOT NULL,
            owner TEXT NOT NULL,
            PRIMARY KEY (team_id, year),
            FOREIGN KEY (year) REFERENCES seasons (year)
        )
    ''')

    # Matchups Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matchups (
            matchup_id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            week INTEGER NOT NULL,
            home_team_id INTEGER NOT NULL,
            home_score REAL NOT NULL,
            away_team_id INTEGER,
            away_score REAL,
            is_playoff BOOLEAN NOT NULL,
            UNIQUE (year, week, home_team_id, away_team_id),
            FOREIGN KEY (year) REFERENCES seasons (year)
        )
    ''')

    conn.commit()
    conn.close()
    print(f"Database '{DB_NAME}' and tables created successfully.")

if __name__ == '__main__':
    create_tables()
