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
# Custom CSS Injection
# =================================================================================================
center_style = """
<style>
    .stDataFrame [data-testid="stDataFrameData-row"] > div {
        text-align: center;
    }
    .stDataFrame [data-testid="stDataFrameData-row"] > div[data-field="Number"] {
        text-align: center !important;
    }
    /* Force centering for all st.table elements (including the row headers used in Option C) */
    [data-testid="stTable"] th, [data-testid="stTable"] td {
        text-align: center !important;
    }
    .dataframe th, .dataframe td {
        text-align: center !important;
    }
</style>
"""
st.markdown(center_style, unsafe_allow_html=True)


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
                col_lower = str(col_name).lower()
                if col_lower in ['win_pct', 'real_pct', 'ap_pct']: return f"{float(val):.3f}"
                elif col_lower == 'luck_diff': return f"{float(val):+.3f}"
                elif col_lower in ['avg_points', 'total_points', 'points', 'opponent_points', 'score', 'opp_score', 'points_for']: return f"{float(val):.2f}"
                return str(val)
            except (ValueError, TypeError): return str(val)
        df_copy[col] = df_copy[col].apply(lambda x: safe_format(x, col))
        
    # Rename columns here so we don't need column_config later
    df_copy = df_copy.rename(columns=COLUMN_NAME_MAP)
    
    # We use pure Pandas Styler to center everything. 
    # To hide the unwanted numerical index without leaving a blank column, 
    # we dynamically set the first column as the index (Option C).
    # To prevent the KeyError ("Styler.apply and .map are not compatible with non-unique index"),
    # we make the first column's values unique by appending invisible zero-width spaces (\u200b).
    first_col = df_copy.columns[0]
    s = df_copy[first_col].astype(str)
    df_copy[first_col] = s + s.groupby(s).cumcount().map(lambda x: '\u200b' * x)
    
    df_copy = df_copy.set_index(first_col)
    
    styler = df_copy.style.set_properties(**{'text-align': 'center'})
    styler = styler.set_table_styles([dict(selector='th', props=[('text-align', 'center')])])
        
    return styler

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
def get_granular_records_cached(): return queries.get_granular_records()
@st.cache_data
def get_all_season_point_totals_cached(): return queries.get_all_season_point_totals()
@st.cache_data
def get_trivia_categories_cached(): return ["All Categories"] + queries.get_trivia_categories()
@st.cache_data
def get_head_to_head_cached(owner1, owner2): return queries.get_head_to_head(owner1, owner2)
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

with tabs[0]:
    st.header("League Champions")
    champions_df = get_champions_cached()
    if not champions_df.empty:
        st.table(prepare_df_for_display(champions_df))

with tabs[1]:
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

    st.divider()
    
    granular_records = get_granular_records_cached()
    if granular_records and not granular_records['position'].empty:
        st.header("Player Scoring Records")
        
        st.subheader("Highest Scoring Seasons by Position")
        st.info("The most total points scored by a player in a single season (excluding bench/IR points).")
        st.table(prepare_df_for_display(granular_records['position']))
        
        col_draft, col_acq = st.columns(2)
        
        with col_draft:
            st.subheader("Biggest Late-Draft Steals")
            st.info("Highest scoring players drafted in Round 10 or later.")
            st.table(prepare_df_for_display(granular_records['draft']))
            
        with col_acq:
            st.subheader("Best Waiver/Trade Acquisitions")
            st.info("Highest scoring players who were not drafted by the manager that started them.")
            st.table(prepare_df_for_display(granular_records['acquisitions']))

