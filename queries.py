import sqlite3
import pandas as pd
import os

DB_FILENAME = 'fantasy_data.db'

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    try:
        # The path is relative to the script's location.
        # When run by Streamlit, the working directory is the project root.
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_FILENAME)
        if not os.path.exists(db_path):
             # Fallback for local dev if the above path fails
            db_path = DB_FILENAME
            if not os.path.exists(db_path):
                print(f"ERROR: Database file not found at {db_path}")
                return None
        return sqlite3.connect(db_path)
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def find_true_champions(teams_df, matchups_df):
    champions = []
    years = sorted(teams_df['year'].unique())
    for year in years:
        playoffs = matchups_df[(matchups_df['year'] == year) & (matchups_df['is_playoff'] == 1) & (matchups_df['matchup_type'] == 'WINNERS_BRACKET')]
        if playoffs.empty: continue
        playoff_weeks = sorted(playoffs['week'].unique())
        champion_id = None
        runner_up_id = None
        winning_score = 0
        losing_score = 0
        
        if len(playoff_weeks) >= 2:
            if len(playoff_weeks) >= 4:
                semi_final_weeks, final_weeks = playoff_weeks[:2], playoff_weeks[2:4]
                semi_finals = playoffs[playoffs['week'].isin(semi_final_weeks)]
                semi_final_teams = pd.concat([semi_finals['home_team_id'], semi_finals['away_team_id']]).unique()
                team_scores = {}
                for team_id in semi_final_teams:
                    home_pts = semi_finals[semi_finals['home_team_id'] == team_id]['home_score'].sum()
                    away_pts = semi_finals[semi_finals['away_team_id'] == team_id]['away_score'].sum()
                    team_scores[team_id] = home_pts + away_pts
                matchup1 = semi_finals[semi_finals['week'] == semi_final_weeks[0]]
                winners = []
                for _, row in matchup1.iterrows():
                    h_score = team_scores.get(row['home_team_id'], 0)
                    a_score = team_scores.get(row['away_team_id'], 0)
                    winners.append(row['home_team_id'] if h_score > a_score else row['away_team_id'])
                if len(winners) == 2:
                    finals = playoffs[playoffs['week'].isin(final_weeks) & playoffs['home_team_id'].isin(winners) & playoffs['away_team_id'].isin(winners)]
                    if not finals.empty:
                        score1 = finals[finals['home_team_id'] == winners[0]]['home_score'].sum() + finals[finals['away_team_id'] == winners[0]]['away_score'].sum()
                        score2 = finals[finals['home_team_id'] == winners[1]]['home_score'].sum() + finals[finals['away_team_id'] == winners[1]]['away_score'].sum()
                        if score1 > score2:
                            champion_id = winners[0]
                            runner_up_id = winners[1]
                            winning_score = score1
                            losing_score = score2
                        else:
                            champion_id = winners[1]
                            runner_up_id = winners[0]
                            winning_score = score2
                            losing_score = score1
            if not champion_id:
                final_week = playoffs['week'].max()
                final_games = playoffs[playoffs['week'] == final_week].copy()
                if not final_games.empty:
                    final_games['total'] = final_games['home_score'] + final_games['away_score']
                    top_game = final_games.loc[final_games['total'].idxmax()]
                    if top_game['home_score'] > top_game['away_score']:
                        champion_id = top_game['home_team_id']
                        runner_up_id = top_game['away_team_id']
                        winning_score = top_game['home_score']
                        losing_score = top_game['away_score']
                    else:
                        champion_id = top_game['away_team_id']
                        runner_up_id = top_game['home_team_id']
                        winning_score = top_game['away_score']
                        losing_score = top_game['home_score']
                        
        if champion_id: 
            champions.append({
                'year': year, 
                'champion_id': champion_id,
                'runner_up_id': runner_up_id,
                'score_str': f"{winning_score:.2f} - {losing_score:.2f}"
            })
    return pd.DataFrame(champions)

