import streamlit as st
import pandas as pd
import psycopg2
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Set page config
st.set_page_config(page_title="Fantasy Football Dashboard", layout="wide")

st.title("Fantasy Football Dashboard")

# Function to create a database connection
@st.cache_resource
def get_db_connection():
    """Establishes a connection to the PostgreSQL database using secrets."""
    try:
        conn = psycopg2.connect(**st.secrets["database"])
        logging.info("Database connection established successfully.")
        return conn
    except Exception as e:
        st.error(f"Error connecting to the database: {e}")
        logging.error(f"Database connection failed: {e}")
        return None

# Function to fetch data
def fetch_data(query, connection):
    """Fetches data from the database and returns it as a Pandas DataFrame."""
    if connection is None:
        return pd.DataFrame() # Return empty dataframe if no connection
    try:
        df = pd.read_sql(query, connection)
        logging.info(f"Successfully executed query: {query}")
        return df
    except Exception as e:
        st.error(f"Error executing query: {e}")
        logging.error(f"Query execution failed: {e}")
        return pd.DataFrame()

# Main application logic
def main():
    """Main function to run the Streamlit app."""
    conn = get_db_connection()

    if conn:
        st.subheader("Team Owners")
        
        # Query to select all teams and owners
        owners_query = "SELECT team_id, year, team_name, owner FROM teams ORDER BY owner;"
        
        # Fetch and display the data
        owners_df = fetch_data(owners_query, conn)
        
        if not owners_df.empty:
            st.dataframe(owners_df, use_container_width=True)
        else:
            st.warning("No team data found. The database may be empty. Please run the data extractor script.")
            
        # You can add more sections here for other data
        # For example:
        # st.subheader("Team Information")
        # teams_query = "SELECT * FROM teams;"
        # teams_df = fetch_data(teams_query, conn)
        # st.dataframe(teams_df, use_container_width=True)

if __name__ == "__main__":
    main()
