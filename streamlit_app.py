import streamlit as st
import pandas as pd
import queries

# =================================================================================================
# Page Configuration & Main Title
# =================================================================================================
st.set_page_config(layout="wide", page_title="Fantasy League Legacy")

st.title("Fantasy League Legacy Dashboard")

# =================================================================================================
# Constants
# =================================================================================================
COLUMN_NAME_MAP = {
    'year': 'Year', 'team_name': 'Team', 'owner_name': 'Owner', 'record': 'Record',
    'runner_up': 'Runner-Up', 'score': 'Final Score', 'points_for': 'Points For',
    'games_played': 'Games', 'wins': 'W', 'losses': 'L', 'ties': 'T', 'win_pct': 'Win %',
    'avg_points': 'Avg Pts', 'total_points': 'Total Pts', 'week': 'Week', 'points': 'Points',
    'opponent_points': 'Opp. Points', 'outcome': 'Outcome', 'owner': 'Owner',
    'opponent': 'Opponent', 'opp_score': 'Opp. Score', 'real_record': 'Real Record',
    'real_pct': 'Real %', 'ap_record': 'All-Play Record', 'ap_pct': 'All-Play %',
    'luck_diff': 'Luck Diff', 'team': 'Team', 'total': 'Total Games',
}

# =================================================================================================
# Data Fetching (with Caching)
# =================================================================================================
@st.cache_data
def get_champions_cached():
    return queries.get_league_champions()

@st.cache_data
def get_all_time_standings_cached(standings_type):
    return queries.get_all_time_standings(standings_type)

@st.cache_data
def get_all_owners_cached():
    return queries.get_all_owners()

@st.cache_data
def get_h2h_cached(o1, o2):
    return queries.get_head_to_head(o1, o2)

@st.cache_data
def get_luck_metrics_cached():
    return queries.get_luck_metrics()

@st.cache_data
def get_owner_profile_cached(owner):
    return queries.get_owner_profile(owner)

# =================================================================================================
# Navigation Tabs
# =================================================================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 Champions", "📊 All-Time Records", "⚔️ Head-to-Head",
    "🎲 Luck Metrics", "👤 Manager Profiles"
])

# =================================================================================================
# Tab 1: Champions
# =================================================================================================
with tab1:
    st.header("League Champions")
    champions_df = get_champions_cached()
    if not champions_df.empty:
        # Convert problematic numeric columns to strings to enforce center alignment
        champions_df['year'] = champions_df['year'].astype(str)
        champions_df['points_for'] = champions_df['points_for'].astype(str)

        st.dataframe(
            champions_df,
            column_config={col: {"label": COLUMN_NAME_MAP.get(col, col), "alignment": "center"} for col in champions_df.columns},
            hide_index=True, use_container_width=True
        )

# =================================================================================================
# Tab 2: All-Time Records
# =================================================================================================
with tab2:
    st.header("All-Time Records")
    
    st.subheader("Regular Season")
    reg_season_df = get_all_time_standings_cached('Regular Season')
    if not reg_season_df.empty:
        df = reg_season_df.drop(columns=['owner_id'], errors='ignore')
        st.dataframe(
            df.style.format({"win_pct": "{:.3f}", "avg_points": "{:.2f}", "total_points": "{:.2f}"}),
            column_config={col: {"label": COLUMN_NAME_MAP.get(col, col), "alignment": "center"} for col in df.columns},
            hide_index=True, use_container_width=True
        )

    st.subheader("Playoffs")
    playoffs_df = get_all_time_standings_cached('Playoffs')
    if not playoffs_df.empty:
        df = playoffs_df.drop(columns=['owner_id'], errors='ignore')
        st.dataframe(
            df.style.format({"win_pct": "{:.3f}", "avg_points": "{:.2f}", "total_points": "{:.2f}"}),
            column_config={col: {"label": COLUMN_NAME_MAP.get(col, col), "alignment": "center"} for col in df.columns},
            hide_index=True, use_container_width=True
        )

