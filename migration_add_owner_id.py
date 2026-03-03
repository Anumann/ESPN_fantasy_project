# migration_add_owner_id.py
import sqlite3

DB_NAME = 'fantasy_data.db'

def add_owner_id_column():
    """Adds the owner_id column to the teams table to uniquely identify owners."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('ALTER TABLE teams ADD COLUMN owner_id TEXT')
        print("Column 'owner_id' added to 'teams' table successfully.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column 'owner_id' already exists in 'teams' table.")
        else:
            raise
    conn.commit()
    conn.close()

if __name__ == '__main__':
    add_owner_id_column()