with tabs[2]:
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
                if top_gun: st.metric(label=f"{top_gun['Manager']} ({top_gun['Team']})", value=top_gun['Total Points'], help="Highest total points in the regular season.")
                else: st.info("Award not calculated.")

                st.subheader("🔪 Boston Scott Giant Killer Award")
                giant_killer = awards.get("Giant Killer", {})
                if giant_killer: st.metric(label=f"{giant_killer['Manager']} ({giant_killer['Team']})", value=giant_killer['Winning Score'], help=f"Lowest score to win a matchup (Week {giant_killer['Week']}).")
                else: st.info("Award not calculated.")
            with col2:
                st.subheader("🐶 The Underdog")
                underdog = awards.get("The Underdog", {})
                if underdog: st.metric(label=f"{underdog['Manager']} ({underdog['Team']})", value=f"#{underdog['Seed']} Seed", help="Lowest seeded team to make the playoffs.")
                else: st.info("Award not calculated.")

                st.subheader("💔 Heartbreak Kid")
                heartbreaks = awards.get("Heartbreak Kid", [])
                if heartbreaks:
                    for hb in heartbreaks:
                        st.markdown(f"**{hb['Manager']} ({hb['Team']})**")
                        st.caption(f"Week {hb['Week']} - Scored {hb['Score']} and lost (Top 3 score).")
            st.divider()
            
            # Granular Awards
            col3, col4 = st.columns(2)
            with col3:
                st.subheader("🪑 The Golden Bench")
                bench = awards.get("Golden Bench", {})
                if bench: 
                    st.metric(label=f"{bench['Manager']}", value=bench['Bench Points'], help="Most total points left on the bench.")
                else: st.info("Award not calculated.")
                
                st.subheader("💰 Free Agent of the Year")
                pickup = awards.get("Pickup of the Year", {})
                if pickup: 
                    st.metric(label=f"{pickup['Player']} ({pickup['Manager']})", value=pickup['Points'], help="Highest scoring free agent/trade acquisition.")
                else: st.info("Award not calculated.")

            with col4:
                st.subheader("💎 Draft Steal of the Year")
                steal = awards.get("Draft Steal", {})
                if steal: 
                    st.metric(label=f"{steal['Player']} ({steal['Manager']})", value=steal['Points'], help=f"Drafted in Round {steal.get('Round', '?')}.")
                else: st.info("Award not calculated.")

with tabs[3]:
    st.header("All-Time Records")
    st.subheader("Regular Season")
    reg_season_df = get_all_time_standings_cached('Regular Season')
    if not reg_season_df.empty:
        st.table(prepare_df_for_display(reg_season_df.drop(columns=['owner_id'], errors='ignore')))
    
    st.subheader("Playoffs")
    playoffs_df = get_all_time_standings_cached('Playoffs')
    if not playoffs_df.empty:
        st.table(prepare_df_for_display(playoffs_df.drop(columns=['owner_id'], errors='ignore')))

with tabs[4]:
    st.header("Interactive Rivalry Matrix")
    st.info("Select two managers to visualize their head-to-head history.")
    owners_list = sorted(get_all_owners_cached())
    
    col1, col2 = st.columns(2)
    with col1:
        owner_a = st.selectbox("Manager A:", options=owners_list, index=None, placeholder="Select first manager", key='rivalry_improved_owner1')
    
    with col2:
        if owner_a:
            opponents = [o for o in owners_list if o != owner_a]
            owner_b = st.selectbox("Manager B:", options=opponents, index=None, placeholder="Select opponent", key='rivalry_improved_owner2')
        else:
            owner_b = st.selectbox("Manager B:", options=[], index=None, placeholder="Select Manager A first", disabled=True, key='rivalry_improved_owner2_disabled')

    if owner_a and owner_b:
        h2h_df = get_head_to_head_cached(owner_a, owner_b)
        if h2h_df.empty:
            st.warning(f"{owner_a} and {owner_b} have never played against each other.")
        else:
            chart_df = h2h_df.copy()
            # Sort chronologically (oldest to newest)
            chart_df = chart_df.sort_values(['year', 'week'], ascending=True)
            chart_df['differential'] = chart_df['points'] - chart_df['opponent_points']
            chart_df['matchup_label'] = chart_df['year'].astype(str) + " Wk " + chart_df['week'].astype(str)
            
            # Dynamic diverging color scale based on max differential
            max_diff = float(chart_df['differential'].abs().max())
            if max_diff == 0: max_diff = 1.0 # Prevent scale issues if all ties
            
            color_scale = alt.Scale(
                domain=[-max_diff, 0, max_diff],
                range=['#d62728', '#e0e0e0', '#2ca02c']  # Red to Gray to Green
            )

            st.subheader(f"{owner_a} vs {owner_b} Matchup History")
            
            bar_chart = alt.Chart(chart_df).mark_bar().encode(
                x=alt.X('matchup_label:O', sort=None, title='Matchup (Chronological)', axis=alt.Axis(labelAngle=-45)),
                y=alt.Y('differential:Q', title=f'Point Differential ({owner_a} perspective)'),
                color=alt.Color('differential:Q', scale=color_scale, legend=alt.Legend(title="Point Differential")),
                tooltip=[
                    alt.Tooltip('year', title='Year'),
                    alt.Tooltip('week', title='Week'),
                    alt.Tooltip('points', title=f"{owner_a} Points"),
                    alt.Tooltip('opponent_points', title=f"{owner_b} Points"),
                    alt.Tooltip('differential', title='Differential', format='+.2f'),
                    alt.Tooltip('outcome', title='Outcome')
                ]
            ).properties(height=400)
            
            rule = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(color='gray', strokeDash=[4,4]).encode(y='y')
            
            st.altair_chart(bar_chart + rule, use_container_width=True)
            
            wins = len(chart_df[chart_df['outcome'] == 'WIN'])
            losses = len(chart_df[chart_df['outcome'] == 'LOSS'])
            ties = len(chart_df[chart_df['outcome'] == 'TIE'])
            
            st.markdown(f"**Overall Record for {owner_a} vs {owner_b}:** {wins}-{losses}-{ties}")
            
            with st.expander("View Raw Matchup Data"):
                st.table(prepare_df_for_display(h2h_df))


