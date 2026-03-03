# playoff_analyzer.py
import sqlite3

DB_NAME = 'fantasy_data.db'

def get_playoff_records():
    """
    Queries the database to calculate the historical playoff records
    for each team owner across all seasons.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    query = """
        WITH playoff_results AS (
            -- Select home team results
            SELECT
                year,
                home_team_id as team_id,
                CASE WHEN home_score > away_score THEN 1 ELSE 0 END as win,
                CASE WHEN home_score < away_score THEN 1 ELSE 0 END as loss,
                CASE WHEN home_score = away_score THEN 1 ELSE 0 END as tie
            FROM matchups
            WHERE is_playoff = 1

            UNION ALL

            -- Select away team results
            SELECT
                year,
                away_team_id as team_id,
                CASE WHEN away_score > home_score THEN 1 ELSE 0 END as win,
                CASE WHEN away_score < home_score THEN 1 ELSE 0 END as loss,
                CASE WHEN away_score = home_score THEN 1 ELSE 0 END as tie
            FROM matchups
            WHERE is_playoff = 1
        )
        -- We GROUP BY the unique owner_id to correctly aggregate records
        -- for owners who may have changed their display name.
        -- We select the most recent owner name for display purposes.
        SELECT
            t.owner_id,
            MAX(t.owner) as display_name,
            SUM(g.win) as total_wins,
            SUM(g.loss) as total_losses,
            SUM(g.tie) as total_ties,
            -- Calculate winning percentage
            CASE
                WHEN (SUM(g.win) + SUM(g.loss)) = 0 THEN 0.0
                ELSE (SUM(g.win) * 1.0 / (SUM(g.win) + SUM(g.loss)))
            END as winning_percentage
        FROM playoff_results g
        JOIN teams t ON g.team_id = t.team_id AND g.year = t.year
        WHERE t.owner_id != 'UNKNOWN_ID'
        GROUP BY t.owner_id
        ORDER BY winning_percentage DESC, total_wins DESC;
    """

    cursor.execute(query)
    records = cursor.fetchall()

    # Second query to find all owners who have never made the playoffs
    no_playoffs_query = """
        SELECT DISTINCT
            t.owner
        FROM teams t
        WHERE t.owner_id NOT IN (
            SELECT DISTINCT
                t2.owner_id
            FROM matchups m
            JOIN teams t2 ON (m.home_team_id = t2.team_id OR m.away_team_id = t2.team_id) AND m.year = t2.year
            WHERE m.is_playoff = 1
        ) AND t.owner_id != 'UNKNOWN_ID'
    """
    cursor.execute(no_playoffs_query)
    no_playoffs_owners = cursor.fetchall()

    conn.close()
    return records, [owner[0] for owner in no_playoffs_owners]

def main():
    """Prints the formatted historical playoff records."""
    records, no_playoffs_owners = get_playoff_records()
    
    if not records:
        print("No playoff records found to analyze.")
        return

    print("--- Career Playoff Records (All-Time) ---")
    print("-" * 65)
    print(f"{'Rank':<5} {'Owner':<25} {'Record (W-L-T)':<18} {'Win %':<10}")
    print("-" * 65)

    target_owner_name = "Johnny Ray  Hinojosa"
    target_record = None

    for i, record in enumerate(records):
        owner_id, display_name, wins, losses, ties, win_pct = record
        rank = i + 1
        record_str = f"{wins}-{losses}-{ties}"
        win_pct_str = f"{win_pct:.3f}"
        
        # Highlight the target owner
        if display_name == target_owner_name:
            target_record = (rank, display_name, record_str, win_pct_str)
            print(f"*{rank:<4} {display_name:<25} {record_str:<18} {win_pct_str:<10}*")
        else:
            print(f" {rank:<4} {display_name:<25} {record_str:<18} {win_pct_str:<10}")
    
    print("-" * 65)

    if no_playoffs_owners:
        print("\nOwners who have never made the playoffs:")
        for owner in no_playoffs_owners:
            print(f"- {owner}")
    
    if target_record:
        print(f"\nJohnny Ray Hinojosa's Corrected Playoff Record:")
        print(f"Rank: {target_record[0]}")
        print(f"Record: {target_record[2]}")
        print(f"Winning Percentage: {target_record[3]}")
    else:
        print(f"\nNo playoff record found for {target_owner_name}.")


if __name__ == '__main__':
    main()
