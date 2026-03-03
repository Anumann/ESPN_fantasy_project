import sqlite3

try:
    conn = sqlite3.connect('espn-fantasy-project/fantasy_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", tables)
    
    for table in tables:
        print(f"\nSchema for {table[0]}:")
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        for col in columns:
            print(col)
            
    conn.close()
except Exception as e:
    print(f"Error: {e}")
