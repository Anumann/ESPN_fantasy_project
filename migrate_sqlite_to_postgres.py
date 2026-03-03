# migrate_sqlite_to_postgres.py
import sqlite3
import psycopg2
import toml
import logging
import sys
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_postgres_credentials(secrets_file="temp_secrets.toml"):
    """Loads PostgreSQL credentials from a TOML file."""
    try:
        secrets = toml.load(secrets_file)
        return secrets.get("database", {})
    except FileNotFoundError:
        logging.error(f"Secrets file not found at {secrets_file}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error reading secrets file: {e}")
        sys.exit(1)

def migrate_data(pg_creds, sqlite_db_path='fantasy_data.db'):
    """Migrates data from SQLite to PostgreSQL."""
    
    # --- 1. Connect to both databases ---
    try:
        logging.info(f"Connecting to SQLite database: {sqlite_db_path}")
        sqlite_conn = sqlite3.connect(sqlite_db_path)
        
        logging.info("Connecting to PostgreSQL database...")
        pg_conn = psycopg2.connect(**pg_creds)
        pg_cursor = pg_conn.cursor()
        logging.info("All database connections successful.")
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        sys.exit(1)

    # --- 2. Define tables to migrate ---
    tables_to_migrate = ['seasons', 'teams', 'matchups']
    
    # --- 3. Migrate each table ---
    try:
        for table_name in tables_to_migrate:
            logging.info(f"Reading data from SQLite table: '{table_name}'...")
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", sqlite_conn)
            
            if df.empty:
                logging.warning(f"Table '{table_name}' is empty. Nothing to migrate.")
                continue

            logging.info(f"Found {len(df)} rows to migrate for table '{table_name}'.")

            # Truncate the table in PostgreSQL to ensure a clean import
            logging.info(f"Clearing existing data from PostgreSQL table: '{table_name}'...")
            pg_cursor.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;")

            # Prepare data for insertion
            cols = ','.join(df.columns)
            placeholders = ','.join(['%s'] * len(df.columns))
            sql = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"
            
            # Execute insert
            logging.info(f"Inserting data into PostgreSQL table: '{table_name}'...")
            pg_cursor.executemany(sql, df.to_records(index=False).tolist())
            logging.info(f"Successfully migrated data for table '{table_name}'.")

        # --- 4. Commit and close connections ---
        pg_conn.commit()
        logging.info("Data migration committed successfully.")

    except Exception as e:
        pg_conn.rollback()
        logging.error(f"An error occurred during migration: {e}")
        sys.exit(1)
    finally:
        pg_cursor.close()
        pg_conn.close()
        sqlite_conn.close()
        logging.info("All database connections closed.")

if __name__ == '__main__':
    creds = get_postgres_credentials()
    migrate_data(creds)
