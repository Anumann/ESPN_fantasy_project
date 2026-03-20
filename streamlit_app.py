import streamlit as st
import pandas as pd
import altair as alt
import queries
import random

# =================================================================================================
# Page Configuration & Main Title
# =================================================================================================
st.set_page_config(layout="wide", page_title="Fantasy League Legacy")
st.title("Fantasy League Legacy Dashboard")

# =================================================================================================
# Session State Initialization
# =================================================================================================
if 'current_question' not in st.session_state:
    st.session_state.current_question = None
if 'shuffled_answers' not in st.session_state:
    st.session_state.shuffled_answers = []

# =================================================================================================
# Constants & Helpers
# =================================================================================================
COLUMN_NAME_MAP = {
    'year': 'Year', 'team_name': 'Team', 'owner_name': 'Owner', 'record': 'Record',
    'runner_up': 'Runner-Up', 'score': 'Score', 'points_for': 'Points For',
    'games_played': 'Games', 'wins': 'W', 'losses': 'L', 'ties': 'T', 'win_pct': 'Win %',
    'avg_points': 'Avg Pts', 'total_points': 'Total Pts', 'week': 'Week', 'points': 'Points',
    'opponent_points': 'Opp. Points', 'outcome': 'Outcome', 'owner': 'Owner',
    'opponent': 'Opponent', 'opp_score': 'Opp. Score', 'real_record': 'Real Record',
    'real_pct': 'Real %', 'ap_record': 'All-Play Record', 'ap_pct': 'All-Play %',
    'luck_diff': 'Luck Diff', 'team': 'Team', 'total': 'Total Games', 'rank': 'Rank',
    'manager_1': 'Manager 1', 'manager_2': 'Manager 2',
}

def prepare_df_for_display(df):
    df_copy = df.copy()
    for col in df_copy.columns:
        def safe_format(val, col_name):
            if pd.isnull(val): return ""
            try:
                if col_name in ['win_pct', 'real_pct', 'ap_pct']: return f"{float(val):.3f}"
                elif col_name == 'luck_diff': return f"{float(val):+.3f}"
                elif col_name in ['avg_points', 'total_points', 'points', 'opponent_points', 'score', 'opp_score', 'points_for']: return f"{float(val):.2f}"
                return str(val)
            except (ValueError, TypeError): return str(val)
        df_copy[col] = df_copy[col].apply(lambda x: safe_format(x, col))
    return df_copy

# =================================================================================================
# Data Fetching Functions
# =================================================================================================
@st.cache_data
def get_champions_cached(): return queries.get_league_champions()
@st.cache_data
def get_all_time_standings_cached(standings_type): return queries.get_all_time_standings(standings_type)
@st.cache_data
def get_all_owners_cached(): return queries.get_all_owners()
@st.cache_data
def get_rivalry_matrix_cached(owner): return queries.get_rivalry_matrix(owner)
@st.cache_data
def get_luck_metrics_cached(): return queries.get_luck_metrics()
@st.cache_data
def get_owner_profile_cached(owner): return queries.get_owner_profile(owner)
@st.cache_data
def get_all_ties_cached(): return queries.get_all_ties()
@st.cache_data
def get_league_records_cached(): return queries.get_league_records()
@st.cache_data
def get_league_awards_cached(year): return queries.get_league_awards(year)
@st.cache_data
def get_all_season_point_totals_cached(): return queries.get_all_season_point_totals()
@st.cache_data
def get_trivia_categories_cached(): return ["All Categories"] + queries.get_trivia_categories()
def get_random_trivia_question(category=None): return queries.get_random_trivia_question(category)

# =================================================================================================
# Trivia Helper Function
# =================================================================================================
def setup_new_question(category):
    question_data = get_random_trivia_question(category)
    st.session_state.current_question = question_data
    if question_data:
        correct_answer = next((ans for ans in question_data['answers'] if ans['is_correct']), None)
        incorrect_answers = [ans for ans in question_data['answers'] if not ans['is_correct']]
        if correct_answer:
            random.shuffle(incorrect_answers)
            display_answers = [correct_answer] + incorrect_answers[:3]
            random.shuffle(display_answers)
            st.session_state.shuffled_answers = display_answers
        else:
            st.session_state.shuffled_answers = []
    else:
        st.session_state.shuffled_answers = []

# =================================================================================================
# Main App Layout
# =================================================================================================
tabs = st.tabs(["🏆 Champions", "📜 League Records", "🥇 League Awards", "📊 All-Time Records", "⚔️ Rivalries", "🎲 Luck Metrics", "👤 Manager Profiles", "🤝 Ties", "🧠 Trivia"])

with tabs[0]: # Champions
    st.header("League Champions")
    champions_df = get_champions_cached()
    if not champions_df.empty:
        st.dataframe(prepare_df_for_display(champions_df), column_config={col: {"label": COLUMN_NAME_MAP.get(col, col)} for col in champions_df.columns}, hide_index=True)

