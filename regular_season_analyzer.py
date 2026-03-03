# regular_season_analyzer.py
import sqlite3
import pandas as pd

DB_NAME = 'fantasy_data.db'

def main():
    """
    Connects to the database, performs a correct and robust analysis using pandas,
    and prints the definitive career regular season records.
    """
    conn = sqlite3.connect(DB_NAME)
    
    teams_df = pd.read_sql_query("SELECT * FROM teams WHERE owner_id != 'UNKNOWN_ID'", conn)
    matchups_df = pd.read_sql_query("SELECT * FROM matchups", conn)
    
    conn.close()

    # --- Analysis Logic ---
    # 1. Isolate only regular season games
    regular_games = matchups_df[matchups_df['is_playoff'] == 0].copy()

    # 2. De-normalize the data
    home_teams = regular_games[['year', 'home_team_id', 'home_score', 'away_score']].rename(columns={'home_team_id': 'team_id', 'home_score': 'score', 'away_score': 'opponent_score'})
    away_teams = regular_games[['year', 'away_team_id', 'away_score', 'home_score']].rename(columns={'away_team_id': 'team_id', 'away_score': 'score', 'home_score': 'opponent_score'})
    all_appearances = pd.concat([home_teams, away_teams], ignore_index=True)

    # 3. Determine outcome
    all_appearances['wins'] = (all_appearances['score'] > all_appearances['opponent_score']).astype(int)
    all_appearances['losses'] = (all_appearances['score'] < all_appearances['opponent_score']).astype(int)
    all_appearances['ties'] = (all_appearances['score'] == all_appearances['opponent_score']).astype(int)

    # 4. Merge with team data
    merged_data = pd.merge(all_appearances, teams_df, on=['team_id', 'year'])

    # 5. Group by owner_id and aggregate
    summary = merged_data.groupby('owner_id').agg(
        wins=('wins', 'sum'),
        losses=('losses', 'sum'),
        ties=('ties', 'sum'),
        display_name=('owner', 'last')
    ).reset_index()

    # 6. Get all owners to include those with no games (e.g., joined but never played)
    all_owners = teams_df[['owner_id', 'owner']].drop_duplicates(subset='owner_id')
    all_owners = all_owners.rename(columns={'owner': 'latest_name'})
    final_records = pd.merge(all_owners, summary, on='owner_id', how='left').fillna(0)
    final_records['display_name'] = final_records['display_name'].fillna(final_records['latest_name'])

    # 7. Calculate win_pct and sort
    final_records['win_pct'] = final_records['wins'] / (final_records['wins'] + final_records['losses'])
    final_records['win_pct'] = final_records['win_pct'].fillna(0.0)
    final_records = final_records.sort_values(by='win_pct', ascending=False).reset_index(drop=True)

    # --- Display Results ---
    print("--- Definitive Career Regular Season Records (All-Time) ---")
    print("-" * 70)
    print(f"{'Rank':<5} {'Owner':<25} {'Record (W-L-T)':<18} {'Win %':<10}")
    print("-" * 70)

    for i, row in final_records.iterrows():
        rank = i + 1
        owner = row['display_name']
        record_str = f"{int(row['wins'])}-{int(row['losses'])}-{int(row['ties'])}"
        win_pct_str = f"{row['win_pct']:.3f}"
        print(f" {rank:<4} {owner:<25} {record_str:<18} {win_pct_str:<10}")

    print("-" * 70)

if __name__ == '__main__':
    main()