def get_league_champions():
    conn = get_db_connection()
    if not conn: return pd.DataFrame()
    teams_df = pd.read_sql_query("SELECT * FROM teams", conn)
    matchups_df = pd.read_sql_query("SELECT * FROM matchups", conn)
    conn.close()
    teams_df.loc[teams_df['owner'] == 'Alex Guam', 'owner_id'] = '{0690C529-10A3-4648-B467-4B594AE11B8E}'
    
    champs_list = find_true_champions(teams_df, matchups_df)
    if champs_list.empty: return pd.DataFrame(columns=['year', 'team_name', 'owner_name', 'record', 'points_for', 'runner_up', 'score'])
    
    merged = pd.merge(champs_list, teams_df[['team_id', 'year', 'team_name', 'owner']], left_on=['year', 'champion_id'], right_on=['year', 'team_id'])
    merged = merged.rename(columns={'owner': 'owner_name'})
    
    merged = pd.merge(merged, teams_df[['team_id', 'year', 'owner']], left_on=['year', 'runner_up_id'], right_on=['year', 'team_id'], suffixes=('', '_ru'))
    merged = merged.rename(columns={'owner': 'runner_up_name'})
    
    results = []
    for _, row in merged.iterrows():
        team_id = row['champion_id']
        year = row['year']
        season_games = matchups_df[(matchups_df['year'] == year) & (matchups_df['is_playoff'] == 0) & ((matchups_df['home_team_id'] == team_id) | (matchups_df['away_team_id'] == team_id))]
        wins = 0; losses = 0; ties = 0; pts = 0
        for _, game in season_games.iterrows():
            if game['home_team_id'] == team_id: score = game['home_score']; opp_score = game['away_score']
            else: score = game['away_score']; opp_score = game['home_score']
            pts += score
            if score > opp_score: wins += 1
            elif score < opp_score: losses += 1
            else: ties += 1
        results.append({
            'year': year, 
            'team_name': row['team_name'], 
            'owner_name': row['owner_name'], 
            'record': f"{wins}-{losses}-{ties}", 
            'points_for': pts,
            'runner_up': row['runner_up_name'],
            'score': row['score_str']
        })
    return pd.DataFrame(results).sort_values('year', ascending=False)

def get_all_time_standings(season_type='Regular Season'):
    conn = get_db_connection()
    if not conn: return pd.DataFrame()
    teams_df = pd.read_sql_query("SELECT * FROM teams", conn)
    matchups_df = pd.read_sql_query("SELECT * FROM matchups", conn)
    conn.close()
    teams_df.loc[teams_df['owner'] == 'Alex Guam', 'owner_id'] = '{0690C529-10A3-4648-B467-4B594AE11B8E}'
    is_playoff = (season_type == 'Playoffs')
    games = matchups_df[matchups_df['is_playoff'] == (1 if is_playoff else 0)]
    home = games[['year', 'home_team_id', 'home_score', 'away_score']].rename(columns={'home_team_id': 'team_id', 'home_score': 'score', 'away_score': 'opponent_score'})
    away = games[['year', 'away_team_id', 'away_score', 'home_score']].rename(columns={'away_team_id': 'team_id', 'away_score': 'score', 'home_score': 'opponent_score'})
    all_games = pd.concat([home, away])
    all_games['wins'] = (all_games['score'] > all_games['opponent_score']).astype(int)
    all_games['losses'] = (all_games['score'] < all_games['opponent_score']).astype(int)
    all_games['ties'] = (all_games['score'] == all_games['opponent_score']).astype(int)
    merged = pd.merge(all_games, teams_df, on=['team_id', 'year'])
    summary = merged.groupby('owner_id').agg(owner_name=('owner', 'last'), games_played=('wins', 'count'), wins=('wins', 'sum'), losses=('losses', 'sum'), ties=('ties', 'sum'), total_points=('score', 'sum')).reset_index()
    summary['win_pct'] = summary['wins'] / summary['games_played']
    summary['avg_points'] = summary['total_points'] / summary['games_played']
    return summary.sort_values('win_pct', ascending=False)

def get_all_owners():
    conn = get_db_connection()
    if not conn: return []
    owners = pd.read_sql_query("SELECT DISTINCT owner FROM teams ORDER BY owner", conn)
    conn.close()
    return owners['owner'].tolist()

def get_head_to_head(owner1, owner2):
    conn = get_db_connection()
    if not conn: return pd.DataFrame()
    teams_df = pd.read_sql_query("SELECT * FROM teams", conn)
    matchups_df = pd.read_sql_query("SELECT * FROM matchups", conn)
    conn.close()
    games = matchups_df.copy()
    games = pd.merge(games, teams_df[['team_id', 'year', 'owner']], left_on=['home_team_id', 'year'], right_on=['team_id', 'year'], suffixes=('', '_home'))
    games = games.rename(columns={'owner': 'home_owner'})
    games = pd.merge(games, teams_df[['team_id', 'year', 'owner']], left_on=['away_team_id', 'year'], right_on=['team_id', 'year'], suffixes=('', '_away'))
    games = games.rename(columns={'owner': 'away_owner'})
    h2h = games[((games['home_owner'] == owner1) & (games['away_owner'] == owner2)) | ((games['home_owner'] == owner2) & (games['away_owner'] == owner1))]
    clean_results = []
    for _, match in h2h.iterrows():
        if match['home_owner'] == owner1:
            my_score = match['home_score']; opp_score = match['away_score']
        else:
            my_score = match['away_score']; opp_score = match['home_score']
        outcome = 'TIE'
        if my_score > opp_score: outcome = 'WIN'
        elif my_score < opp_score: outcome = 'LOSS'
        clean_results.append({'year': match['year'], 'week': match['week'], 'points': my_score, 'opponent_points': opp_score, 'outcome': outcome})
    return pd.DataFrame(clean_results).sort_values(['year', 'week'], ascending=False)