with tabs[1]: # League Records
    st.header("All-Time League Records")
    records = get_league_records_cached()
    if records:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.subheader("High Scores")
            st.markdown(f"**Highest Score:** `{records['Highest Score']['Points']}`")
            st.caption(f"{records['Highest Score']['Manager']} ({records['Highest Score']['Year']}, Week {records['Highest Score']['Week']})")
            st.markdown(f"**Highest Scoring Matchup:** `{records['Highest Scoring Matchup']['Total Points']}`")
            st.caption(f"{records['Highest Scoring Matchup']['Matchup']} ({records['Highest Scoring Matchup']['Year']}, Week {records['Highest Scoring Matchup']['Week']})")
        with col2:
            st.subheader("Low Scores")
            st.markdown(f"**Lowest Score:** `{records['Lowest Score']['Points']}`")
            st.caption(f"{records['Lowest Score']['Manager']} ({records['Lowest Score']['Year']}, Week {records['Lowest Score']['Week']})")
            st.markdown(f"**Lowest Scoring Matchup:** `{records['Lowest Scoring Matchup']['Total Points']}`")
            st.caption(f"{records['Lowest Scoring Matchup']['Matchup']} ({records['Lowest Scoring Matchup']['Year']}, Week {records['Lowest Scoring Matchup']['Week']})")
        with col3:
            st.subheader("Margins of Victory")
            st.markdown(f"**Biggest Blowout:** `{records['Biggest Blowout']['Margin']}`")
            st.caption(f"{records['Biggest Blowout']['Matchup']} ({records['Biggest Blowout']['Year']}, Week {records['Biggest Blowout']['Week']})")
            st.markdown(f"**Closest Shave:** `{records['Closest Shave']['Margin']}`")
            st.caption(f"{records['Closest Shave']['Matchup']} ({records['Closest Shave']['Year']}, Week {records['Closest Shave']['Week']})")

with tabs[2]: # League Awards
    st.header("Seasonal League Awards")
    all_years = queries.get_all_years()
    selected_year = st.selectbox("Select a Season", options=all_years, key='awards_year_selector')
    if selected_year:
        awards = get_league_awards_cached(selected_year)
        if not awards or not any(awards.values()):
            st.warning(f"Could not retrieve or calculate awards for {selected_year}.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🏆 Top Gun (MVP)")
                top_gun = awards.get("Top Gun", {})
                if top_gun:
                    st.metric(label=f"{top_gun['Manager']} ({top_gun['Team']})", value=top_gun['Total Points'], help="Highest total points in the regular season.")
                else:
                    st.info("Award not calculated.")

                st.subheader("🔪 Boston Scott Giant Killer Award")
                giant_killer = awards.get("Giant Killer", {})
                if giant_killer:
                    st.metric(label=f"{giant_killer['Manager']} ({giant_killer['Team']})", value=giant_killer['Winning Score'], help=f"Lowest score to win a matchup (Week {giant_killer['Week']}).")
                else:
                    st.info("Award not calculated.")

            with col2:
                st.subheader("🐶 The Underdog")
                underdog = awards.get("The Underdog", {})
                if underdog:
                     st.metric(label=f"{underdog['Manager']} ({underdog['Team']})", value=f"#{underdog['Seed']} Seed", help="Lowest seeded team to make the playoffs.")
                else:
                    st.info("Award not calculated.")

                st.subheader("💔 Heartbreak Kid")
                heartbreaks = awards.get("Heartbreak Kid", [])
                if heartbreaks:
                    for hb in heartbreaks:
                        st.markdown(f"**{hb['Manager']} ({hb['Team']})**")
                        st.caption(f"Week {hb['Week']} - Scored {hb['Score']} and lost (Top 3 score).")
                else:
                    st.info("No heartbreaking losses found for this season.")

with tabs[3]: # All-Time Records
    st.header("All-Time Records")
    # ... and so on for all other tabs ...

with tabs[8]: # Trivia
    st.header("League History Trivia")
    trivia_categories = get_trivia_categories_cached()
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_category = st.selectbox("Select a Category", options=trivia_categories)
    with col2:
        if st.button("New Question", width='stretch'):
            setup_new_question(selected_category)
    st.divider()

    if st.session_state.current_question:
        q_data = st.session_state.current_question
        st.subheader(q_data['question_text'])
        st.caption(f"Category: {q_data['category']}")

        with st.form(key='trivia_form'):
            answers_to_display = st.session_state.shuffled_answers
            if not answers_to_display:
                st.error("Could not load trivia question. Please try requesting a new one.")
                st.form_submit_button("Submit Answer", disabled=True)
            else:
                user_choice = st.radio("Choose your answer:", [a['answer_text'] for a in answers_to_display], index=None)
                submitted = st.form_submit_button("Submit Answer")
                if submitted:
                    if user_choice is None:
                        st.warning("Please select an answer.")
                    else:
                        chosen_obj = next((a for a in answers_to_display if a['answer_text'] == user_choice), None)
                        correct_text = next((a['answer_text'] for a in q_data['answers'] if a['is_correct']), "Error")
                        if chosen_obj and chosen_obj['is_correct']:
                            st.success(f"**{user_choice}** is correct!")
                        else:
                            st.error(f"Incorrect. The correct answer was: **{correct_text}**")
    else:
        st.info("Click 'New Question' to start playing!")
