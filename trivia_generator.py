import sqlite3
import pandas as pd
import os
import random

DB_FILENAME = 'fantasy_data.db'

def get_db_connection():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_FILENAME)
    if not os.path.exists(db_path):
        db_path = DB_FILENAME
        if not os.path.exists(db_path):
            print(f"ERROR: Database file not found at {db_path}")
            return None
    return sqlite3.connect(db_path)

def clear_existing_trivia(conn):
    """Clears the trivia tables before generating new ones."""
    print("Clearing existing trivia...")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM answers")
    cursor.execute("DELETE FROM questions")
    conn.commit()

def generate_all_time_records_trivia(matchups_df, teams_df):
    """Generates trivia questions based on all-time league records."""
    print("Generating 'All-Time Records' trivia...")
    trivia_list = []
    
    # Pre-merge for easier data access
    merged = matchups_df.merge(teams_df, left_on=['year', 'home_team_id'], right_on=['year', 'team_id'])
    merged = merged.rename(columns={'owner': 'home_owner'})
    merged = merged.merge(teams_df, left_on=['year', 'away_team_id'], right_on=['year', 'team_id'], suffixes=('', '_away'))
    merged = merged.rename(columns={'owner': 'away_owner'})
    
    # For individual scores - ONLY from regular season
    reg_season_games = merged[merged['is_playoff'] == 0]
    scores_home = reg_season_games[['year', 'week', 'home_owner', 'home_score']].rename(columns={'home_owner': 'owner', 'home_score': 'score'})
    scores_away = reg_season_games[['year', 'week', 'away_owner', 'away_score']].rename(columns={'away_owner': 'owner', 'away_score': 'score'})
    all_scores = pd.concat([scores_home, scores_away]).dropna(subset=['score']).sort_values('score', ascending=False).reset_index(drop=True)
    all_owners = teams_df['owner'].unique().tolist()

    # Q1: Highest single-week score
    if not all_scores.empty:
        top_score = all_scores.iloc[0]
        correct_answer = top_score['owner']
        distractors = all_scores['owner'][1:6].unique().tolist()
        # Ensure enough distractors
        while len(distractors) < 5:
            random_owner = random.choice(all_owners)
            if random_owner != correct_answer and random_owner not in distractors:
                distractors.append(random_owner)

        trivia_list.append({
            "question_text": f"Who holds the all-time record for the highest single-week score with {top_score['score']:.2f} points?",
            "category": "All-Time Records",
            "correct_answer": correct_answer,
            "distractors": distractors
        })

    # Q2: Biggest Blowout
    merged['margin'] = (merged['home_score'] - merged['away_score']).abs()
    biggest_blowout = merged.sort_values('margin', ascending=False).iloc[0]
    winner = biggest_blowout['home_owner'] if biggest_blowout['home_score'] > biggest_blowout['away_score'] else biggest_blowout['away_owner']
    
    trivia_list.append({
        "question_text": f"What was the largest margin of victory in league history, a whopping {biggest_blowout['margin']:.2f} points?",
        "category": "All-Time Records",
        "correct_answer": f"A victory for {winner}",
        "distractors": [
            f"A victory for {biggest_blowout['away_owner'] if winner == biggest_blowout['home_owner'] else biggest_blowout['home_owner']}", # The loser
            f"{merged.sort_values('margin', ascending=False).iloc[1]['margin']:.2f} points", # 2nd highest margin
            f"{merged.sort_values('margin', ascending=False).iloc[2]['margin']:.2f} points",
            f"{merged.sort_values('margin', ascending=False).iloc[3]['margin']:.2f} points",
            "A tie game"
        ]
    })
    
    return trivia_list

