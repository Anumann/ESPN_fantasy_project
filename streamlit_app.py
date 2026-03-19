import streamlit as st
import pandas as pd
import queries

# =================================================================================================
# Page Configuration & Main Title
# =================================================================================================
st.set_page_config(layout="wide", page_title="Fantasy League Legacy")

st.title("Fantasy League Legacy Dashboard")

# =================================================================================================
# Helper Functions & Constants
# =================================================================================================
COLUMN_NAME_MAP = {
    'year': 'Year',
    'team_name': 'Team',
    'owner_name': 'Owner',
    'record': 'Record',
    'runner_up': 'Runner-Up',
    'score': 'Final Score',
    'games_played': 'Games',
    'wins': 'W',
    'losses': 'L',
    'ties': 'T',
    'win_pct': 'Win %',
    'avg_points': 'Avg Pts',
    'week': 'Week',
    'points': 'Points',
    'opponent_points': 'Opp. Points',
    'outcome': 'Outcome',
    'owner': 'Owner',
    'opponent': 'Opponent',
    'opp_score': 'Opp. Score',
    'real_record': 'Real Record',
    'real_pct': 'Real %',
    'ap_record': 'All-Play Record',
    'ap_pct': 'All-Play %',
    'luck_diff': 'Luck Diff',
}

def anonymize_name(name):
    """Capitalizes and formats a full name to omit the last name, with an exception for 'Alex'."""
    if not isinstance(name, str):
        return str(name)
    parts = name.title().split()
    if parts[0] == 'Alex' and len(parts) > 1:
        return f"Alex {parts[-1][0]}."
    if len(parts) > 1:
        return ' '.join(parts[:-1])
    return name.title()

def format_df_names(df, column_names):
    """Applies the anonymize_name function to specified columns of a DataFrame."""
    df_copy = df.copy()
    for col in column_names:
        if col in df_copy.columns:
            df_copy[col] = df_copy[col].apply(anonymize_name)
    return df_copy

def style_and_display_df(df):
    """Applies renaming, styling, and displays a Streamlit DataFrame."""
    df = df.rename(columns=COLUMN_NAME_MAP)
    st.dataframe(
        df.style.set_properties(**{'text-align': 'center'}),
        hide_index=True,
        use_container_width=True
    )

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
    "🏆 Champions",
    "📊 All-Time Records",
    "⚔️ Head-to-Head",
    "🎲 Luck Metrics",
    "👤 Manager Profiles"
])

# =================================================================================================
# Tab 1: Champions
# =================================================================================================
with tab1:
    st.header("League Champions")
    champions_df = get_champions_cached()
    if champions_df.empty:
        st.warning("No champion data found.")
    else:
        display_df = format_df_names(champions_df, ['owner_name', 'runner_up'])
        style_and_display_df(display_df)

# =================================================================================================
# Tab 2: All-Time Records
# =================================================================================================
with tab2:
    st.header("All-Time Records")
    
    st.subheader("Regular Season")
    reg_season_df = get_all_time_standings_cached('Regular Season')
    if not reg_season_df.empty:
        display_reg = format_df_names(reg_season_df, ['owner_name'])
        display_reg = display_reg.drop(columns=['owner_id'], errors='ignore')
        style_and_display_df(display_reg)

    st.subheader("Playoffs")
    playoffs_df = get_all_time_standings_cached('Playoffs')
    if not playoffs_df.empty:
        display_playoffs = format_df_names(playoffs_df, ['owner_name'])
        display_playoffs = display_playoffs.drop(columns=['owner_id'], errors='ignore')
        style_and_display_df(display_playoffs)

