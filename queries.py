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

def get_all_years():
    conn = get_db_connection()
    if not conn: return []
    years = pd.read_sql_query("SELECT DISTINCT year FROM seasons ORDER BY year DESC", conn)
    conn.close()
    return years['year'].tolist()

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
    years = sorted(my_teams['year'].unique())
    total_w = 0; total_l = 0; total_t = 0; total_pts = 0
    
    for year in years:
        # Calculate full season standings to get rank
        teams_year = teams_df[teams_df['year'] == year]
        reg_season_games = matchups_df[(matchups_df['year'] == year) & (matchups_df['is_playoff'] == 0)]
        standings = {team_id: {'w': 0, 'l': 0, 't': 0, 'pf': 0} for team_id in teams_year['team_id']}
        for _, game in reg_season_games.iterrows():
            h_id, a_id, h_s, a_s = game['home_team_id'], game['away_team_id'], game['home_score'], game['away_score']
            if h_id in standings: standings[h_id]['pf'] += h_s
            if a_id in standings: standings[a_id]['pf'] += a_s
            if h_s > a_s: 
                if h_id in standings: standings[h_id]['w'] += 1
                if a_id in standings: standings[a_id]['l'] += 1
            elif a_s > h_s:
                if a_id in standings: standings[a_id]['w'] += 1
                if h_id in standings: standings[h_id]['l'] += 1
            else:
                if h_id in standings: standings[h_id]['t'] += 1
                if a_id in standings: standings[a_id]['t'] += 1
        
        standings_df = pd.DataFrame.from_dict(standings, orient='index')
        standings_df['win_pct'] = standings_df['w'] / (standings_df['w'] + standings_df['l'] + standings_df['t'])
        standings_df = standings_df.sort_values(['win_pct', 'pf'], ascending=[False, False]).reset_index().rename(columns={'index': 'team_id'})
        standings_df['rank'] = standings_df.index + 1
        
        team_row = my_teams[my_teams['year'] == year].iloc[0]
        team_id = team_row['team_id']
        team_name = team_row['team_name']
        
        w = standings_df.loc[standings_df['team_id'] == team_id, 'w'].iloc[0]
        l = standings_df.loc[standings_df['team_id'] == team_id, 'l'].iloc[0]
        t = standings_df.loc[standings_df['team_id'] == team_id, 't'].iloc[0]
        pts = standings_df.loc[standings_df['team_id'] == team_id, 'pf'].iloc[0]
        rank = standings_df.loc[standings_df['team_id'] == team_id, 'rank'].iloc[0]

        is_champion = (year, team_id) in champion_set
        season_log.append({'year': year, 'team': team_name, 'record': f"{w}-{l}-{t}", 'points': pts, 'rank': rank, 'is_champion': is_champion})
        
        total_w += w; total_l += l; total_t += t; total_pts += pts
    
    rivalries_df = get_rivalry_matrix(owner_name, teams_df, matchups_df)

    games_played = total_w + total_l + total_t
    win_pct = total_w / games_played if games_played > 0 else 0.0
    return {'career': {'wins': total_w, 'losses': total_l, 'ties': total_t, 'points': total_pts, 'win_pct': win_pct}, 'season_log': pd.DataFrame(season_log), 'rivalries': rivalries_df}