def insert_trivia_into_db(conn, trivia_list):
    """Inserts a list of validated trivia questions and answers into the database."""
    print(f"Validating and inserting new trivia questions...")
    cursor = conn.cursor()
    inserted_count = 0
    for trivia in trivia_list:
        # Validation Step
        if not trivia.get("question_text") or not trivia.get("correct_answer") or len(trivia.get("distractors", [])) < 3:
            print(f"Skipping invalid trivia item: {trivia.get('question_text', 'N/A')}")
            continue

        cursor.execute("INSERT INTO questions (question_text, category) VALUES (?, ?)", (trivia['question_text'], trivia['category']))
        question_id = cursor.lastrowid
        
        cursor.execute("INSERT INTO answers (question_id, answer_text, is_correct) VALUES (?, ?, ?)", (question_id, trivia['correct_answer'], 1))
        
        for d in trivia['distractors']:
            cursor.execute("INSERT INTO answers (question_id, answer_text, is_correct) VALUES (?, ?, ?)", (question_id, d, 0))
        
        inserted_count += 1
    
    conn.commit()
    print(f"Successfully inserted {inserted_count} new trivia questions.")

def main():
    conn = get_db_connection()
    if not conn:
        return

    clear_existing_trivia(conn)
    
    matchups_df = pd.read_sql_query("SELECT * FROM matchups", conn)
    teams_df = pd.read_sql_query("SELECT * FROM teams", conn)
    seasons_df = pd.read_sql_query("SELECT * FROM seasons", conn)
    
    all_trivia = []
    all_trivia.extend(generate_all_time_records_trivia(matchups_df, teams_df))
    all_trivia.extend(generate_season_specific_trivia(matchups_df, teams_df, seasons_df))
    all_trivia.extend(generate_rivalry_trivia(matchups_df, teams_df))
    all_trivia.extend(generate_obscure_stats_trivia(matchups_df, teams_df))
    
    insert_trivia_into_db(conn, all_trivia)
    conn.close()
    print("Trivia generation complete.")

def generate_season_specific_trivia(matchups_df, teams_df, seasons_df):
    """Generates trivia questions about specific seasons."""
    print("Generating 'Season-Specific' trivia...")
    trivia_list = []
    all_owners = teams_df['owner'].unique().tolist()
    
    for year in seasons_df['year'].unique():
        matchups_year = matchups_df[matchups_df['year'] == year]
        teams_year = teams_df[teams_df['year'] == year]
        
        # Q: Who was the runner up in year X?
        playoffs = matchups_year[(matchups_year['is_playoff'] == 1) & (matchups_year['matchup_type'] == 'WINNERS_BRACKET')]
        if not playoffs.empty:
            final_week = playoffs['week'].max()
            final_game = playoffs[playoffs['week'] == final_week].iloc[0]
            winner = final_game['home_team_id'] if final_game['home_score'] > final_game['away_score'] else final_game['away_team_id']
            loser = final_game['away_team_id'] if final_game['home_score'] > final_game['away_score'] else final_game['home_team_id']
            
            winner_owner = teams_year[teams_year['team_id'] == winner].iloc[0]['owner']
            loser_owner = teams_year[teams_year['team_id'] == loser].iloc[0]['owner']

            distractors = [winner_owner]
            semi_final_week = playoffs['week'].unique()[-2]
            semi_finalists = pd.concat([playoffs[playoffs['week']==semi_final_week]['home_team_id'], playoffs[playoffs['week']==semi_final_week]['away_team_id']]).unique()
            semi_final_losers = [team for team in semi_finalists if team not in [winner, loser]]
            for team_id in semi_final_losers:
                 distractors.append(teams_year[teams_year['team_id'] == team_id].iloc[0]['owner'])
            while len(distractors) < 5:
                random_owner = random.choice(all_owners)
                if random_owner not in distractors and random_owner != loser_owner:
                    distractors.append(random_owner)

            trivia_list.append({
                "question_text": f"Who was the runner-up in the {year} championship game?",
                "category": "Season-Specific",
                "correct_answer": loser_owner,
                "distractors": distractors
            })
    return trivia_list

