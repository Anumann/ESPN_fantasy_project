# query_analyzer.py
import sqlite3

DB_NAME = 'fantasy_data.db'

def get_historical_records():
    """
    Queries the database to calculate the historical regular season records
    for each team owner across all seasons.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # This SQL query is a bit complex. Here's the breakdown:
    # 1. We create a temporary table `game_results` that lists every single regular season game from the perspective of each participant.
    # 2. It calculates a "win", "loss", or "tie" for each game played by each team.
    # 3. We then JOIN this with the `teams` table to link each game to an owner.
    # 4. Finally, we GROUP BY the owner's name and SUM their wins, losses, and ties to get a career record.
    # 5. The results are ordered by winning percentage (descending).
    query = """
        WITH game_results AS (
            -- Select home team results
            SELECT
                year,
                home_team_id as team_id,
                CASE WHEN home_score > away_score THEN 1 ELSE 0 END as win,
                CASE WHEN home_score < away_score THEN 1 ELSE 0 END as loss,
                CASE WHEN home_score = away_score THEN 1 ELSE 0 END as tie
            FROM matchups
            WHERE is_playoff = 0

            UNION ALL

            -- Select away team results
            SELECT
                year,
                away_team_id as team_id,
                CASE WHEN away_score > home_score THEN 1 ELSE 0 END as win,
                CASE WHEN away_score < home_score THEN 1 ELSE 0 END as loss,
                CASE WHEN away_score = home_score THEN 1 ELSE 0 END as tie
            FROM matchups
            WHERE is_playoff = 0
        )
        SELECT
            t.owner,
            SUM(g.win) as total_wins,
            SUM(g.loss) as total_losses,
            SUM(g.tie) as total_ties,
            -- Calculate winning percentage, handling division by zero
            CASE
                WHEN (SUM(g.win) + SUM(g.loss)) = 0 THEN 0.0
                ELSE (SUM(g.win) * 1.0 / (SUM(g.win) + SUM(g.loss)))
            END as winning_percentage
        FROM game_results g
        JOIN teams t ON g.team_id = t.team_id AND g.year = t.year
        GROUP BY t.owner
        ORDER BY winning_percentage DESC;
    """

    cursor.execute(query)
    records = cursor.fetchall()
    conn.close()
    return records

def main():
    """Prints the formatted historical records."""
    records = get_historical_records()
    
    if not records:
        print("No records found to analyze.")
        return

    print("--- Career Regular Season Records (All-Time) ---")
    print("-" * 65)
    print(f"{'Rank':<5} {'Owner':<25} {'Record (W-L-T)':<18} {'Win %':<10}")
    print("-" * 65)

    for i, record in enumerate(records):
        owner, wins, losses, ties, win_pct = record
        rank = i + 1
        record_str = f"{wins}-{losses}-{ties}"
        win_pct_str = f"{win_pct:.3f}"
        print(f"{rank:<5} {owner:<25} {record_str:<18} {win_pct_str:<10}")
    
    print("-" * 65)
    print("\nBest Record: ", records[0][0])
    print("Worst Record:", records[-1][0])


if __name__ == '__main__':
    main()
