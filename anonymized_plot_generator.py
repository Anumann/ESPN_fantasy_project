# anonymized_plot_generator.py
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

DB_NAME = 'fantasy_data.db'
YOUR_NAME = 'Alex'
REFERENCE_NAME = 'Alex Guam'

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
    summary['win_pct'] = summary['wins'] / (summary['wins'] + summary['losses'])
    summary = summary.fillna(0.0).sort_values(by='win_pct', ascending=False).reset_index(drop=True)
    return summary

def create_anonymized_plot(records, title, filename):
    """Generates and saves a bar chart with anonymized names."""
    # Anonymize names, replacing the reference name with the desired shorter name
    records['display_name'] = records['display_name'].apply(lambda name: YOUR_NAME if name == REFERENCE_NAME else name)
    records['display_name'] = [name if name == YOUR_NAME else f"Manager {i+1}" for i, name in enumerate(records['display_name'])]
    
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(12, 10))
    
    records_sorted = records.sort_values(by='win_pct', ascending=True)
    
    bars = ax.barh(records_sorted['display_name'], records_sorted['win_pct'], color='skyblue')
    
    # Highlight your bar
    if not records_sorted[records_sorted['display_name'] == YOUR_NAME].empty:
        your_bar_index = records_sorted[records_sorted['display_name'] == YOUR_NAME].index[0]
        # Find the bar object corresponding to your index
        for i, bar in enumerate(bars):
            if records_sorted.index[i] == your_bar_index:
                bar.set_color('salmon')
                break

    ax.set_xlabel('Winning Percentage', fontsize=12)
    ax.set_ylabel('Owner', fontsize=12)
    ax.set_title(title, fontsize=16, weight='bold')
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0%}'))
    ax.set_xlim(0, 1)
    
    for i, bar in enumerate(bars):
        record = records_sorted.iloc[i]
        record_str = f"{int(record['wins'])}-{int(record['losses'])}-{int(record['ties'])}"
        width = bar.get_width()
        ax.text(width + 0.01, bar.get_y() + bar.get_height()/2, f'{width:.1%} ({record_str})', va='center', ha='left', fontsize=9)
        
    plt.tight_layout(pad=1.5)
    plt.savefig(filename)
    print(f"Successfully saved anonymized plot to '{filename}'")

def main():
    conn = sqlite3.connect(DB_NAME)
    teams_df = pd.read_sql_query("SELECT * FROM teams", conn)
    matchups_df = pd.read_sql_query("SELECT * FROM matchups", conn)
    conn.close()
    teams_df.loc[teams_df['owner'] == REFERENCE_NAME, 'owner_id'] = '{0690C529-10A3-4648-B467-4B594AE11B8E}'

    reg_season_records = analyze_records(teams_df, matchups_df, is_playoff=False)
    create_anonymized_plot(reg_season_records, 'All-Time Regular Season Records (Anonymized)', 'espn-fantasy-project/regular_season_anonymous.png')

    playoff_records = analyze_records(teams_df, matchups_df, is_playoff=True)
    create_anonymized_plot(playoff_records, 'All-Time Playoff Records (Anonymized)', 'espn-fantasy-project/playoff_anonymous.png')

if __name__ == '__main__':
    main()