def get_rivalry_matrix(owner_name, teams_df=None, matchups_df=None):
    if teams_df is None or matchups_df is None:
        conn = get_db_connection()
        if not conn: return pd.DataFrame()
        teams_df = pd.read_sql_query("SELECT * FROM teams", conn)
        matchups_df = pd.read_sql_query("SELECT * FROM matchups", conn)
        conn.close()

    my_teams = teams_df[teams_df['owner'] == owner_name]
    if my_teams.empty: return pd.DataFrame()

    all_games = []
    for _, team_row in my_teams.iterrows():
        year = team_row['year']
        team_id = team_row['team_id']
        
        games = matchups_df[(matchups_df['year'] == year) & ((matchups_df['home_team_id'] == team_id) | (matchups_df['away_team_id'] == team_id))]
        for _, g in games.iterrows():
            if g['home_team_id'] == team_id:
                my_s, opp_s, opp_id = g['home_score'], g['away_score'], g['away_team_id']
            else:
                my_s, opp_s, opp_id = g['away_score'], g['home_score'], g['home_team_id']
            
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
            rivalry_stats.append({'opponent': opp, 'record': f"{wins}-{losses}-{ties}", 'win_pct': wins/total, 'total': total})

    return pd.DataFrame(rivalry_stats).sort_values('total', ascending=False)


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
    
    matchups_df = pd.read_sql_query("SELECT * FROM matchups WHERE is_playoff = 0", conn)
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

    # Find records robustly by sorting and taking the first row
    highest_score = all_scores.sort_values('score', ascending=False).iloc[0]
    lowest_score = all_scores.sort_values('score', ascending=True).iloc[0]
    biggest_blowout = merged.sort_values('margin', ascending=False).iloc[0]
    closest_shave = merged[merged['margin'] > 0].sort_values('margin', ascending=True).iloc[0]
    highest_scoring_matchup = merged.sort_values('total_score', ascending=False).iloc[0]
    lowest_scoring_matchup = merged.sort_values('total_score', ascending=True).iloc[0]

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

