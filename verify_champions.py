# verify_champions.py
import sqlite3
import pandas as pd

DB_NAME = 'fantasy_data.db'

def find_true_champions(teams_df, matchups_df):
    """
    Finds the champion of each season by reconstructing the playoff winners bracket
    from raw game scores, summing scores for two-week matchups as required.
    """
    champions = []
    
    for year in range(2016, 2026):
        playoffs = matchups_df[
            (matchups_df['year'] == year) &
            (matchups_df['is_playoff'] == 1) &
            (matchups_df['matchup_type'] == 'WINNERS_BRACKET')
        ].copy()

        if playoffs.empty:
            print(f"- {year}: No winners bracket data found.")
            continue
            
        playoff_weeks = sorted(playoffs['week'].unique())
        
        # Logic for two-round, two-week-per-matchup playoffs (4 total weeks)
        if len(playoff_weeks) >= 4:
            semi_final_weeks = playoff_weeks[:2]
            semi_finals = playoffs[playoffs['week'].isin(semi_final_weeks)]
            semi_final_teams = pd.concat([semi_finals['home_team_id'], semi_finals['away_team_id']]).unique()
            team_scores = {team_id: semi_finals[semi_finals['home_team_id'] == team_id]['home_score'].sum() + semi_finals[semi_finals['away_team_id'] == team_id]['away_score'].sum() for team_id in semi_final_teams}
            
            matchup1 = semi_finals[semi_finals['week'] == semi_final_weeks[0]]
            winners = []
            for _, row in matchup1.iterrows():
                team1_id, team2_id = row['home_team_id'], row['away_team_id']
                winners.append(team1_id if team_scores.get(team1_id, 0) > team_scores.get(team2_id, 0) else team2_id)
            
            if len(winners) == 2:
                final_weeks = playoff_weeks[2:4]
                finals = playoffs[playoffs['week'].isin(final_weeks) & playoffs['home_team_id'].isin(winners) & playoffs['away_team_id'].isin(winners)]
                if not finals.empty:
                    finalist1_id, finalist2_id = winners[0], winners[1]
                    score1 = finals[finals['home_team_id'] == finalist1_id]['home_score'].sum() + finals[finals['away_team_id'] == finalist1_id]['away_score'].sum()
                    score2 = finals[finals['home_team_id'] == finalist2_id]['home_score'].sum() + finals[finals['away_team_id'] == finalist2_id]['away_score'].sum()
                    champion_id = finalist1_id if score1 > score2 else finalist2_id
                    champions.append({'year': year, 'champion_id': champion_id})
                    continue

        # Fallback for single-week matchups
        final_week = playoffs['week'].max()
        final_game = playoffs[(playoffs['week'] == final_week) & (playoffs['matchup_type'] == 'WINNERS_BRACKET')]
        if not final_game.empty:
            # In case of multiple games in the final week (e.g., 3rd place), we need to identify the real final.
            # A simple heuristic is the highest-scoring game. A more robust method would be needed for more complex leagues.
            final_game = final_game.loc[(final_game['home_score'] + final_game['away_score']).idxmax()]
            winner = final_game
            champion_id = winner['home_team_id'] if winner['home_score'] > winner['away_score'] else winner['away_team_id']
            champions.append({'year': year, 'champion_id': champion_id})

    champions_df = pd.DataFrame(champions)
    champs_with_owners = pd.merge(champions_df, teams_df, left_on=['year', 'champion_id'], right_on=['year', 'team_id'])
    return champs_with_owners[['year', 'owner']].sort_values(by='year')

def main():
    conn = sqlite3.connect(DB_NAME)
    teams_df = pd.read_sql_query("SELECT * FROM teams", conn)
    matchups_df = pd.read_sql_query("SELECT * FROM matchups", conn)
    conn.close()
    
    # Consolidate Alex Guam's records
    teams_df.loc[teams_df['owner'] == 'Alex Guam', 'owner_id'] = '{0690C529-10A3-4648-B467-4B594AE11B8E}'

    champion_list = find_true_champions(teams_df, matchups_df)
    
    print("--- Preliminary List of Champions ---")
    print(champion_list.to_string(index=False))

if __name__ == '__main__':
    main()
