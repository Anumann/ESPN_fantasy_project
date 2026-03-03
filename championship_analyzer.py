# championship_analyzer.py
import sqlite3
import pandas as pd

DB_NAME = 'fantasy_data.db'

def get_championships(teams_df, matchups_df):
    """
    Determines the number of championships won by each owner.
    """
    playoffs = matchups_df[matchups_df['is_playoff'] == 1].copy()
    
    # Find the last week of the playoffs for each year
    championship_weeks = playoffs.groupby('year')['week'].max().reset_index()
    
    # Filter to get only the championship matchups
    championship_games = pd.merge(playoffs, championship_weeks, on=['year', 'week'])
    
    # Determine the winner
    championship_games['winner_id'] = championship_games.apply(
        lambda row: row['home_team_id'] if row['home_score'] > row['away_score'] else row['away_team_id'],
        axis=1
    )
    
    # Link winner_id back to owner_id
    championships = pd.merge(
        championship_games[['year', 'winner_id']],
        teams_df[['year', 'team_id', 'owner_id']],
        left_on=['year', 'winner_id'],
        right_on=['year', 'team_id']
    )
    
    # Count championships per owner
    championship_counts = championships.groupby('owner_id').size().reset_index(name='Championships')
    
    return championship_counts

def analyze_records(teams_df, matchups_df, is_playoff):
    """Analyzes records for either regular season or playoffs."""
    games = matchups_df[matchups_df['is_playoff'] == (1 if is_playoff else 0)]
    home = games[['year', 'home_team_id', 'home_score', 'away_score']].rename(columns={'home_team_id': 'team_id', 'home_score': 'score', 'away_score': 'opponent_score'})
    away = games[['year', 'away_team_id', 'away_score', 'home_score']].rename(columns={'away_team_id': 'team_id', 'away_score': 'score', 'home_score': 'opponent_score'})
    all_games = pd.concat([home, away])
    all_games['wins'] = (all_games['score'] > all_games['opponent_score']).astype(int)
    all_games['losses'] = (all_games['score'] < all_games['opponent_score']).astype(int)
    all_games['ties'] = (all_games['score'] == all_games['opponent_score']).astype(int)
    merged = pd.merge(all_games, teams_df, on=['team_id', 'year'])
    summary = merged.groupby('owner_id').agg(wins=('wins', 'sum'), losses=('losses', 'sum'), ties=('ties', 'sum'), display_name=('owner', 'last')).reset_index()
    return summary

def main():
    conn = sqlite3.connect(DB_NAME)
    teams_df = pd.read_sql_query("SELECT * FROM teams WHERE owner_id != 'UNKNOWN_ID'", conn)
    matchups_df = pd.read_sql_query("SELECT * FROM matchups", conn)
    conn.close()

    championship_counts = get_championships(teams_df, matchups_df)
    
    for is_playoff_report in [False, True]:
        report_type = "Playoff" if is_playoff_report else "Regular Season"
        records = analyze_records(teams_df, matchups_df, is_playoff=is_playoff_report)
        
        # Merge with all owners to include everyone
        all_owners = teams_df[['owner_id', 'owner']].drop_duplicates(subset='owner_id').rename(columns={'owner': 'latest_name'})
        final_records = pd.merge(all_owners, records, on='owner_id', how='left').fillna(0)
        final_records['display_name'] = final_records['display_name'].fillna(final_records['latest_name'])
        
        # Merge with championship counts
        final_records = pd.merge(final_records, championship_counts, on='owner_id', how='left').fillna(0)
        final_records['Championships'] = final_records['Championships'].astype(int)

        # Calculate win_pct and sort
        final_records['win_pct'] = final_records['wins'] / (final_records['wins'] + final_records['losses'])
        final_records = final_records.fillna(0.0).sort_values(by=['win_pct', 'wins'], ascending=[False, False]).reset_index(drop=True)

        # Display Results
        print(f"\n--- Definitive Career {report_type} Records (All-Time) ---")
        print("-" * 85)
        print(f"{'Rank':<5} {'Owner':<25} {'Record (W-L-T)':<18} {'Win %':<10} {'Championships':<15}")
        print("-" * 85)

        for i, row in final_records.iterrows():
            rank = i + 1
            owner = row['display_name']
            record_str = f"{int(row['wins'])}-{int(row['losses'])}-{int(row['ties'])}"
            win_pct_str = f"{row['win_pct']:.3f}"
            champs_str = row['Championships']
            print(f" {rank:<4} {owner:<25} {record_str:<18} {win_pct_str:<10} {champs_str:<15}")

        print("-" * 85)

if __name__ == '__main__':
    main()
