# migration_add_matchup_type.py
import sqlite3

DB_NAME = 'fantasy_data.db'

def add_matchup_type_column():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('ALTER TABLE matchups ADD COLUMN matchup_type TEXT')
        print("Column 'matchup_type' added to 'matchups' table successfully.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column 'matchup_type' already exists.")
        else:
            raise
    conn.commit()
    conn.close()

if __name__ == '__main__':
    add_matchup_type_column()