with tabs[5]:
    st.header("Luck Metrics")
    st.info("Luck Diff = (Real Win % - All-Play Win %). A negative score means bad luck.")
    metrics = get_luck_metrics_cached()
    if not metrics: st.warning("Luck metrics could not be calculated.")
    else:
        st.subheader("All-Play vs. Real Records")
        st.table(prepare_df_for_display(metrics['all_play']))
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Heartbreak Index (Top Losses)")
            st.table(prepare_df_for_display(metrics['heartbreak']))
        with col2:
            st.subheader("Lucky Duck Index (Top Wins)")
            st.table(prepare_df_for_display(metrics['lucky_duck']))

with tabs[6]:
    st.header("Manager Profile")
    owners = sorted(get_all_owners_cached())
    selected_owner = st.selectbox("Select a Manager", options=owners, index=None, placeholder="Choose a manager", key='manager_select')
    if selected_owner:
        profile_data = get_owner_profile_cached(selected_owner)
        if not profile_data: st.warning(f"No profile data found for {selected_owner}.")
        else:
            career_stats = profile_data['career']
            st.subheader(f"Career Stats for {selected_owner}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Wins", career_stats['wins'])
            c2.metric("Losses", career_stats['losses'])
            c3.metric("Win %", f"{career_stats['win_pct']:.3f}")
            c4.metric("Total Points", f"{career_stats['points']:.2f}")

            season_log = profile_data['season_log'].copy()
            season_log['year'] = season_log.apply(lambda row: f"{row['year']} 🏆" if row['is_champion'] else str(row['year']), axis=1)
            rivalries_df = profile_data['rivalries']

            scol1, scol2 = st.columns(2)
            with scol1:
                st.subheader("Season History")
                df_log = season_log[['year', 'team', 'record', 'points']]
                st.table(prepare_df_for_display(df_log))
            with scol2:
                st.subheader("Rivalry Matrix (Min. 3 Games)")
                st.table(prepare_df_for_display(rivalries_df))

            st.subheader("Performance Charts")
            all_points_df = get_all_season_point_totals_cached()
            min_points = all_points_df['total_points'].min()
            max_points = all_points_df['total_points'].max()

            chart_df = season_log.copy()
            chart_df['year'] = chart_df['year'].astype(str)

            points_chart_base = alt.Chart(chart_df).mark_bar().encode(
                x=alt.X('year', title='Year', sort=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y('points', title='Total Points For'),
                color=alt.Color('points', title="Points", scale=alt.Scale(domain=[min_points, max_points], range=["#4393c3", "#d6604d"])),
                tooltip=['year', 'points', 'team']
            )

            flame_accent = alt.Chart(chart_df).mark_text(
                align='center',
                baseline='middle',
                fontSize=30,
                dy=15
            ).encode(
                x=alt.X('year:N', sort=None),
                y='points:Q',
                text=alt.value('🔥🔥🔥')
            ).transform_filter('datum.points > 2000')

            final_points_chart = (points_chart_base + flame_accent).properties(title='Points Per Season')
            st.altair_chart(final_points_chart, width='stretch')

            rank_chart = alt.Chart(chart_df).mark_line(point=True).encode(
                x=alt.X('year', title='Year', sort=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y('rank', title='Regular Season Rank', scale=alt.Scale(reverse=True, zero=False)),
                tooltip=['year', 'rank', 'record']
            ).properties(title='Rank Per Season')
            st.altair_chart(rank_chart, width='stretch')

with tabs[7]:
    st.header("Tied Matchups")
    ties_df = get_all_ties_cached()
    if not ties_df.empty:
        st.table(prepare_df_for_display(ties_df))
    else:
        st.info("No tied matchups found.")

with tabs[8]:
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

