# Project Plan: Fantasy League Dashboard

**Date:** 2026-03-02
**Timestamp:** 14:28 EST

## 1. Objective

To create a web-based dashboard using Plotly Dash for visualizing the historical data of our ESPN Fantasy Football league. The application will run on port `8051`.

## 2. Inspiration and Key Features

Based on research of existing platforms like `leaguelegacy.io`, the dashboard will be built in phases. Phase 1 will focus on creating a "Historical Record Book" with the following key features:

### 2.1. Proposed Pages and Features (Phase 1)

1.  **Homepage / League Overview:**
    *   A simple landing page displaying a manually curated list of league champions by year.
    *   High-level league statistics (e.g., total points scored all-time).

2.  **All-Time Records Page:**
    *   Clean, filterable data tables for career **Regular Season** and **Playoff** records for all owners.

3.  **Head-to-Head Analysis Page:**
    *   Dropdown menus to select any two managers.
    *   A summary of their all-time win-loss record against each other.
    *   A detailed list of every game they have played against one another, including year, week, and final scores.

4.  **League "Record Book" Page:**
    *   A collection of notable league records, calculated from the database:
        *   **Highest Score (Single Week):** Team, owner, year, score.
        *   **Lowest Score (Single Week):** Team, owner, year, score.
        *   **Biggest Blowout (Single Week):** The matchup with the largest point differential.
        *   **Closest Game (Single Week):** The matchup with the smallest point differential.

## 3. Technical Plan

-   **Framework:** Plotly Dash
-   **Directory Structure:** A new `dashboard/` sub-directory will be created within the main `espn-fantasy-project/` folder.
-   **Core Files:**
    -   `app.py`: Will contain the main application layout, routing, and callbacks.
    -   `queries.py`: A dedicated module to handle all SQL queries to the `fantasy_data.db` database.
-   **Deployment:** The application will be configured to run locally on port `8051`.

This plan provides a clear path to building a valuable and interactive front-end for the data we have collected and validated.
