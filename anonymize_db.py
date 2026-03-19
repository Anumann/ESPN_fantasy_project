import sqlite3
import os

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

def anonymize_database():
    """
    Connects to the SQLite database and anonymizes all owner names in the 'teams' table.
    """
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_FILENAME)
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}. Exiting.")
        return

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Fetch all unique owner names
        cursor.execute("SELECT DISTINCT owner FROM teams")
        owners = cursor.fetchall()
        
        owner_map = {owner[0]: anonymize_name(owner[0]) for owner in owners}

        print("--- Anonymization Map ---")
        for original, anonymized in owner_map.items():
            print(f"'{original}' -> '{anonymized}'")

        # Update each owner name
        for original, anonymized in owner_map.items():
            cursor.execute("UPDATE teams SET owner = ? WHERE owner = ?", (anonymized, original))

        conn.commit()
        print(f"\nSuccessfully anonymized {len(owner_map)} unique owner names in '{DB_FILENAME}'.")

    except Exception as e:
        print(f"An error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    anonymize_database()
