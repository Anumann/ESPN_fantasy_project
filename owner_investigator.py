# owner_investigator.py
import sqlite3
import pandas as pd

DB_NAME = 'fantasy_data.db'

def main():
    """
    Investigates all unique owners in the database and lists all names and years
    associated with each unique owner ID.
    """
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT owner_id, owner, year FROM teams"
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Fill missing owner_ids with a placeholder for grouping purposes
    df['owner_id'] = df['owner_id'].fillna('MISSING_ID_' + df['owner'])
    
    # Group by the unique owner ID
    grouped = df.groupby('owner_id')
    
    print("--- Owner Investigation Report ---")
    print("This report lists every unique owner ID and the names/years associated with it.\n")

    for owner_id, group in grouped:
        unique_names = group['owner'].unique()
        years = sorted(group['year'].unique())
        
        print(f"Owner ID: {owner_id}")
        print(f"  Associated Names: {', '.join(unique_names)}")
        print(f"  Active Years: {', '.join(map(str, years))}")
        print("-" * 40)

if __name__ == '__main__':
    main()
