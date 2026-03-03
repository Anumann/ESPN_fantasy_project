# new_analyzer.py
import sqlite3
import pandas as pd

DB_NAME = 'fantasy_data.db'

def get_dataframes():
    """Fetches data from the database and loads it into pandas DataFrames."""
    conn = sqlite3.connect(DB_NAME)
    
    teams_df = pd.read_sql_query("SELECT * FROM teams WHERE owner_id != 'UNKNOWN_ID'", conn)
    matchups_df = pd.read_sql_query("SELECT * FROM matchups", conn)
    
    conn.close()
    
    return teams_df, matchups_df

def analyze_records(teams_df, matchups_df, is_playoff):
    """Analyzes records for either regular season or playoffs."""
    
    # Filter for the correct game type
    games = matchups_df[matchups_df['is_playoff'] == (1 if is_playoff else 0)]
    
    # Create records for home and away teams
    home_games = games[['year', 'home_team_id', 'home_score', 'away_score']].rename(columns={'home_team_id': 'team_id', 'home_score': 'score', 'away_score': 'opponent_score'})
    away_games = games[['year', 'away_team_id', 'away_score', 'home_score']].rename(columns={'away_team_id': 'team_id', 'away_score': 'score', 'home_score': 'opponent_score'})
    
    all_games = pd.concat([home_games, away_games])
    
    # Determine win, loss, tie
    all_games['win'] = (all_games['score'] > all_games['opponent_score']).astype(int)
    all_games['loss'] = (all_games['score'] < all_games['opponent_score']).astype(int)
    all_games['tie'] = (all_games['score'] == all_games['opponent_score']).astype(int)
    
    # Merge with team data to get owner info
    full_data = pd.merge(all_games, teams_df, on=['team_id', 'year'])
    
    # Group by owner to get career records
    records = full_data.groupby('owner_id').agg(
        wins=('win', 'sum'),
        losses=('loss', 'sum'),
        ties=('tie', 'sum'),
        display_name=('owner', 'last') # Get their most recent name
    ).reset_index()
    
    records['win_pct'] = records['wins'] / (records['wins'] + records['losses'])
    records = records.sort_values(by=['win_pct', 'wins'], ascending=[False, False])
    
    return records

def main():
    teams_df, matchups_df = get_dataframes()
    
    # --- Playoff Analysis ---
    playoff_records = analyze_records(teams_df, matchups_df, is_playoff=True)
    all_owners = teams_df[['owner_id', 'owner']].drop_duplicates(subset='owner_id')
    
    # Merge to include owners who never made playoffs
    playoff_records = pd.merge(all_owners, playoff_records, on='owner_id', how='left').fillna(0)
    playoff_records = playoff_records.sort_values(by=['win_pct', 'wins'], ascending=[False, False])
    playoff_records.rename(columns={'owner': 'display_name_x', 'display_name': 'display_name_y'}, inplace=True)
    playoff_records['display_name'] = playoff_records['display_name_y'].where(playoff_records['display_name_y'] != 0, playoff_records['display_name_x'])


    print("--- Corrected Career Playoff Records (All-Time) ---")
    print("-" * 70)
    print(f"{'Rank':<5} {'Owner':<25} {'Record (W-L-T)':<18} {'Win %':<10}")
    print("-" * 70)
    
    for i, row in playoff_records.iterrows():
        rank = i + 1
        owner = row['display_name']
        record_str = f"{int(row['wins'])}-{int(row['losses'])}-{int(row['ties'])}"
        win_pct_str = f"{row['win_pct']:.3f}"
        print(f" {rank:<4} {owner:<25} {record_str:<18} {win_pct_str:<10}")
            
    print("-" * 70)




if __name__ == '__main__':
    main()