def get_luck_metrics():
    conn = get_db_connection()
    if not conn: return {}
    teams_df = pd.read_sql_query("SELECT * FROM teams", conn)
    matchups_df = pd.read_sql_query("SELECT * FROM matchups", conn)
    conn.close()
    matchups_df = matchups_df[matchups_df['is_playoff'] == 0]
    home = matchups_df[['year', 'week', 'home_team_id', 'home_score', 'away_team_id', 'away_score']].copy()
    home = pd.merge(home, teams_df[['team_id', 'year', 'owner']], left_on=['home_team_id', 'year'], right_on=['team_id', 'year'], right_index=False)
    home = home.rename(columns={'owner': 'owner', 'home_score': 'score', 'away_score': 'opp_score'})
    home = pd.merge(home, teams_df[['team_id', 'year', 'owner']], left_on=['away_team_id', 'year'], right_on=['team_id', 'year'], suffixes=('', '_opp'))
    home = home.rename(columns={'owner_opp': 'opponent'})
    away = matchups_df[['year', 'week', 'away_team_id', 'away_score', 'home_team_id', 'home_score']].copy()
    away = pd.merge(away, teams_df[['team_id', 'year', 'owner']], left_on=['away_team_id', 'year'], right_on=['team_id', 'year'])
    away = away.rename(columns={'owner': 'owner', 'away_score': 'score', 'home_score': 'opp_score'})
    away = pd.merge(away, teams_df[['team_id', 'year', 'owner']], left_on=['home_team_id', 'year'], right_on=['team_id', 'year'], suffixes=('', '_opp'))
    away = away.rename(columns={'owner_opp': 'opponent'})
    all_scores = pd.concat([home[['year', 'week', 'owner', 'score', 'opponent', 'opp_score']], away[['year', 'week', 'owner', 'score', 'opponent', 'opp_score']]])
    losses = all_scores[all_scores['score'] < all_scores['opp_score']]
    heartbreak = losses.sort_values('score', ascending=False).head(10)
    wins = all_scores[all_scores['score'] > all_scores['opp_score']]
    lucky_duck = wins.sort_values('score', ascending=True).head(10)
    ap_stats = {} 
    weeks = all_scores[['year', 'week']].drop_duplicates()
    for _, w_row in weeks.iterrows():
        y, w = w_row['year'], w_row['week']
        week_data = all_scores[(all_scores['year'] == y) & (all_scores['week'] == w)]
        scores_list = week_data['score'].tolist()
        for _, row in week_data.iterrows():
            owner = row['owner']
            score = row['score']
            w_count = sum(1 for s in scores_list if score > s)
            l_count = sum(1 for s in scores_list if score < s)
            t_count = sum(1 for s in scores_list if score == s) - 1
            if owner not in ap_stats: ap_stats[owner] = {'ap_w':0, 'ap_l':0, 'ap_t':0, 'real_w':0, 'real_l':0, 'real_t':0}
            ap_stats[owner]['ap_w'] += w_count
            ap_stats[owner]['ap_l'] += l_count
            ap_stats[owner]['ap_t'] += t_count
            if score > row['opp_score']: ap_stats[owner]['real_w'] += 1
            elif score < row['opp_score']: ap_stats[owner]['real_l'] += 1
            else: ap_stats[owner]['real_t'] += 1
    ap_results = []
    for owner, s in ap_stats.items():
        total_ap = s['ap_w'] + s['ap_l'] + s['ap_t']
        ap_pct = s['ap_w'] / total_ap if total_ap > 0 else 0.0
        total_real = s['real_w'] + s['real_l'] + s['real_t']
        real_pct = s['real_w'] / total_real if total_real > 0 else 0.0
        diff = real_pct - ap_pct
        ap_results.append({'owner': owner, 'real_record': f"{s['real_w']}-{s['real_l']}-{s['real_t']}", 'real_pct': real_pct, 'ap_record': f"{s['ap_w']}-{s['ap_l']}-{s['ap_t']}", 'ap_pct': ap_pct, 'luck_diff': diff})
    all_play_df = pd.DataFrame(ap_results).sort_values('luck_diff', ascending=True)
    return {'heartbreak': heartbreak, 'lucky_duck': lucky_duck, 'all_play': all_play_df}

