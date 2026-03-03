# dump_playoff_data.py
import sqlite3
import pandas as pd

DB_NAME = 'fantasy_data.db'

def main():
    """
    Connects to the database and dumps the raw, joined data for all playoff games.
    This provides the source data for manual analysis and verification.
    """
    conn = sqlite3.connect(DB_NAME)
    
    query = """
    SELECT
        m.year,
        m.week,
        t_home.owner AS home_owner,
        t_home.team_name AS home_team,
        m.home_score,
        t_away.owner AS away_owner,
        t_away.team_name AS away_team,
        m.away_score
    FROM matchups m
    JOIN teams t_home ON m.home_team_id = t_home.team_id AND m.year = t_home.year
    JOIN teams t_away ON m.away_team_id = t_away.team_id AND m.year = t_away.year
    WHERE m.is_playoff = 1
    ORDER BY m.year, m.week;
    """
    
    try:
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            print("Query returned no playoff games. Please verify the data in the 'matchups' and 'teams' tables.")
        else:
            print("--- Raw Playoff Game Data (All-Time) ---")
            print(df.to_string())

    except Exception as e:
        print(f"An error occurred during the query: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    main()
