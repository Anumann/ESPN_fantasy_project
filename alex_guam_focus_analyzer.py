# al Guam_focus_analyzer.py
import sqlite3
import pandas as pd
import time
import config
from espn_api.football import League

DB_NAME = 'fantasy_data.db'

def get_championships_for_alex(teams_df):
    """
    Finds all championships associated with any known 'Alex Guam' profile.
    """
    target_owner_ids = ['{0690C529-10A3-4648-B467-4B594AE11B8E}', 'UNKNOWN_ID']
    championship_years = []
    
    for year in range(2025, 2015, -1):
        try:
            league = League(league_id=config.LEAGUE_ID, year=year, espn_s2=config.ESPN_S2, swid=config.SWID)
            for team in league.teams:
                owner_id = team.owners[0]['id'] if team.owners and team.owners[0] and 'id' in team.owners[0] else 'UNKNOWN_ID'
                if team.final_standing == 1 and owner_id in target_owner_ids:
                    championship_years.append(year)
            time.sleep(2)
        except Exception:
            continue
            
    return len(championship_years), championship_years

def analyze_records_for_alex(teams_df, matchups_df):
    """
    Aggregates all stats for any 'Alex Guam' profile.
    """
    target_teams = teams_df[
        (teams_df['owner_id'] == '{0690C529-10A3-4648-B467-4B594AE11B8E}') | 
        ((teams_df['owner_id'] == 'UNKNOWN_ID') & (teams_df['owner'] == 'Alex Guam'))
    ]

    team_year_pairs = target_teams[['team_id', 'year']]
    
    # Filter matchups to only include games played by Alex Guam's teams
    home_games = pd.merge(matchups_df, team_year_pairs, left_on=['home_team_id', 'year'], right_on=['team_id', 'year'])
    away_games = pd.merge(matchups_df, team_year_pairs, left_on=['away_team_id', 'year'], right_on=['team_id', 'year'])
    
    # Regular Season
    reg_home = home_games[home_games['is_playoff'] == 0]
    reg_away = away_games[away_games['is_playoff'] == 0]
    reg_wins = (reg_home['home_score'] > reg_home['away_score']).sum() + (reg_away['away_score'] > reg_away['home_score']).sum()
    reg_losses = (reg_home['home_score'] < reg_home['away_score']).sum() + (reg_away['away_score'] < reg_away['home_score']).sum()
    reg_ties = (reg_home['home_score'] == reg_home['away_score']).sum() + (reg_away['away_score'] == reg_away['home_score']).sum()

    # Playoffs
    playoff_home = home_games[home_games['is_playoff'] == 1]
    playoff_away = away_games[away_games['is_playoff'] == 1]
    playoff_wins = (playoff_home['home_score'] > playoff_home['away_score']).sum() + (playoff_away['away_score'] > playoff_away['home_score']).sum()
    playoff_losses = (playoff_home['home_score'] < playoff_home['away_score']).sum() + (playoff_away['away_score'] < playoff_away['home_score']).sum()
    playoff_ties = (playoff_home['home_score'] == playoff_home['away_score']).sum() + (playoff_away['away_score'] == playoff_away['home_score']).sum()
    
    return (reg_wins, reg_losses, reg_ties), (playoff_wins, playoff_losses, playoff_ties)

def main():
    conn = sqlite3.connect(DB_NAME)
    teams_df = pd.read_sql_query("SELECT * FROM teams", conn)
    matchups_df = pd.read_sql_query("SELECT * FROM matchups", conn)
    conn.close()

    championship_count, championship_years = get_championships_for_alex(teams_df)
    reg_record, playoff_record = analyze_records_for_alex(teams_df, matchups_df)

    print("\n--- Consolidated Career Record for Alex Guam ---")
    print("-" * 50)
    print("REGULAR SEASON")
    print(f"  Record: {reg_record[0]}-{reg_record[1]}-{reg_record[2]}")
    print(f"  Win %:  {reg_record[0] / (reg_record[0] + reg_record[1]):.3f}")
    print("\nPLAYOFFS")
    print(f"  Record: {playoff_record[0]}-{playoff_record[1]}-{playoff_record[2]}")
    print(f"  Win %:  {playoff_record[0] / (playoff_record[0] + playoff_record[1]):.3f}")
    print("\nCHAMPIONSHIPS")
    print(f"  Total: {championship_count}")
    print(f"  Years: {sorted(championship_years)}")
    print("-" * 50)

if __name__ == '__main__':
    main()