def get_owner_profile(owner_name):
    conn = get_db_connection()
    if not conn: return None
    teams_df = pd.read_sql_query("SELECT * FROM teams", conn)
    matchups_df = pd.read_sql_query("SELECT * FROM matchups", conn)
    conn.close()
    
    champs_df = find_true_champions(teams_df, matchups_df)
    if not champs_df.empty:
        champion_set = set(zip(champs_df['year'], champs_df['champion_id']))
    else:
        champion_set = set()
    
    teams_df.loc[teams_df['owner'] == 'Alex Guam', 'owner_id'] = '{0690C529-10A3-4648-B467-4B594AE11B8E}'
    my_teams = teams_df[teams_df['owner'] == owner_name]
    if my_teams.empty: return None
    season_log = []
    years = sorted(my_teams['year'].unique(), reverse=True)
    total_w = 0; total_l = 0; total_t = 0; total_pts = 0
    for year in years:
        team_row = my_teams[my_teams['year'] == year].iloc[0]
        team_id = team_row['team_id']
        team_name = team_row['team_name']
        games = matchups_df[(matchups_df['year'] == year) & (matchups_df['is_playoff'] == 0) & ((matchups_df['home_team_id'] == team_id) | (matchups_df['away_team_id'] == team_id))]
        w = 0; l = 0; t = 0; pts = 0
        for _, g in games.iterrows():
            if g['home_team_id'] == team_id: s = g['home_score']; o = g['away_score']
            else: s = g['away_score']; o = g['home_score']
            pts += s
            if s > o: w += 1
            elif s < o: l += 1
            else: t += 1
            
        is_champion = (year, team_id) in champion_set
        season_log.append({'year': year, 'team': team_name, 'record': f"{w}-{l}-{t}", 'points': pts, 'is_champion': is_champion})
        
        total_w += w; total_l += l; total_t += t; total_pts += pts
    all_games = []
    for year in years:
        team_id = my_teams[my_teams['year'] == year].iloc[0]['team_id']
        games = matchups_df[(matchups_df['year'] == year) & ((matchups_df['home_team_id'] == team_id) | (matchups_df['away_team_id'] == team_id))]
        for _, g in games.iterrows():
            if g['home_team_id'] == team_id: my_s = g['home_score']; opp_s = g['away_score']; opp_id = g['away_team_id']
            else: my_s = g['away_score']; opp_s = g['home_score']; opp_id = g['home_team_id']
            opp_row = teams_df[(teams_df['year'] == year) & (teams_df['team_id'] == opp_id)]
            if not opp_row.empty:
                opp_name = opp_row.iloc[0]['owner']
                res = 'W' if my_s > opp_s else ('L' if my_s < opp_s else 'T')
                all_games.append({'opponent': opp_name, 'result': res})
    rivals = pd.DataFrame(all_games)
    rivalry_stats = []
    if not rivals.empty:
        grouped = rivals.groupby('opponent')
        for opp, group in grouped:
            wins = len(group[group['result'] == 'W'])
            losses = len(group[group['result'] == 'L'])
            ties = len(group[group['result'] == 'T'])
            total = wins + losses + ties
            if total >= 3: 
                rivalry_stats.append({'opponent': opp, 'record': f"{wins}-{losses}-{ties}", 'win_pct': wins/total, 'total': total})
    if rivalry_stats: rivalries_df = pd.DataFrame(rivalry_stats).sort_values('win_pct', ascending=False)
    else: rivalries_df = pd.DataFrame(columns=['opponent', 'record', 'win_pct', 'total'])
    games_played = total_w + total_l + total_t
    win_pct = total_w / games_played if games_played > 0 else 0.0
    return {'career': {'wins': total_w, 'losses': total_l, 'ties': total_t, 'points': total_pts, 'win_pct': win_pct}, 'season_log': pd.DataFrame(season_log), 'rivalries': rivalries_df}

