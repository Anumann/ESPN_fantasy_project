import sqlite3

def verify_data(year):
    conn = sqlite3.connect('fantasy_data.db')
    cursor = conn.cursor()

    # Get a few matchups from the main database
    cursor.execute('''
        SELECT m.matchup_id, m.week, m.home_team_id, m.home_score, m.away_team_id, m.away_score
        FROM matchups m
        WHERE m.year = ? AND m.week = 1 LIMIT 3
    ''', (year,))
    
    matchups = cursor.fetchall()
    
    for m in matchups:
        matchup_id, week, home_team_id, home_score, away_team_id, away_score = m
        
        # Calculate Home Score from granular data
        cursor.execute('''
            SELECT SUM(actual_points) FROM weekly_rosters 
            WHERE year = ? AND week = ? AND team_id = ? AND lineup_slot NOT IN ('BE', 'IR')
        ''', (year, week, home_team_id))
        
        calc_home_score = cursor.fetchone()[0] or 0.0
        
        print(f"Matchup {matchup_id} (Week {week}) - Team {home_team_id}")
        print(f"  Main DB Score:  {home_score:.2f}")
        print(f"  Granular Sum:   {calc_home_score:.2f}")
        diff = abs(home_score - calc_home_score)
        print(f"  Diff:           {diff:.2f}")
        if diff > 0.1:
            print("  ❌ MISMATCH DETECTED")
        else:
            print("  ✅ MATCH")

    conn.close()

if __name__ == '__main__':
    verify_data(2023)
