# System Deployment Plan: ESPN Fantasy Dashboard
**Timestamp:** 2026-03-03 14:22 EST
**Status:** Planning Phase

This document outlines the agreed-upon plan to deploy the existing Dash-based fantasy football dashboard to a live, cloud-hosted, auto-updating environment.

---

### 1. System Architecture

The project will consist of four key components working together:

*   **Application Framework:** The existing **Dash** application will serve as the user interface.
*   **Hosting Platform:** **Render** will be the all-in-one cloud provider to host all necessary services.
*   **Database:** A **PostgreSQL** database hosted on Render will serve as the persistent, live "production" datastore.
*   **Version Control & CI/CD:** A **GitHub** repository will store the codebase and act as the trigger for automated deployments to Render.

---

### 2. The Role of GitHub

A private GitHub repository will be the central source of truth for our code. Its role is twofold:
1.  **Version Control:** Provides a complete history of all code changes.
2.  **Deployment Trigger:** It connects directly to Render. Any `git push` to the main branch will automatically trigger a new deployment of the application, creating a seamless "push-to-deploy" workflow.

---

### 3. Step-by-Step Deployment Plan

#### Phase 1: Code & Repository Preparation (Local)

1.  **Initialize GitHub Repository:** Create a new private repository on GitHub and push the current `espn-fantasy-project` codebase to it.
2.  **Create `requirements.txt`:** Generate a `requirements.txt` file listing all Python dependencies (e.g., `dash`, `pandas`, `gunicorn`, `psycopg2-binary`) to ensure Render builds the correct environment.
3.  **Database Migration:**
    *   Modify all scripts (`dashboard/queries.py`, `data_extractor.py`) to connect to and query a PostgreSQL database instead of the local `fantasy_data.db` (SQLite) file.
    *   Write a one-time utility script to migrate all historical data from the local SQLite database into the new Render PostgreSQL database.
4.  **Add Production Web Server:** Add `gunicorn` to `requirements.txt` and create a startup configuration that Render can use to launch the Dash app in a production-ready manner.

#### Phase 2: Render Platform Setup

5.  **Provision Services on Render:** In the Render dashboard, create three services linked to the GitHub repository:
    *   **PostgreSQL Database:** The live production database. We will store its connection credentials securely as environment variables.
    *   **Web Service:** The service that will run the Dash application. It will be configured to use the `gunicorn` start command and will be linked to the PostgreSQL database via the environment variables.
    *   **Cron Job:** A scheduled task that will run the `data_extractor.py` script on a recurring basis (e.g., weekly) to keep the production database updated with the latest league data.

#### Phase 3: Go-Live & Future Updates

6.  **Initial Deployment:** After the services are configured, Render will perform the first deployment from the GitHub repository. We will monitor the logs to verify a successful launch.
7.  **Ongoing Updates:** All future updates will follow the "push-to-deploy" workflow:
    *   Make code changes locally.
    *   Commit and push the changes to GitHub.
    *   Render will automatically detect the push, rebuild the application, and deploy the new version, typically with zero downtime.

---
This plan will result in a robust, secure, and self-updating version of the fantasy dashboard accessible from a public URL.