# =================================================================================================
# Tab 3: Head-to-Head
# =================================================================================================
with tab3:
    st.header("Head-to-Head Analysis")
    owners = sorted(get_all_owners_cached())
    
    col1, col2 = st.columns(2)
    with col1:
        owner1 = st.selectbox("Select Owner 1", options=owners, index=None, placeholder="Choose an owner")
    with col2:
        owner2 = st.selectbox("Select Owner 2", options=owners, index=None, placeholder="Choose an owner")

    if owner1 and owner2:
        if owner1 == owner2:
            st.warning("Please select two different owners.")
        else:
            h2h_df = get_h2h_cached(owner1, owner2)
            if h2h_df.empty:
                st.info(f"No match history found between {owner1} and {owner2}.")
            else:
                wins = len(h2h_df[h2h_df['outcome'] == 'WIN'])
                losses = len(h2h_df[h2h_df['outcome'] == 'LOSS'])
                ties = len(h2h_df[h2h_df['outcome'] == 'TIE'])
                
                if wins > losses: st.subheader(f"Record: {owner1} leads {wins}-{losses}-{ties}")
                elif losses > wins: st.subheader(f"Record: {owner2} leads {losses}-{wins}-{ties}")
                else: st.subheader(f"Record: Tied {wins}-{losses}-{ties}")
                
                st.dataframe(
                    h2h_df.style.format({"points": "{:.2f}", "opponent_points": "{:.2f}"}),
                    column_config={col: {"label": COLUMN_NAME_MAP.get(col, col), "alignment": "center"} for col in h2h_df.columns},
                    hide_index=True, use_container_width=True
                )

# =================================================================================================
# Tab 4: Luck Metrics
# =================================================================================================
with tab4:
    st.header("Luck Metrics")
    st.info("Luck Diff = (Real Win % - All-Play Win %). A negative score means bad luck.")
    
    metrics = get_luck_metrics_cached()
    if not metrics:
        st.warning("Luck metrics could not be calculated.")
    else:
        st.subheader("All-Play vs. Real Records")
        all_play_df = metrics['all_play']
        st.dataframe(
            all_play_df.style.format({'real_pct': '{:.3f}', 'ap_pct': '{:.3f}', 'luck_diff': '{:+.3f}'}),
            column_config={col: {"label": COLUMN_NAME_MAP.get(col, col), "alignment": "center"} for col in all_play_df.columns},
            hide_index=True, use_container_width=True
        )

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Heartbreak Index (Top Losses)")
            heartbreak_df = metrics['heartbreak']
            st.dataframe(
                heartbreak_df.style.format({"score": "{:.2f}", "opp_score": "{:.2f}"}),
                column_config={col: {"label": COLUMN_NAME_MAP.get(col, col), "alignment": "center"} for col in heartbreak_df.columns},
                hide_index=True, use_container_width=True
            )
        with col2:
            st.subheader("Lucky Duck Index (Top Wins)")
            lucky_duck_df = metrics['lucky_duck']
            st.dataframe(
                lucky_duck_df.style.format({"score": "{:.2f}", "opp_score": "{:.2f}"}),
                column_config={col: {"label": COLUMN_NAME_MAP.get(col, col), "alignment": "center"} for col in lucky_duck_df.columns},
                hide_index=True, use_container_width=True
            )

# =================================================================================================
# Tab 5: Manager Profiles
# =================================================================================================
with tab5:
    st.header("Manager Profile")
    owners = sorted(get_all_owners_cached())
    selected_owner = st.selectbox("Select a Manager", options=owners, index=None, placeholder="Choose a manager")

    if selected_owner:
        profile_data = get_owner_profile_cached(selected_owner)
        if not profile_data:
            st.warning(f"No profile data found for {selected_owner}.")
        else:
            career_stats = profile_data['career']
            st.subheader(f"Career Stats for {selected_owner}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Wins", career_stats['wins'])
            c2.metric("Losses", career_stats['losses'])
            c3.metric("Win %", f"{career_stats['win_pct']:.3f}")
            c4.metric("Total Points", f"{career_stats['points']:.2f}")

            season_log = profile_data['season_log'].copy()
            season_log['year'] = season_log.apply(
                lambda row: f"{row['year']} 🏆" if row['is_champion'] else str(row['year']), axis=1)
            
            rivalries_df = profile_data['rivalries']

            scol1, scol2 = st.columns(2)
            with scol1:
                st.subheader("Season History")
                df_log = season_log[['year', 'team', 'record', 'points']]
                st.dataframe(
                    df_log.style.format({"points": "{:.2f}"}),
                    column_config={col: {"label": COLUMN_NAME_MAP.get(col, col), "alignment": "center"} for col in df_log.columns},
                    hide_index=True, use_container_width=True
                )
            with scol2:
                st.subheader("Rivalry Matrix (Min. 3 Games)")
                st.dataframe(
                    rivalries_df.style.format({"win_pct": "{:.3f}"}),
                    column_config={col: {"label": COLUMN_NAME_MAP.get(col, col), "alignment": "center"} for col in rivalries_df.columns},
                    hide_index=True, use_container_width=True
                )