def get_league_awards(year_to_filter):
    conn = get_db_connection()
    if not conn: return {}
    
    matchups_df = pd.read_sql_query("SELECT * FROM matchups", conn)
    teams_df = pd.read_sql_query("SELECT * FROM teams", conn)
    conn.close()

    matchups_year = matchups_df[matchups_df['year'] == year_to_filter]
    if matchups_year.empty: return {}
    teams_year = teams_df[teams_df['year'] == year_to_filter]

    reg_season_games = matchups_year[matchups_year['is_playoff'] == 0]
    if reg_season_games.empty: return {}

    # Award 1: Top Gun
    home_pts = reg_season_games[['home_team_id', 'home_score']].rename(columns={'home_team_id': 'team_id', 'home_score': 'score'})
    away_pts = reg_season_games[['away_team_id', 'away_score']].rename(columns={'away_team_id': 'team_id', 'away_score': 'score'})
    total_points = pd.concat([home_pts, away_pts]).groupby('team_id')['score'].sum().reset_index()
    top_gun_id = total_points.loc[total_points['score'].idxmax()]
    top_gun_team_info = teams_year[teams_year['team_id'] == top_gun_id['team_id']].iloc[0]
    top_gun_award = {"Manager": top_gun_team_info['owner'], "Team": top_gun_team_info['team_name'], "Total Points": f"{top_gun_id['score']:.2f}"}

    # Award 2: Heartbreak Kid
    heartbreak_awards = []
    for week in reg_season_games['week'].unique():
        weekly_games = reg_season_games[reg_season_games['week'] == week]
        home_scores = weekly_games[['home_team_id', 'home_score']].rename(columns={'home_team_id': 'team_id', 'home_score': 'score'})
        away_scores = weekly_games[['away_team_id', 'away_score']].rename(columns={'away_team_id': 'team_id', 'away_score': 'score'})
        weekly_all_scores = pd.concat([home_scores, away_scores]).sort_values('score', ascending=False).reset_index(drop=True)
        for i in [1, 2]:
            if i < len(weekly_all_scores):
                team_id = weekly_all_scores.iloc[i]['team_id']
                team_score = weekly_all_scores.iloc[i]['score']
                match = weekly_games[(weekly_games['home_team_id'] == team_id) | (weekly_games['away_team_id'] == team_id)].iloc[0]
                is_loss = (match['home_team_id'] == team_id and match['home_score'] < match['away_score']) or \
                          (match['away_team_id'] == team_id and match['away_score'] < match['home_score'])
                if is_loss:
                    team_info = teams_year[teams_year['team_id'] == team_id].iloc[0]
                    heartbreak_awards.append({"Manager": team_info['owner'], "Team": team_info['team_name'], "Week": int(week), "Score": f"{team_score:.2f}", "Rank": i + 1})

    # Award 3: Giant Killer
    wins = reg_season_games[reg_season_games['home_score'] != reg_season_games['away_score']]
    winners_data = []
    for _, row in wins.iterrows():
        if row['home_score'] > row['away_score']: winners_data.append({'team_id': row['home_team_id'], 'score': row['home_score'], 'week': row['week']})
        else: winners_data.append({'team_id': row['away_team_id'], 'score': row['away_score'], 'week': row['week']})
    giant_killer_award = {}
    if winners_data:
        lowest_win = pd.DataFrame(winners_data).loc[pd.DataFrame(winners_data)['score'].idxmin()]
        killer_team_info = teams_year[teams_year['team_id'] == lowest_win['team_id']].iloc[0]
        giant_killer_award = {"Manager": killer_team_info['owner'], "Team": killer_team_info['team_name'], "Week": int(lowest_win['week']), "Winning Score": f"{lowest_win['score']:.2f}"}

    # Award 4: The Underdog
    standings = {team_id: {'w': 0, 'l': 0, 't': 0, 'pf': 0} for team_id in teams_year['team_id']}
    for _, game in reg_season_games.iterrows():
        h_id, a_id, h_s, a_s = game['home_team_id'], game['away_team_id'], game['home_score'], game['away_score']
        standings[h_id]['pf'] += h_s
        standings[a_id]['pf'] += a_s
        if h_s > a_s: standings[h_id]['w'] += 1; standings[a_id]['l'] += 1
        elif a_s > h_s: standings[a_id]['w'] += 1; standings[h_id]['l'] += 1
        else: standings[h_id]['t'] += 1; standings[a_id]['t'] += 1
    standings_df = pd.DataFrame.from_dict(standings, orient='index')
    standings_df['win_pct'] = standings_df['w'] / (standings_df['w'] + standings_df['l'] + standings_df['t'])
    standings_df = standings_df.sort_values(['win_pct', 'pf'], ascending=[False, False]).reset_index().rename(columns={'index': 'team_id'})
    standings_df['seed'] = standings_df.index + 1
    
    playoff_games = matchups_year[(matchups_year['is_playoff'] == 1) & (matchups_year['matchup_type'] == 'WINNERS_BRACKET')]
    playoff_teams = pd.concat([playoff_games['home_team_id'], playoff_games['away_team_id']]).unique()
    
    playoff_standings = standings_df[standings_df['team_id'].isin(playoff_teams)]
    underdog_award = {}
    if not playoff_standings.empty:
        underdog_details = playoff_standings.loc[playoff_standings['seed'].idxmax()]
        underdog_team_info = teams_year[teams_year['team_id'] == underdog_details['team_id']].iloc[0]
        underdog_award = {"Manager": underdog_team_info['owner'], "Team": underdog_team_info['team_name'], "Seed": int(underdog_details['seed'])}
    
    # Award 5: Golden Bench (Most Points Left on Bench)
    golden_bench_award = {}
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT t.owner, t.team_name, SUM(wr.actual_points) as bench_points
            FROM weekly_rosters wr
            JOIN teams t ON wr.team_id = t.team_id AND wr.year = t.year
            WHERE wr.year = ? AND wr.lineup_slot = 'BE'
            GROUP BY wr.team_id
            ORDER BY bench_points DESC LIMIT 1
        ''', (year_to_filter,))
        res = cursor.fetchone()
        if res:
            golden_bench_award = {"Manager": res[0], "Team": res[1], "Bench Points": f"{res[2]:.2f}"}
            
        # Award 6: Draft Steal of the Year
        draft_steal_award = {}
        cursor.execute('''
            SELECT p.name, t.owner, dp.round_num, SUM(wr.actual_points) as points
            FROM weekly_rosters wr
            JOIN players p ON wr.player_id = p.player_id
            JOIN teams t ON wr.team_id = t.team_id AND wr.year = t.year
            JOIN draft_picks dp ON wr.year = dp.year AND wr.team_id = dp.team_id AND wr.player_id = dp.player_id
            WHERE wr.year = ? AND wr.lineup_slot NOT IN ('BE', 'IR') AND dp.round_num >= 10
            GROUP BY wr.player_id, wr.team_id
            ORDER BY points DESC LIMIT 1
        ''', (year_to_filter,))
        res2 = cursor.fetchone()
        if res2:
            draft_steal_award = {"Player": res2[0], "Manager": res2[1], "Round": res2[2], "Points": f"{res2[3]:.2f}"}

        # Award 7: Pickup of the Year
        pickup_award = {}
        cursor.execute('''
            WITH player_season_stats AS (
                SELECT wr.year, wr.team_id, wr.player_id, SUM(wr.actual_points) as total_points
                FROM weekly_rosters wr
                WHERE wr.year = ? AND wr.lineup_slot NOT IN ('BE', 'IR')
                GROUP BY wr.team_id, wr.player_id
            )
            SELECT p.name, t.owner, ps.total_points
            FROM player_season_stats ps
            JOIN players p ON ps.player_id = p.player_id
            JOIN teams t ON ps.team_id = t.team_id AND ps.year = t.year
            LEFT JOIN draft_picks dp ON ps.year = dp.year AND ps.team_id = dp.team_id AND ps.player_id = dp.player_id
            WHERE dp.pick_id IS NULL
            ORDER BY ps.total_points DESC LIMIT 1
        ''', (year_to_filter,))
        res3 = cursor.fetchone()
        if res3:
            pickup_award = {"Player": res3[0], "Manager": res3[1], "Points": f"{res3[2]:.2f}"}
            
        conn.close()
    except Exception as e:
        print(f"Error fetching granular awards: {e}")

    return {
        "Top Gun": top_gun_award,
        "Heartbreak Kid": heartbreak_awards,
        "Giant Killer": giant_killer_award,
        "The Underdog": underdog_award,
        "Golden Bench": golden_bench_award,
        "Draft Steal": draft_steal_award,
        "Pickup of the Year": pickup_award
    }

def get_all_season_point_totals():
    conn = get_db_connection()
    if not conn: return pd.DataFrame()
    
    query = """
        SELECT
            t.owner,
            m.year,
            SUM(CASE WHEN m.home_team_id = t.team_id THEN m.home_score ELSE m.away_score END) as total_points
        FROM matchups m
        JOIN teams t ON (m.year = t.year AND (m.home_team_id = t.team_id OR m.away_team_id = t.team_id))
        WHERE m.is_playoff = 0
        GROUP BY t.owner, m.year
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_trivia_categories():
    conn = get_db_connection()
    if not conn: return []
    df = pd.read_sql_query("SELECT DISTINCT category FROM questions ORDER BY category", conn)
    return df['category'].tolist()

def get_random_trivia_question(category=None):
    conn = get_db_connection()
    if not conn: return None
    
    query = "SELECT question_id, question_text, category FROM questions"
    params = []
    if category and category != "All Categories":
        query += " WHERE category = ?"
        params.append(category)
    
    questions_df = pd.read_sql_query(query, conn, params=params)
    if questions_df.empty:
        return None
    
    random_question = questions_df.sample(n=1).iloc[0]
    question_id = int(random_question['question_id'])
    
    answers_df = pd.read_sql_query("SELECT answer_text, is_correct FROM answers WHERE question_id = ?", conn, params=(question_id,))
    
    conn.close()
    
    return {
        "question_id": int(question_id),
        "question_text": random_question['question_text'],
        "category": random_question['category'],
        "answers": answers_df.to_dict('records')
    }



def get_granular_records():
    """Returns granular records like highest scoring positional players and best late draft picks."""
    conn = get_db_connection()
    if not conn: return {}
    
    query_base = """
    WITH player_season_stats AS (
        SELECT 
            wr.year,
            wr.team_id,
            t.owner,
            wr.player_id,
            p.name,
            p.default_position,
            SUM(wr.actual_points) as total_points
        FROM weekly_rosters wr
        JOIN players p ON wr.player_id = p.player_id
        JOIN teams t ON wr.team_id = t.team_id AND wr.year = t.year
        WHERE wr.lineup_slot NOT IN ('BE', 'IR')
        GROUP BY wr.year, wr.team_id, wr.player_id
    )
    """

    q_pos = query_base + """
    SELECT 
        default_position as 'Position', 
        name as 'Player', 
        owner as 'Manager', 
        year as 'Year', 
        total_points as 'Points'
    FROM (
        SELECT *, ROW_NUMBER() OVER(PARTITION BY default_position ORDER BY total_points DESC) as rn
        FROM player_season_stats
        WHERE default_position IN ('QB', 'RB', 'WR', 'TE', 'K', 'D/ST')
    ) WHERE rn = 1
    ORDER BY 
        CASE default_position 
            WHEN 'QB' THEN 1 
            WHEN 'RB' THEN 2 
            WHEN 'WR' THEN 3 
            WHEN 'TE' THEN 4 
            WHEN 'K' THEN 5 
            WHEN 'D/ST' THEN 6 
            ELSE 7 
        END
    """
    
    q_draft = query_base + """
    SELECT 
        ps.name as 'Player',
        ps.default_position as 'Position',
        ps.owner as 'Manager', 
        ps.year as 'Year', 
        dp.round_num as 'Round', 
        ps.total_points as 'Points'
    FROM player_season_stats ps
    JOIN draft_picks dp ON ps.year = dp.year AND ps.team_id = dp.team_id AND ps.player_id = dp.player_id
    WHERE dp.round_num >= 10
    ORDER BY ps.total_points DESC LIMIT 10
    """
    
    q_acq = query_base + """,
    first_rostered_week AS (
        SELECT 
            ps.year,
            ps.team_id,
            ps.player_id,
            MIN(wr.week) as min_week
        FROM player_season_stats ps
        JOIN weekly_rosters wr 
            ON ps.year = wr.year AND ps.team_id = wr.team_id AND ps.player_id = wr.player_id
        GROUP BY ps.year, ps.team_id, ps.player_id
    ),
    previous_week_roster AS (
        SELECT 
            frw.year,
            frw.team_id as current_team_id,
            frw.player_id,
            prev_t.owner as prev_owner
        FROM first_rostered_week frw
        LEFT JOIN weekly_rosters prev_wr
            ON frw.year = prev_wr.year 
            AND prev_wr.week = frw.min_week - 1
            AND frw.player_id = prev_wr.player_id
        LEFT JOIN teams prev_t 
            ON prev_wr.team_id = prev_t.team_id AND prev_wr.year = prev_t.year
    )
    SELECT 
        ps.name as 'Player', 
        ps.default_position as 'Position',
        ps.owner as 'Manager', 
        COALESCE(pwr.prev_owner, 'Free Agency') as 'Acquired From',
        ps.year as 'Year', 
        ps.total_points as 'Points'
    FROM player_season_stats ps
    LEFT JOIN draft_picks dp ON ps.year = dp.year AND ps.team_id = dp.team_id AND ps.player_id = dp.player_id
    JOIN previous_week_roster pwr 
        ON ps.year = pwr.year AND ps.team_id = pwr.current_team_id AND ps.player_id = pwr.player_id
    WHERE dp.pick_id IS NULL
    ORDER BY ps.total_points DESC LIMIT 10
    """

    try:
        import pandas as pd
        res = {
            'position': pd.read_sql_query(q_pos, conn),
            'draft': pd.read_sql_query(q_draft, conn),
            'acquisitions': pd.read_sql_query(q_acq, conn)
        }
    except Exception as e:
        print(f"Error fetching granular records: {e}")
        res = {}
        
    conn.close()
    return res
