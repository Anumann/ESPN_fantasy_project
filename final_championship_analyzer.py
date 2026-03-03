# final_championship_analyzer.py
import sqlite3
import pandas as pd

DB_NAME = 'fantasy_data.db'

def get_championships(teams_df, matchups_df):
    """
    Correctly determines championships based on two-week playoff matchups.
    """
    playoffs = matchups_df[(matchups_df['is_playoff'] == 1) & (matchups_df['matchup_type'] == 'WINNERS_BRACKET')].copy()
    
    champions = []
    for year in playoffs['year'].unique():
        yearly_playoffs = playoffs[playoffs['year'] == year]
        
        # Find the final two weeks of the playoffs for that year
        playoff_weeks = sorted(yearly_playoffs['week'].unique())
        if len(playoff_weeks) < 2:
            continue # Not enough data for a two-week final
        
        championship_weeks = playoff_weeks[-2:]
        
        # Isolate the final matchup (should be one game across two weeks)
        final_matchups = yearly_playoffs[yearly_playoffs['week'].isin(championship_weeks)]
        
        # Aggregate scores across the two weeks for each team
        home_scores = final_matchups.groupby('home_team_id')['home_score'].sum()
        away_scores = final_matchups.groupby('away_team_id')['away_score'].sum()
        
        total_scores = pd.concat([home_scores, away_scores], axis=1).sum(axis=1).reset_index()
        total_scores.columns = ['team_id', 'total_score']
        
        if total_scores.empty:
            continue

        # Find the team with the highest total score
        championship_winner_id = total_scores.loc[total_scores['total_score'].idxmax()]['team_id']
        
        champions.append({'year': year, 'team_id': championship_winner_id})

    if not champions:
        return pd.DataFrame(columns=['owner_id', 'Championships'])
        
    champions_df = pd.DataFrame(champions)
    
    # Link team_id back to owner_id for that year
    champs_with_owners = pd.merge(champions_df, teams_df[['year', 'team_id', 'owner_id']], on=['year', 'team_id'])
    
    championship_counts = champs_with_owners.groupby('owner_id').size().reset_index(name='Championships')
    
    return championship_counts

def analyze_records(teams_df, matchups_df, is_playoff):
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
        all_owners = teams_df[['owner_id', 'owner']].drop_duplicates(subset='owner_id').rename(columns={'owner': 'latest_name'})
        final_records = pd.merge(all_owners, records, on='owner_id', how='left').fillna(0)
        final_records['display_name'] = final_records['display_name'].fillna(final_records['latest_name'])
        final_records = pd.merge(final_records, championship_counts, on='owner_id', how='left').fillna(0)
        final_records['Championships'] = final_records['Championships'].astype(int)
        final_records['win_pct'] = final_records['wins'] / (final_records['wins'] + final_records['losses'])
        final_records = final_records.fillna(0.0).sort_values(by=['win_pct', 'wins'], ascending=[False, False]).reset_index(drop=True)

        print(f"\n--- Definitive Career {report_type} Records (All-Time) ---")
        print("-" * 85)
        print(f"{'Rank':<5} {'Owner':<25} {'Record (W-L-T)':<18} {'Win %':<10} {'Championships':<15}")
        print("-" * 85)
        for i, row in final_records.iterrows():
            rank, owner, record_str, win_pct_str, champs_str = i + 1, row['display_name'], f"{int(row['wins'])}-{int(row['losses'])}-{int(row['ties'])}", f"{row['win_pct']:.3f}", row['Championships']
            print(f" {rank:<4} {owner:<25} {record_str:<18} {win_pct_str:<10} {champs_str:<15}")
        print("-" * 85)

if __name__ == '__main__':
    main()
