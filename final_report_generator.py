# final_report_generator.py
import sqlite3
import pandas as pd

DB_NAME = 'fantasy_data.db'

def find_true_champions(teams_df, matchups_df):
    """
    Finds the champion of each season by reconstructing the playoff bracket.
    This is the validated logic from the previous step.
    """
    champions = []
    for year in range(2016, 2026):
        playoffs = matchups_df[(matchups_df['year'] == year) & (matchups_df['is_playoff'] == 1) & (matchups_df['matchup_type'] == 'WINNERS_BRACKET')]
        if playoffs.empty: continue
        playoff_weeks = sorted(playoffs['week'].unique())
        if len(playoff_weeks) >= 4:
            semi_final_weeks, final_weeks = playoff_weeks[:2], playoff_weeks[2:4]
            semi_finals = playoffs[playoffs['week'].isin(semi_final_weeks)]
            semi_final_teams = pd.concat([semi_finals['home_team_id'], semi_finals['away_team_id']]).unique()
            team_scores = {team_id: semi_finals[semi_finals['home_team_id'] == team_id]['home_score'].sum() + semi_finals[semi_finals['away_team_id'] == team_id]['away_score'].sum() for team_id in semi_final_teams}
            matchup1 = semi_finals[semi_finals['week'] == semi_final_weeks[0]]
            winners = [row['home_team_id'] if team_scores.get(row['home_team_id'], 0) > team_scores.get(row['away_team_id'], 0) else row['away_team_id'] for _, row in matchup1.iterrows()]
            if len(winners) == 2:
                finals = playoffs[playoffs['week'].isin(final_weeks) & playoffs['home_team_id'].isin(winners) & playoffs['away_team_id'].isin(winners)]
                if not finals.empty:
                    score1 = finals[finals['home_team_id'] == winners[0]]['home_score'].sum() + finals[finals['away_team_id'] == winners[0]]['away_score'].sum()
                    score2 = finals[finals['home_team_id'] == winners[1]]['home_score'].sum() + finals[finals['away_team_id'] == winners[1]]['away_score'].sum()
                    champions.append({'year': year, 'champion_id': winners[0] if score1 > score2 else winners[1]})
                    continue
        final_week = playoffs['week'].max()
        final_games_in_week = playoffs[playoffs['week'] == final_week].copy()
        if not final_games_in_week.empty:
            final_games_in_week['total_score'] = final_games_in_week['home_score'] + final_games_in_week['away_score']
            top_game = final_games_in_week.loc[final_games_in_week['total_score'].idxmax()]
            champion_id = top_game['home_team_id'] if top_game['home_score'] > top_game['away_score'] else top_game['away_team_id']
            champions.append({'year': year, 'champion_id': champion_id})

    champions_df = pd.DataFrame(champions)
    champs_with_owners = pd.merge(champions_df, teams_df, left_on=['year', 'champion_id'], right_on=['year', 'team_id'])
    return champs_with_owners.groupby('owner_id').size().reset_index(name='Championships')

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
    teams_df = pd.read_sql_query("SELECT * FROM teams", conn)
    matchups_df = pd.read_sql_query("SELECT * FROM matchups", conn)
    conn.close()

    teams_df.loc[teams_df['owner'] == 'Alex Guam', 'owner_id'] = '{0690C529-10A3-4648-B467-4B594AE11B8E}'
    
    # Calculate seasons played for avg wins calculation
    seasons_played = teams_df.groupby('owner_id').size().reset_index(name='seasons_played')

    championship_counts = find_true_champions(teams_df, matchups_df)
    
    for is_playoff_report in [False, True]:
        report_type = "Playoff" if is_playoff_report else "Regular Season"
        records = analyze_records(teams_df, matchups_df, is_playoff=is_playoff_report)
        all_owners = teams_df[['owner_id', 'owner']].drop_duplicates(subset='owner_id').rename(columns={'owner': 'latest_name'})
        final_records = pd.merge(all_owners, records, on='owner_id', how='left').fillna(0)
        final_records = pd.merge(final_records, seasons_played, on='owner_id', how='left')
        final_records = pd.merge(final_records, championship_counts, on='owner_id', how='left').fillna(0)
        final_records['display_name'] = final_records['display_name'].fillna(final_records['latest_name'])
        
        if not is_playoff_report:
            final_records['avg_wins'] = final_records['wins'] / final_records['seasons_played']

        final_records['Championships'] = final_records['Championships'].astype(int)
        final_records['win_pct'] = final_records['wins'] / (final_records['wins'] + final_records['losses'])
        final_records = final_records.fillna(0.0).sort_values(by='win_pct', ascending=False).reset_index(drop=True)

        print(f"\n--- Definitive Career {report_type} Records (All-Time) ---")
        header = f"{'Rank':<5} {'Owner':<25} {'Record (W-L-T)':<18} {'Win %':<10} {'Championships':<15}"
        if not is_playoff_report:
            header += f"{'Avg Wins/Season':<20}"
        print(header)
        print("-" * len(header))
        for i, row in final_records.iterrows():
            record_str = f"{int(row['wins'])}-{int(row['losses'])}-{int(row['ties'])}"
            line = f" {i+1:<4} {row['display_name']:<25} {record_str:<18} {row['win_pct']:.3f}{' ':<5} {row['Championships']:<15}"
            if not is_playoff_report:
                line += f"{row['avg_wins']:.2f}"
            print(line)
        print("-" * len(header))

if __name__ == '__main__':
    main()
