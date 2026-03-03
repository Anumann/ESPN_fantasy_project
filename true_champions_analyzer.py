# true_champions_analyzer.py
import sqlite3
import pandas as pd
from collections import defaultdict

DB_NAME = 'fantasy_data.db'

def get_all_champions_by_year(teams_df, matchups_df):
    """
    Determines the champion for each year.
    Returns a dictionary mapping year to the winning owner_id.
    """
    playoffs = matchups_df[matchups_df['is_playoff'] == 1].copy()
    if playoffs.empty:
        return {}
    
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
    champions = pd.merge(
        championship_games[['year', 'winner_id']],
        teams_df[['team_id', 'year', 'owner_id', 'owner']],
        left_on=['year', 'winner_id'],
        right_on=['year', 'team_id']
    )
    
    # Create a simple dict of {year: owner_id}
    champions_dict = dict(zip(champions['year'], champions['owner_id']))
    return champions_dict

def main():
    """
    Prints a season-by-season history for each manager,
    marking championship years with a trophy.
    """
    conn = sqlite3.connect(DB_NAME)
    # Exclude teams with unknown owners to keep data clean
    teams_df = pd.read_sql_query("SELECT * FROM teams WHERE owner_id != 'UNKNOWN_ID'", conn)
    matchups_df = pd.read_sql_query("SELECT * FROM matchups", conn)
    conn.close()

    champions_by_year = get_all_champions_by_year(teams_df, matchups_df)
    
    # Group teams by owner to build a history for each
    owner_history = defaultdict(list)
    owner_names = {}

    # Sort by year to process chronologically
    for _, row in teams_df.sort_values('year').iterrows():
        owner_id = row['owner_id']
        year = row['year']
        
        # Store the most recent owner name
        owner_names[owner_id] = row['owner']
        
        # Check if this owner was the champion this year
        is_champion = champions_by_year.get(year) == owner_id
        
        # Append the year and a trophy if they won
        season_marker = f"{year} 🏆" if is_champion else str(year)
        owner_history[owner_id].append(season_marker)

    print("--- Manager Season Histories ---")
    print("(Includes all seasons played, with championships marked by 🏆)")
    
    # Sort owners by their most recent name for consistent ordering
    sorted_owner_ids = sorted(owner_names, key=lambda oid: owner_names[oid])

    for owner_id in sorted_owner_ids:
        name = owner_names[owner_id]
        history = ", ".join(owner_history[owner_id])
        print(f"\n{name}:")
        print(f"  {history}")

if __name__ == '__main__':
    main()
