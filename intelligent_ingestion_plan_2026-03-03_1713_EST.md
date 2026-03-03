# Plan: Intelligent Data Ingestion and Merging Pipeline
**Timestamp:** 2026-03-03 17:13 EST
**Objective:** Create a fully automated, scalable pipeline to populate the PostgreSQL database. This pipeline will re-fetch all historical data from the ESPN API and include logic to intelligently merge owner names that are similar but not identical, preserving the intent of previous manual data curation.

---

### Phase 1: Develop Name-Merging Module

1.  **Goal:** Create a standalone Python script (`name_merger.py`) to identify and map similar owner names.
2.  **Process:**
    *   The script will first pull a raw list of all unique owner names across all historical seasons directly from the ESPN API.
    *   It will then use a fuzzy string matching algorithm (e.g., Levenshtein distance or a similar library like `thefuzz`) to compare each name against all others.
    *   When two or more names are found to be above a certain similarity threshold (e.g., 90% similar), they will be flagged as a potential match.
    *   The script will generate a definitive mapping file (e.g., `owner_map.json`) that maps variant names to a single, canonical name (e.g., `{"Bob Avery Smith": "Bob Smith"}`). This file can be reviewed or edited manually if needed.

### Phase 2: Integrate into Data Extractor

1.  **Goal:** Enhance the existing `data_extractor.py` to use the name-merging logic.
2.  **Process:**
    *   The script will be modified to load the `owner_map.json` file at runtime.
    *   As it processes team data from the API, it will check if the owner's name exists as a key in the mapping.
    *   If a match is found, it will replace the variant name with the canonical name from the map before inserting the data into the database.
    *   This ensures that all data entering the database is pre-cleaned and consistent.

### Phase 3: Execute Full Historical Backfill

1.  **Goal:** Populate the Render PostgreSQL database with the complete, clean historical data.
2.  **Process:**
    *   The existing `historical_backfill.py` script will be used to execute the enhanced `data_extractor.py` for every year of the league's existence, from the most recent season backwards.
    *   This process will be run via a **Render Cron Job**. A Cron Job provides a stable, managed, and fully automated server environment, which is the industry standard for this type of task and will bypass the issues encountered in the local execution environment.
    *   The Cron Job will be configured in the Render dashboard and triggered once to perform the complete backfill.

This plan results in a robust, automated data pipeline that solves the core data integrity problem in a scalable way.