# =================================================================================================
# Tab 3: Head-to-Head
# =================================================================================================
with tab3:
    st.header("Head-to-Head Analysis")
    owners = get_all_owners_cached()
    
    name_map = {anonymize_name(name): name for name in owners}
    anonymized_owners = sorted(name_map.keys())
    
    col1, col2 = st.columns(2)
    with col1:
        anon_owner1 = st.selectbox("Select Owner 1", options=anonymized_owners, index=None, placeholder="Choose an owner")
    with col2:
        anon_owner2 = st.selectbox("Select Owner 2", options=anonymized_owners, index=None, placeholder="Choose an owner")

    if anon_owner1 and anon_owner2:
        if anon_owner1 == anon_owner2:
            st.warning("Please select two different owners.")
        else:
            original_owner1 = name_map[anon_owner1]
            original_owner2 = name_map[anon_owner2]
            
            h2h_df = get_h2h_cached(original_owner1, original_owner2)
            if h2h_df.empty:
                st.info(f"No match history found between {anon_owner1} and {anon_owner2}.")
            else:
                wins = len(h2h_df[h2h_df['outcome'] == 'WIN'])
                losses = len(h2h_df[h2h_df['outcome'] == 'LOSS'])
                ties = len(h2h_df[h2h_df['outcome'] == 'TIE'])
                
                if wins > losses:
                    st.subheader(f"Record: {anon_owner1} leads {wins}-{losses}-{ties}")
                elif losses > wins:
                    st.subheader(f"Record: {anon_owner2} leads {losses}-{wins}-{ties}")
                else:
                    st.subheader(f"Record: Tied {wins}-{losses}-{ties}")
                
                style_and_display_df(h2h_df)

# =================================================================================================
# Tab 4: Luck Metrics
# =================================================================================================
with tab4:
    st.header("Luck Metrics")
    st.info("Luck Diff = (Real Win % - All-Play Win %). A negative score means you had bad luck (your team performed better than its record shows).")
    
    metrics = get_luck_metrics_cached()
    
    if not metrics:
        st.warning("Luck metrics could not be calculated.")
    else:
        st.subheader("All-Play vs. Real Records")
        
        all_play_df = format_df_names(metrics['all_play'], ['owner'])
        heartbreak_df = format_df_names(metrics['heartbreak'], ['owner', 'opponent'])
        lucky_duck_df = format_df_names(metrics['lucky_duck'], ['owner', 'opponent'])

        def style_luck(val):
            if val > 0.05: return 'color: #28a745'
            elif val < -0.05: return 'color: #dc3545'
            return ''
        
        all_play_renamed = all_play_df.rename(columns=COLUMN_NAME_MAP)
        st.dataframe(
            all_play_renamed.style.apply(lambda x: x.map(style_luck), subset=['Luck Diff']).format({'Luck Diff': '{:+.3f}'}).set_properties(**{'text-align': 'center'}),
            hide_index=True,
            use_container_width=True
        )

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Heartbreak Index (Top Losses)")
            style_and_display_df(heartbreak_df)
        with col2:
            st.subheader("Lucky Duck Index (Top Wins)")
            style_and_display_df(lucky_duck_df)

# =================================================================================================
# Tab 5: Manager Profiles
# =================================================================================================
with tab5:
    st.header("Manager Profile")
    owners = get_all_owners_cached()
    name_map = {anonymize_name(name): name for name in owners}
    anonymized_owners = sorted(name_map.keys())

    selected_anon_owner = st.selectbox("Select a Manager", options=anonymized_owners, index=None, placeholder="Choose a manager to view their profile")

    if selected_anon_owner:
        original_owner = name_map[selected_anon_owner]
        profile_data = get_owner_profile_cached(original_owner)
        
        if not profile_data:
            st.warning(f"No profile data found for {selected_anon_owner}.")
        else:
            career_stats = profile_data['career']
            
            st.subheader(f"Career Stats for {selected_anon_owner}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Wins", career_stats['wins'])
            c2.metric("Losses", career_stats['losses'])
            c3.metric("Win %", f"{career_stats['win_pct']:.3f}")
            c4.metric("Total Points", f"{career_stats['points']:.0f}")

            season_log = profile_data['season_log'].copy()
            season_log['year'] = season_log.apply(lambda row: f"{row['year']} 🏆" if row['is_champion'] else str(row['year']), axis=1)
            
            rivalries_df = format_df_names(profile_data['rivalries'], ['opponent'])

            scol1, scol2 = st.columns(2)
            with scol1:
                st.subheader("Season History")
                style_and_display_df(season_log[['year', 'team', 'record', 'points']])
            with scol2:
                st.subheader("Rivalry Matrix (Min. 3 Games)")
                style_and_display_df(rivalries_df)
