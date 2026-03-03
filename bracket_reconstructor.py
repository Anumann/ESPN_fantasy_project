# bracket_reconstructor.py
import sqlite3
import pandas as pd

DB_NAME = 'fantasy_data.db'

def reconstruct_playoffs(year, teams_df, matchups_df):
    """
    Reconstructs the playoff bracket for a given year to find the champion,
    summing scores for two-week matchups.
    """
    playoffs = matchups_df[
        (matchups_df['year'] == year) &
        (matchups_df['is_playoff'] == 1) &
        (matchups_df['matchup_type'] == 'WINNERS_BRACKET')
    ].copy()

    if playoffs.empty:
        return f"No winners bracket data for {year}."

    playoff_weeks = sorted(playoffs['week'].unique())
    if len(playoff_weeks) < 4:
        return f"Not enough playoff weeks for a two-round, two-week matchup in {year}."

    # --- SEMI-FINALS ---
    semi_final_weeks = playoff_weeks[:2]
    semi_finals = playoffs[playoffs['week'].isin(semi_final_weeks)]
    
    # Identify the four unique teams in the semi-finals
    semi_final_teams = pd.concat([semi_finals['home_team_id'], semi_finals['away_team_id']]).unique()
    
    # Sum scores for each of the four teams across the two weeks
    team_scores = {}
    for team_id in semi_final_teams:
        home_score = semi_finals[semi_finals['home_team_id'] == team_id]['home_score'].sum()
        away_score = semi_finals[semi_finals['away_team_id'] == team_id]['away_score'].sum()
        team_scores[team_id] = home_score + away_score

    # Pair up the teams and determine winners
    # This assumes two matchups in the semi-finals
    matchup1_teams = semi_finals[semi_finals['week'] == semi_final_weeks[0]]
    
    winners = []
    for index, row in matchup1_teams.iterrows():
        team1_id = row['home_team_id']
        team2_id = row['away_team_id']
        
        if team_scores.get(team1_id, 0) > team_scores.get(team2_id, 0):
            winners.append(team1_id)
        else:
            winners.append(team2_id)
            
    if len(winners) != 2:
        return f"Could not determine two winners from the semi-finals in {year}."

    # --- CHAMPIONSHIP ---
    final_weeks = playoff_weeks[2:]
    finals = playoffs[playoffs['week'].isin(final_weeks)]
    
    # Filter to only include games between the two winners
    finals = finals[(finals['home_team_id'].isin(winners)) & (finals['away_team_id'].isin(winners))]

    if finals.empty:
        return f"Could not find the championship matchup in {year}."
        
    # Sum scores for the final two teams
    finalist1_id = winners[0]
    finalist2_id = winners[1]
    
    finalist1_score = finals[finals['home_team_id'] == finalist1_id]['home_score'].sum() + finals[finals['away_team_id'] == finalist1_id]['away_score'].sum()
    finalist2_score = finals[finals['home_team_id'] == finalist2_id]['home_score'].sum() + finals[finals['away_team_id'] == finalist2_id]['away_score'].sum()
    
    champion_id = finalist1_id if finalist1_score > finalist2_score else finalist2_id
    
    champion_owner = teams_df[(teams_df['team_id'] == champion_id) & (teams_df['year'] == year)]['owner'].iloc[0]
    
    return f"The reconstructed champion for {year} is: {champion_owner}"

def main():
    conn = sqlite3.connect(DB_NAME)
    teams_df = pd.read_sql_query("SELECT * FROM teams", conn)
    matchups_df = pd.read_sql_query("SELECT * FROM matchups", conn)
    conn.close()

    # Test with the year you corrected me on
    year_to_test = 2021
    result = reconstruct_playoffs(year_to_test, teams_df, matchups_df)
    print(result)

if __name__ == '__main__':
    main()
