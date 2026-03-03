# verify_data_completeness.py
import sqlite3
import pandas as pd

DB_NAME = 'fantasy_data.db'

def main():
    """
    Connects to the database and runs counts for regular season and playoff games
    for every year to verify data completeness.
    """
    conn = sqlite3.connect(DB_NAME)
    
    query = """
    SELECT
        year,
        SUM(CASE WHEN is_playoff = 0 THEN 1 ELSE 0 END) as regular_season_games,
        SUM(CASE WHEN is_playoff = 1 THEN 1 ELSE 0 END) as playoff_games
    FROM matchups
    GROUP BY year
    ORDER BY year DESC;
    """
    
    try:
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            print("The 'matchups' table is empty.")
        else:
            print("--- Data Completeness Report ---")
            # Fill NaN with 0 for years that might have one type of game but not the other
            df = df.fillna(0)
            df['regular_season_games'] = df['regular_season_games'].astype(int)
            df['playoff_games'] = df['playoff_games'].astype(int)
            print(df.to_string(index=False))

    except Exception as e:
        print(f"An error occurred during the query: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    main()