def get_all_ties():
    conn = get_db_connection()
    if not conn: return pd.DataFrame()
    query = """
        SELECT
            m.year,
            m.week,
            t1.owner AS manager_1,
            t2.owner AS manager_2,
            m.home_score AS score
        FROM matchups m
        JOIN teams t1 ON m.home_team_id = t1.team_id AND m.year = t1.year
        JOIN teams t2 ON m.away_team_id = t2.team_id AND m.year = t2.year
        WHERE m.home_score = m.away_score
        ORDER BY m.year, m.week;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_league_records():
    conn = get_db_connection()
    if not conn: return {}
    
    matchups_df = pd.read_sql_query("SELECT * FROM matchups", conn)
    teams_df = pd.read_sql_query("SELECT * FROM teams", conn)
    conn.close()

    # Merge to get team/owner names
    merged = matchups_df.merge(teams_df, left_on=['year', 'home_team_id'], right_on=['year', 'team_id'], suffixes=('', '_home'))
    merged = merged.rename(columns={'owner': 'home_owner'})
    merged = merged.merge(teams_df, left_on=['year', 'away_team_id'], right_on=['year', 'team_id'], suffixes=('', '_away'))
    merged = merged.rename(columns={'owner': 'away_owner'})

    # Calculate margins and totals
    merged['margin'] = (merged['home_score'] - merged['away_score']).abs()
    merged['total_score'] = merged['home_score'] + merged['away_score']

    # Unpivot for individual high/low scores
    scores_home = merged[['year', 'week', 'home_owner', 'home_score']].rename(columns={'home_owner': 'owner', 'home_score': 'score'})
    scores_away = merged[['year', 'week', 'away_owner', 'away_score']].rename(columns={'away_owner': 'owner', 'away_score': 'score'})
    all_scores = pd.concat([scores_home, scores_away]).dropna(subset=['score'])

    # Find records
    highest_score = all_scores.loc[all_scores['score'].idxmax()]
    lowest_score = all_scores.loc[all_scores['score'].idxmin()]
    biggest_blowout = merged.loc[merged['margin'].idxmax()]
    closest_shave = merged.loc[merged['margin'][merged['margin'] > 0].idxmin()]
    highest_scoring_matchup = merged.loc[merged['total_score'].idxmax()]
    lowest_scoring_matchup = merged.loc[merged['total_score'].idxmin()]

    # Format output
    records = {
        "Highest Score": {
            "Year": int(highest_score['year']),
            "Week": int(highest_score['week']),
            "Manager": highest_score['owner'],
            "Points": f"{highest_score['score']:.2f}"
        },
        "Lowest Score": {
            "Year": int(lowest_score['year']),
            "Week": int(lowest_score['week']),
            "Manager": lowest_score['owner'],
            "Points": f"{lowest_score['score']:.2f}"
        },
        "Biggest Blowout": {
            "Year": int(biggest_blowout['year']),
            "Week": int(biggest_blowout['week']),
            "Matchup": f"{biggest_blowout['home_owner']} vs {biggest_blowout['away_owner']}",
            "Score": f"{biggest_blowout['home_score']:.2f} - {biggest_blowout['away_score']:.2f}",
            "Margin": f"{biggest_blowout['margin']:.2f}"
        },
        "Closest Shave": {
            "Year": int(closest_shave['year']),
            "Week": int(closest_shave['week']),
            "Matchup": f"{closest_shave['home_owner']} vs {closest_shave['away_owner']}",
            "Score": f"{closest_shave['home_score']:.2f} - {closest_shave['away_score']:.2f}",
            "Margin": f"{closest_shave['margin']:.2f}"
        },
        "Highest Scoring Matchup": {
            "Year": int(highest_scoring_matchup['year']),
            "Week": int(highest_scoring_matchup['week']),
            "Matchup": f"{highest_scoring_matchup['home_owner']} vs {highest_scoring_matchup['away_owner']}",
            "Score": f"{highest_scoring_matchup['home_score']:.2f} - {highest_scoring_matchup['away_score']:.2f}",
            "Total Points": f"{highest_scoring_matchup['total_score']:.2f}"
        },
        "Lowest Scoring Matchup": {
            "Year": int(lowest_scoring_matchup['year']),
            "Week": int(lowest_scoring_matchup['week']),
            "Matchup": f"{lowest_scoring_matchup['home_owner']} vs {lowest_scoring_matchup['away_owner']}",
            "Score": f"{lowest_scoring_matchup['home_score']:.2f} - {lowest_scoring_matchup['away_score']:.2f}",
            "Total Points": f"{lowest_scoring_matchup['total_score']:.2f}"
        }
    }
    return records

