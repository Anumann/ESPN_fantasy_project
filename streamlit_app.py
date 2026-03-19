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
# Functions are cached to prevent re-fetching data on every interaction
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
        champions_df.rename(columns=COLUMN_NAME_MAP, inplace=True)
        st.dataframe(champions_df.style.format({"Points For": "{:.2f}"})
                     .set_properties(**{'text-align': 'center'}),
                     hide_index=True, use_container_width=True)

# =================================================================================================
# Tab 2: All-Time Records
# =================================================================================================
with tab2:
    st.header("All-Time Records")
    
    st.subheader("Regular Season")
    reg_season_df = get_all_time_standings_cached('Regular Season')
    if not reg_season_df.empty:
        reg_season_df = reg_season_df.drop(columns=['owner_id'], errors='ignore')
        reg_season_df.rename(columns=COLUMN_NAME_MAP, inplace=True)
        st.dataframe(reg_season_df.style.format({"Win %": "{:.3f}", "Avg Pts": "{:.2f}", "Total Pts": "{:.2f}"})
                     .set_properties(**{'text-align': 'center'}),
                     hide_index=True, use_container_width=True)

    st.subheader("Playoffs")
    playoffs_df = get_all_time_standings_cached('Playoffs')
    if not playoffs_df.empty:
        playoffs_df = playoffs_df.drop(columns=['owner_id'], errors='ignore')
        playoffs_df.rename(columns=COLUMN_NAME_MAP, inplace=True)
        st.dataframe(playoffs_df.style.format({"Win %": "{:.3f}", "Avg Pts": "{:.2f}", "Total Pts": "{:.2f}"})
                     .set_properties(**{'text-align': 'center'}),
                     hide_index=True, use_container_width=True)

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
                
                h2h_df.rename(columns=COLUMN_NAME_MAP, inplace=True)
                st.dataframe(h2h_df.style.format({"Points": "{:.2f}", "Opp. Points": "{:.2f}"})
                             .set_properties(**{'text-align': 'center'}),
                             hide_index=True, use_container_width=True)

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
        heartbreak_df = metrics['heartbreak']
        lucky_duck_df = metrics['lucky_duck']

        def style_luck(val):
            if val > 0.05: return 'color: #28a745'
            elif val < -0.05: return 'color: #dc3545'
            return ''
        
        all_play_df.rename(columns=COLUMN_NAME_MAP, inplace=True)
        st.dataframe(all_play_df.style.apply(lambda x: x.map(style_luck), subset=['Luck Diff'])
                     .format({'Real %': '{:.3f}', 'All-Play %': '{:.3f}', 'Luck Diff': '{:+.3f}'})
                     .set_properties(**{'text-align': 'center'}),
                     hide_index=True, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Heartbreak Index (Top Losses)")
            heartbreak_df.rename(columns=COLUMN_NAME_MAP, inplace=True)
            st.dataframe(heartbreak_df.style.format({"Score": "{:.2f}", "Opp. Score": "{:.2f}"})
                         .set_properties(**{'text-align': 'center'}),
                         hide_index=True, use_container_width=True)
        with col2:
            st.subheader("Lucky Duck Index (Top Wins)")
            lucky_duck_df.rename(columns=COLUMN_NAME_MAP, inplace=True)
            st.dataframe(lucky_duck_df.style.format({"Score": "{:.2f}", "Opp. Score": "{:.2f}"})
                         .set_properties(**{'text-align': 'center'}),
                         hide_index=True, use_container_width=True)

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
                season_log.rename(columns=COLUMN_NAME_MAP, inplace=True)
                st.dataframe(season_log[['Year', 'Team', 'Record', 'Points']]
                             .style.format({"Points": "{:.2f}"})
                             .set_properties(**{'text-align': 'center'}),
                             hide_index=True, use_container_width=True)
            with scol2:
                st.subheader("Rivalry Matrix (Min. 3 Games)")
                rivalries_df.rename(columns=COLUMN_NAME_MAP, inplace=True)
                st.dataframe(rivalries_df.style.format({"Win %": "{:.3f}"})
                             .set_properties(**{'text-align': 'center'}),
                             hide_index=True, use_container_width=True)
