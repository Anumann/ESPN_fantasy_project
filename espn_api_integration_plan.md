# Implementation Plan: ESPN API Granular Data Integration

## Objective
To enrich the existing `fantasy_data.db` database with granular, player-level data extracted from the ESPN Fantasy API. This includes historical draft results, weekly team rosters, and individual player scores for every matchup.

The architecture will employ a **Single Database Approach** to maintain relational integrity, allowing complex queries that span from a manager's draft strategy directly to their weekly matchup outcomes, while utilizing existing aliases and cleanup logic (e.g., merging "Tati" to "Tatiana").

---

## Phase 1: Database Schema Design & Migration

We will add new tables to the existing `fantasy_data.db` without altering the current `teams`, `matchups`, or `seasons` tables. This guarantees zero disruption to the active Streamlit dashboard.

### Proposed Tables

**1. `players` (Optional but Recommended)**
A master list of NFL players. This normalizes the data, preventing us from storing the string "Christian McCaffrey" 15,000 times.
*   `player_id` (INTEGER, PRIMARY KEY) - ESPN's native player ID.
*   `name` (TEXT)
*   `default_position` (TEXT) - e.g., 'RB', 'WR'

**2. `draft_picks`**
Logs every draft selection made in league history.
*   `pick_id` (INTEGER, PRIMARY KEY AUTOINCREMENT)
*   `year` (INTEGER) - Foreign Key to `seasons(year)`
*   `team_id` (INTEGER) - Foreign Key to `teams(team_id)`
*   `player_id` (INTEGER) - Foreign Key to `players(player_id)`
*   `round_num` (INTEGER)
*   `pick_num` (INTEGER) - Overall pick number
*   `keeper_status` (BOOLEAN) - If applicable to the league settings.

**3. `weekly_rosters`**
Logs every player's score and roster slot for every team, every week.
*   `roster_entry_id` (INTEGER, PRIMARY KEY AUTOINCREMENT)
*   `year` (INTEGER)
*   `week` (INTEGER)
*   `team_id` (INTEGER)
*   `player_id` (INTEGER)
*   `lineup_slot` (TEXT) - e.g., 'QB', 'RB', 'WR', 'FLEX', 'BENCH', 'IR'
*   `projected_points` (REAL)
*   `actual_points` (REAL)
*   *Foreign Keys:* `(team_id, year)` -> `teams(team_id, year)`

---

## Phase 2: Data Extraction Strategy (ESPN API)

The ESPN Fantasy API is notoriously undocumented. We will build a dedicated extraction script (`espn_api_extractor.py`) to handle the nuances of pulling historical data.

1.  **Authentication:**
    *   If the league has ever been private, the script must handle `swid` and `espn_s2` cookies to authenticate requests. These should be stored in the `.env` file or a secrets manager.
2.  **Endpoint Mapping:**
    *   **Draft Data:** `https://fantasy.espn.com/apis/v3/games/ffl/leagueHistory/{league_id}?seasonId={year}&view=mDraftDetail`
    *   **Roster/Scoring Data:** `https://fantasy.espn.com/apis/v3/games/ffl/leagueHistory/{league_id}?seasonId={year}&view=mMatchupScore` or `view=mRoster`
3.  **Historical vs. Current API Quirk:**
    *   ESPN uses a different endpoint structure for the *current* active year versus historical years (`leagueHistory`). The extractor must intelligently route requests based on the requested year.

---

## Phase 3: Data Transformation & Cleansing (The "Tatiana" Problem)

This is where the single-database architecture shines. 

When pulling data from the ESPN API, historical teams often have outdated or inconsistent owner names.

1.  **Intercepting the Team ID:** The ESPN API primarily relies on `teamId` (an integer from 1 to 14).
2.  **Mapping to the Source of Truth:**
    *   Before inserting any draft pick or roster slot, the script will look up the `team_id` and `year` in our existing `teams` table.
    *   If the ESPN API says "Tati" drafted Patrick Mahomes in 2018 (Team ID 4), our script maps Team ID 4 in 2018 directly to the `owner_id` for "Tatiana" via the existing `teams` and `owners` architecture.
    *   **Result:** The raw string "Tati" from the API is completely discarded. The draft pick is relationaly bound to "Tatiana".

---

## Phase 4: Execution Plan & Safety Protocols

1.  **Backup the Core:** Create a physical copy of the database (`fantasy_data_backup_pre_espn.db`).
2.  **Create the Schema:** Run a SQL script to instantiate the `players`, `draft_picks`, and `weekly_rosters` tables.
3.  **Iterative Ingestion:**
    *   Do not ingest the entire decade at once.
    *   Run the script for a single, recent year (e.g., 2023).
    *   Verify the data.
4.  **Verification Check (The Math Test):**
    *   Write a SQL query that sums the `actual_points` for all players in `weekly_rosters` where the `lineup_slot` is NOT 'BENCH' or 'IR' for a specific team/week.
    *   Compare that sum against the existing `home_score` or `away_score` in the `matchups` table.
    *   If they match (or are within 0.1 points due to floating-point rounding), the ingestion logic is flawless.

---

## Phase 5: Dashboard Integration (Future State)

Once the data is verified, the Streamlit dashboard can be upgraded with new tabs and metrics:

*   **Draft Analysis:** Who has the best historical draft value? Which manager drafts the most busts?
*   **Bench Points:** Who leaves the most points on their bench? (The "Over-thinker" metric).
*   **Positional Dominance:** Which manager historically drafts/fields the highest-scoring Running Backs?
*   **Optimal Lineup:** Comparing a manager's actual score vs. their "Optimal" score if they had started their highest-scoring bench players.
