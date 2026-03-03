# temp_run_postgres_setup.py
import psycopg2
import toml
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_db_credentials(secrets_file="temp_secrets.toml"):
    """Loads database credentials from a TOML file."""
    try:
        secrets = toml.load(secrets_file)
        return secrets.get("database", {})
    except FileNotFoundError:
        logging.error(f"Secrets file not found at {secrets_file}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error reading secrets file: {e}")
        sys.exit(1)

def create_tables(credentials):
    """Creates the database tables using PostgreSQL."""
    if not credentials:
        logging.error("Database credentials are not provided or are empty.")
        sys.exit(1)

    try:
        logging.info("Connecting to the PostgreSQL database...")
        conn = psycopg2.connect(**credentials)
        cursor = conn.cursor()
        logging.info("Connection successful.")

        # Seasons Table
        logging.info("Creating 'seasons' table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS seasons (
                year INTEGER PRIMARY KEY,
                league_name TEXT NOT NULL,
                num_teams INTEGER NOT NULL
            )
        ''')

        # Teams Table
        logging.info("Creating 'teams' table...")
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
        logging.info("Creating 'matchups' table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matchups (
                matchup_id SERIAL PRIMARY KEY,
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
        cursor.close()
        conn.close()
        logging.info("Tables created successfully and connection closed.")

    except psycopg2.OperationalError as e:
        logging.error(f"Database connection error: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == '__main__':
    creds = get_db_credentials()
    create_tables(creds)
