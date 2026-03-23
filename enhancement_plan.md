# Enhancement Plan: Fantasy Dashboard

This document outlines the planning for new features and improvements for the Fantasy Football History Dashboard.

## 1. ESPN API Capabilities

The `espn-api` library provides access to a wide range of data points from the ESPN Fantasy API. Based on the documentation and community usage, we can reliably access the following information for a given league and year:

- **League Info**: Settings, number of teams, season records.
- **Team Info**: Roster, owner information, team name, logo, record.
- **Scores & Matchups**: Weekly scores, box scores, and historical matchups.
- **Players**: Detailed player information, stats for the week and season, position, and pro team.
- **Weekly Lineups**: The specific players that were in a team's starting lineup versus on their bench for any given week.
- **Draft Details**: The full results of the league's draft, including player selected, pick number, and drafting team.
- **Free Agents/Waivers**: Information about players on the waiver wire or in the free agent pool.

This rich dataset confirms that the proposed feature enhancements are feasible.

---

## 2. New Feature: Interactive Rivalry Chart

**Goal:** Replace the static head-to-head table in the "Rivalries" tab with a more engaging, interactive chart.

**Plan:**
1.  **Data Source:** Continue to use the `get_rivalry_matrix()` function in `queries.py` as the primary data source, as it already calculates the necessary win/loss records. We may need a supplemental function, `get_head_to_head_history(owner1, owner2)`, to fetch the chronological matchup scores.
2.  **Visualization:**
    *   On the Rivalries tab, after a user selects two managers to compare, display a chart in addition to the summary table.
    *   Use the **Altair** library (already in the project) to create a combination bar and line chart.
    *   The **X-axis** will represent the timeline of their matchups (e.g., "2022 Week 5", "2023 Week 12").
    *   The **Y-axis** will show the point differential. A **bar chart** will show the margin of victory for each game (e.g., green bar if Manager 1 won, red if Manager 2 won).
    *   A **line chart** can be overlaid to show the running total of wins for each manager over their history.
3.  **User Interface:** The user will select a primary manager from the main dropdown. A second dropdown will then be populated with their rivals to create the head-to-head chart.

---

## 3. New Feature: Weekly Power Rankings

**Goal:** Create a new "Power Rankings" tab to visualize how teams stacked up against each other on a weekly basis throughout a season.

**Plan:**
1.  **Methodology:** Develop a "Power Score" formula. A simple but effective starting point would be a weighted score:
    *   `Power Score = (Total Points * 0.6) + (Avg Score * 0.3) + (Win-Loss Differential * 0.1)`
    *   This formula will be calculated cumulatively for each week of the regular season.
2.  **Backend (`queries.py`):**
    *   Create a new function: `calculate_weekly_power_rankings(year)`.
    *   This function will iterate through each week of the given season, calculate the Power Score for every team based on their performance up to that week, and rank them from 1 to N.
    *   The function will return a pandas DataFrame containing `[year, week, team_name, owner, power_score, rank]`.
3.  **Frontend (`streamlit_app.py`):**
    *   Add a new "Power Rankings" tab.
    *   Include dropdowns for selecting the **Season**.
    *   Use an **Altair line chart** to plot the rankings. Each team will be a different colored line, the X-axis will be the week number, and the Y-axis will be their rank. This will create a dynamic chart showing teams rising and falling throughout the season.

---

## 4. Technical Improvement: Query Refactoring

**Goal:** Improve dashboard performance and code maintainability by shifting complex data processing from Python/Pandas to the SQL database layer.

**Plan:**
1.  **Identify Targets:** Prioritize the most complex and slowest-loading functions for refactoring. Good candidates are `get_luck_metrics()` and `get_owner_profile()`.
2.  **Example Refactor (`get_luck_metrics`):**
    *   **Current Method:** Fetches all matchups and all teams into pandas DataFrames, then uses multiple merges, filters, and loops in Python to calculate "All-Play" records.
    *   **Proposed SQL Method:** Write a more advanced SQL query using Common Table Expressions (CTEs) and window functions.
        *   A first CTE can create a simple `all_scores_for_week` table.
        *   A subsequent query can join this CTE against itself to compare every manager's score to every other score in the same week, calculating all-play wins/losses directly in the database.
    *   **Benefit:** The database is highly optimized for these types of set-based operations. This will significantly reduce the amount of data transferred to the application and leverage the database engine's power, resulting in a faster page load.
3.  **Action:** A dedicated effort will be made to audit `queries.py` and incrementally convert pandas-heavy logic into more direct and efficient SQL queries.

---

## 5. Feature Expansion: Trivia Module

**Goal:** Significantly expand the trivia question database by programmatically generating questions from historical data, making the game more engaging and replayable.

**Plan:**
1.  **Create a Generator Script:** Develop a new standalone script, `trivia_generator.py`.
2.  **Question Templates:** Define a series of templates for generating questions, such as:
    *   **High/Low Scores:** "Who had the highest score in Week {week} of {year}?"
    *   **Championships:** "Who did {champion_owner} defeat in the {year} championship?"
    *   **Rivalries:** "What is {owner1}'s all-time regular season record against {owner2}?"
    *   **Records:** "Which manager holds the record for the biggest blowout victory?"
3.  **Implementation:**
    *   The `trivia_generator.py` script will connect to the `fantasy_data.db`.
    *   It will execute SQL queries based on the templates above to get the correct answer and generate plausible incorrect answers (e.g., for a "highest score" question, the incorrect answers could be the 2nd, 3rd, and 4th highest scores of that week).
    *   The script will then insert these new questions and answers into the `questions` and `answers` tables.
    *   This script can be run once to populate the database with hundreds of new questions, and can be re-run in the future to add more as new seasons are added.
