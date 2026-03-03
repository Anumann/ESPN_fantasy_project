# cli_tool.py
import sqlite3
import pandas as pd
import argparse

DB_NAME = 'fantasy_data.db'

def run_query(query):
    """Connects to the database and runs a user-provided SQL query."""
    try:
        conn = sqlite3.connect(DB_NAME)
        # Use pandas to execute the query and return a nicely formatted DataFrame
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        return f"An error occurred: {e}"

def main():
    parser = argparse.ArgumentParser(description="""
    Command-line interface to query the fantasy football database.
    
    Examples:
    1. List all tables:
       python cli_tool.py -q "SELECT name FROM sqlite_master WHERE type='table';"

    2. Show all data for the 'teams' table for the 2025 season:
       python cli_tool.py -q "SELECT * FROM teams WHERE year = 2025;"

    3. Find a specific owner:
       python cli_tool.py -q "SELECT DISTINCT owner, owner_id FROM teams WHERE owner LIKE '%Hinojosa%';"
    """)
    parser.add_argument('-q', '--query', required=True, help="The SQL query to execute, enclosed in quotes.")
    
    args = parser.parse_args()
    
    result = run_query(args.query)
    
    print(f"Executing query: {args.query}")
    print("-" * 50)
    # Check if the result is a DataFrame before trying to print it
    if isinstance(result, pd.DataFrame):
        # Print the DataFrame without the index for cleaner output
        print(result.to_string(index=False))
    else:
        # Print the error message
        print(result)

if __name__ == '__main__':
    main()