def generate_rivalry_trivia(matchups_df, teams_df):
    """Generates trivia about head-to-head records."""
    print("Generating 'Rivalry' trivia...")
    trivia_list = []
    owners = teams_df['owner'].unique().tolist()
    
    for owner in owners:
        # Get this owner's rivalry matrix
        my_teams = teams_df[teams_df['owner'] == owner]
        all_games = []
        for _, team_row in my_teams.iterrows():
            year, team_id = team_row['year'], team_row['team_id']
            games = matchups_df[(matchups_df['year'] == year) & ((matchups_df['home_team_id'] == team_id) | (matchups_df['away_team_id'] == team_id))]
            for _, g in games.iterrows():
                opp_id = g['away_team_id'] if g['home_team_id'] == team_id else g['home_team_id']
                opp_owner = teams_df[(teams_df['year'] == year) & (teams_df['team_id'] == opp_id)]
                if not opp_owner.empty:
                    all_games.append({'opponent': opp_owner.iloc[0]['owner']})

        if not all_games: continue
        rivals = pd.DataFrame(all_games).groupby('opponent').size().reset_index(name='games_played')
        if rivals.empty: continue
        
        most_played_opponent = rivals.sort_values('games_played', ascending=False).iloc[0]
        
        distractors = rivals.sort_values('games_played', ascending=False)['opponent'][1:6].tolist()
        while len(distractors) < 5:
            random_owner = random.choice(owners)
            if random_owner != most_played_opponent['opponent'] and random_owner not in distractors and random_owner != owner:
                distractors.append(random_owner)
        
        trivia_list.append({
            "question_text": f"Who has {owner} played against more than any other manager in the league's history?",
            "category": "Rivalries",
            "correct_answer": most_played_opponent['opponent'],
            "distractors": distractors
        })
    return trivia_list

def generate_obscure_stats_trivia(matchups_df, teams_df):
    """Generates trivia about weird or obscure stats."""
    print("Generating 'Obscure Stats' trivia...")
    trivia_list = []

    for year in teams_df['year'].unique():
        teams_year = teams_df[teams_df['year'] == year]
        matchups_year = matchups_df[matchups_df['year'] == year]
        reg_season_games = matchups_year[matchups_year['is_playoff'] == 0]
        
        # Standings calc
        standings = {team_id: {'pf': 0} for team_id in teams_year['team_id']}
        for _, game in reg_season_games.iterrows():
            if game['home_team_id'] in standings: standings[game['home_team_id']]['pf'] += game['home_score']
            if game['away_team_id'] in standings: standings[game['away_team_id']]['pf'] += game['away_score']
        
        standings_df = pd.DataFrame.from_dict(standings, orient='index').reset_index().rename(columns={'index': 'team_id'})
        
        # Playoff teams
        playoff_games = matchups_year[(matchups_year['is_playoff'] == 1) & (matchups_year['matchup_type'] == 'WINNERS_BRACKET')]
        if playoff_games.empty: continue
        playoff_teams = pd.concat([playoff_games['home_team_id'], playoff_games['away_team_id']]).unique()
        
        non_playoff_teams_df = standings_df[~standings_df['team_id'].isin(playoff_teams)]
        if non_playoff_teams_df.empty: continue

        highest_pf_non_playoff = non_playoff_teams_df.sort_values('pf', ascending=False).iloc[0]
        team_info = teams_year[teams_year['team_id'] == highest_pf_non_playoff['team_id']].iloc[0]
        correct_answer = team_info['owner']
        
        distractors = []
        playoff_owners = teams_year[teams_year['team_id'].isin(playoff_teams)]['owner'].unique().tolist()
        distractors.extend(playoff_owners[:4]) # Add some playoff managers as distractors
        other_non_playoff_owners = teams_year[teams_year['team_id'].isin(non_playoff_teams_df['team_id'][1:])]['owner'].unique().tolist()
        distractors.extend(other_non_playoff_owners[:2])
        distractors = list(set(distractors)) # remove duplicates
        if correct_answer in distractors: distractors.remove(correct_answer)
        
        trivia_list.append({
            "question_text": f"In {year}, who scored the most points during the regular season but failed to make the playoffs?",
            "category": "Obscure Stats",
            "correct_answer": correct_answer,
            "distractors": distractors[:5]
        })
    return trivia_list


if __name__ == "__main__":
    main()
