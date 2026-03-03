# final_analyzer.py
import sqlite3
import pandas as pd

DB_NAME = 'fantasy_data.db'

def main():
    """
    Connects to the database, performs a correct and robust analysis using pandas,
    and prints the definitive career playoff records.
    """
    conn = sqlite3.connect(DB_NAME)
    
    # Load all necessary data into pandas DataFrames
    teams_df = pd.read_sql_query("SELECT * FROM teams WHERE owner_id != 'UNKNOWN_ID'", conn)
    matchups_df = pd.read_sql_query("SELECT * FROM matchups", conn)
    
    conn.close()

    # 1. Isolate only playoff games
    playoff_games = matchups_df[matchups_df['is_playoff'] == 1].copy()

    # 2. De-normalize the data: create one row per team per game
    home_teams = playoff_games[['year', 'home_team_id', 'home_score', 'away_score']]
    home_teams = home_teams.rename(columns={'home_team_id': 'team_id', 'home_score': 'score', 'away_score': 'opponent_score'})

    away_teams = playoff_games[['year', 'away_team_id', 'away_score', 'home_score']]
    away_teams = away_teams.rename(columns={'away_team_id': 'team_id', 'away_score': 'score', 'home_score': 'opponent_score'})

    # Combine into a single DataFrame of all playoff appearances
    all_playoff_appearances = pd.concat([home_teams, away_teams], ignore_index=True)

    # 3. Determine outcome for each game
    all_playoff_appearances['wins'] = (all_playoff_appearances['score'] > all_playoff_appearances['opponent_score']).astype(int)
    all_playoff_appearances['losses'] = (all_playoff_appearances['score'] < all_playoff_appearances['opponent_score']).astype(int)
    all_playoff_appearances['ties'] = (all_playoff_appearances['score'] == all_playoff_appearances['opponent_score']).astype(int)

    # 4. Merge with team data to get owner information
    # This links each playoff game to the team and owner for that specific year
    merged_data = pd.merge(all_playoff_appearances, teams_df, on=['team_id', 'year'])

    # 5. Group by the permanent owner_id and aggregate the results
    playoff_summary = merged_data.groupby('owner_id').agg(
        wins=('wins', 'sum'),
        losses=('losses', 'sum'),
        ties=('ties', 'sum'),
        # Get the owner's most recent display name
        display_name=('owner', 'last')
    ).reset_index()

    # 6. Get a unique list of ALL owners from the league's history
    all_owners = teams_df[['owner_id', 'owner']].drop_duplicates(subset='owner_id')
    all_owners = all_owners.rename(columns={'owner': 'latest_name'})

    # 7. Merge the summary with the list of all owners to include those with zero playoff games
    final_records = pd.merge(all_owners, playoff_summary, on='owner_id', how='left')
    # Replace NaN for those with no playoff games with 0
    final_records[['wins', 'losses', 'ties']] = final_records[['wins', 'losses', 'ties']].fillna(0)
    # Use the latest known name if a display name wasn't picked up in the summary
    final_records['display_name'] = final_records['display_name'].fillna(final_records['latest_name'])

    # 8. Calculate winning percentage, handling division by zero
    final_records['win_pct'] = final_records['wins'] / (final_records['wins'] + final_records['losses'])
    final_records['win_pct'] = final_records['win_pct'].fillna(0.0)

    # 9. Sort for ranking
    final_records = final_records.sort_values(by=['win_pct', 'wins'], ascending=[False, False]).reset_index(drop=True)

    # --- Display Results ---
    print("--- Definitive Career Playoff Records (All-Time) ---")
    print("--- Note: Owners not listed have a 0-0-0 playoff record. ---")
    print("-" * 70)
    print(f"{'Rank':<5} {'Owner':<25} {'Record (W-L-T)':<18} {'Win %':<10}")
    print("-" * 70)

    # Filter out owners with 0 wins and 0 losses to clean up the display
    playoff_participants = final_records[(final_records['wins'] > 0) | (final_records['losses'] > 0)]

    for i, row in playoff_participants.iterrows():
        rank = i + 1
        owner = row['display_name']
        record_str = f"{int(row['wins'])}-{int(row['losses'])}-{int(row['ties'])}"
        win_pct_str = f"{row['win_pct']:.3f}"
        print(f" {rank:<4} {owner:<25} {record_str:<18} {win_pct_str:<10}")

    print("-" * 70)


if __name__ == '__main__':
    main()
