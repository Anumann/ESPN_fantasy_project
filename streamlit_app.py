import streamlit as st
import pandas as pd
import altair as alt
import queries

# =================================================================================================
# Page Configuration & Main Title
# =================================================================================================
st.set_page_config(layout="wide", page_title="Fantasy League Legacy")

st.title("Fantasy League Legacy Dashboard")

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
    """Converts numeric columns to formatted strings to enforce center alignment via column_config."""
    df_copy = df.copy()
    for col in df_copy.columns:
        def safe_format(val, col_name):
            if pd.isnull(val): return ""
            try:
                if col_name in ['win_pct', 'real_pct', 'ap_pct']:
                    return f"{float(val):.3f}"
                elif col_name == 'luck_diff':
                    return f"{float(val):+.3f}"
                elif col_name in ['avg_points', 'total_points', 'points', 'opponent_points', 'score', 'opp_score', 'points_for']:
                    return f"{float(val):.2f}"
                return str(val)
            except (ValueError, TypeError):
                # Safely catches strings like "120.50 - 110.20" or "10-2-1" and leaves them alone
                return str(val)
        
        df_copy[col] = df_copy[col].apply(lambda x: safe_format(x, col))
    return df_copy

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
def get_rivalry_matrix_cached(owner):
    return queries.get_rivalry_matrix(owner)

@st.cache_data
def get_luck_metrics_cached():
    return queries.get_luck_metrics()

@st.cache_data
def get_owner_profile_cached(owner):
    return queries.get_owner_profile(owner)

@st.cache_data
def get_all_ties_cached():
    return queries.get_all_ties()

@st.cache_data
def get_league_records_cached():
    return queries.get_league_records()

@st.cache_data
def get_league_awards_cached(year):
    return queries.get_league_awards(year)

@st.cache_data
def get_all_season_point_totals_cached():
    return queries.get_all_season_point_totals()

# =================================================================================================
# Navigation Tabs
# =================================================================================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "🏆 Champions", "📜 League Records", "🥇 League Awards", "📊 All-Time Records", "⚔️ Rivalries",
    "🎲 Luck Metrics", "👤 Manager Profiles", "🤝 Ties"
])

# =================================================================================================
# Tab 1: Champions
# =================================================================================================
with tab1:
    st.header("League Champions")
    champions_df = get_champions_cached()
    if not champions_df.empty:
        st.dataframe(
            prepare_df_for_display(champions_df),
            column_config={col: {"label": COLUMN_NAME_MAP.get(col, col), "alignment": "center"} for col in champions_df.columns},
            hide_index=True, use_container_width=True
        )

# =================================================================================================
# Tab 2: League Records
# =================================================================================================
with tab2:
    st.header("All-Time League Records")
    records = get_league_records_cached()
    
    if not records:
        st.warning("Could not retrieve league records.")
    else:
        # Display in 3 columns
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

# =================================================================================================
# Tab 3: League Awards
# =================================================================================================
with tab3:
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

# =================================================================================================
# Tab 4: All-Time Records
# =================================================================================================
with tab4:
    st.header("All-Time Records")
    
    st.subheader("Regular Season")
    reg_season_df = get_all_time_standings_cached('Regular Season')
    if not reg_season_df.empty:
        df = reg_season_df.drop(columns=['owner_id'], errors='ignore')
        st.dataframe(
            prepare_df_for_display(df),
            column_config={col: {"label": COLUMN_NAME_MAP.get(col, col), "alignment": "center"} for col in df.columns},
            hide_index=True, use_container_width=True
        )

    st.subheader("Playoffs")
    playoffs_df = get_all_time_standings_cached('Playoffs')
    if not playoffs_df.empty:
        df = playoffs_df.drop(columns=['owner_id'], errors='ignore')
        st.dataframe(
            prepare_df_for_display(df),
            column_config={col: {"label": COLUMN_NAME_MAP.get(col, col), "alignment": "center"} for col in df.columns},
            hide_index=True, use_container_width=True
        )

# =================================================================================================
# Tab 5: Rivalries
# =================================================================================================
with tab5:
    st.header("Rivalry Matrix")
    owners = sorted(get_all_owners_cached())
    
    selected_owner = st.selectbox("Select a Manager to see their all-time record vs opponents:", options=owners, index=None, placeholder="Choose a manager", key='rivalry_owner_select')

    if selected_owner:
        rivalry_df = get_rivalry_matrix_cached(selected_owner)
        if rivalry_df.empty:
            st.info(f"No match history found for {selected_owner}.")
        else:
            st.dataframe(
                prepare_df_for_display(rivalry_df),
                column_config={col: {"label": COLUMN_NAME_MAP.get(col, col), "alignment": "center"} for col in rivalry_df.columns},
                hide_index=True, use_container_width=True
            )

# =================================================================================================
# Tab 6: Luck Metrics
# =================================================================================================
with tab6:
    st.header("Luck Metrics")
    st.info("Luck Diff = (Real Win % - All-Play Win %). A negative score means bad luck.")
    
    metrics = get_luck_metrics_cached()
    if not metrics:
        st.warning("Luck metrics could not be calculated.")
    else:
        st.subheader("All-Play vs. Real Records")
        all_play_df = metrics['all_play']
        st.dataframe(
            prepare_df_for_display(all_play_df),
            column_config={col: {"label": COLUMN_NAME_MAP.get(col, col), "alignment": "center"} for col in all_play_df.columns},
            hide_index=True, use_container_width=True
        )

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Heartbreak Index (Top Losses)")
            heartbreak_df = metrics['heartbreak']
            st.dataframe(
                prepare_df_for_display(heartbreak_df),
                column_config={col: {"label": COLUMN_NAME_MAP.get(col, col), "alignment": "center"} for col in heartbreak_df.columns},
                hide_index=True, use_container_width=True
            )
        with col2:
            st.subheader("Lucky Duck Index (Top Wins)")
            lucky_duck_df = metrics['lucky_duck']
            st.dataframe(
                prepare_df_for_display(lucky_duck_df),
                column_config={col: {"label": COLUMN_NAME_MAP.get(col, col), "alignment": "center"} for col in lucky_duck_df.columns},
                hide_index=True, use_container_width=True
            )

# =================================================================================================
# Tab 7: Manager Profiles
# =================================================================================================
with tab7:
    st.header("Manager Profile")
    owners = sorted(get_all_owners_cached())
    selected_owner = st.selectbox("Select a Manager", options=owners, index=None, placeholder="Choose a manager", key='manager_select')

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
                    prepare_df_for_display(df_log),
                    column_config={col: {"label": COLUMN_NAME_MAP.get(col, col), "alignment": "center"} for col in df_log.columns},
                    hide_index=True, use_container_width=True
                )
            with scol2:
                st.subheader("Rivalry Matrix (Min. 3 Games)")
                st.dataframe(
                    prepare_df_for_display(rivalries_df),
                    column_config={col: {"label": COLUMN_NAME_MAP.get(col, col), "alignment": "center"} for col in rivalries_df.columns},
                    hide_index=True, use_container_width=True
                )
            
            st.subheader("Performance Charts")
            
            # Get global point distribution for color scale
            all_points_df = get_all_season_point_totals_cached()
            min_points = all_points_df['total_points'].min()
            max_points = all_points_df['total_points'].max()

            chart_df = season_log.copy()
            chart_df['year'] = chart_df['year'].astype(str)

            # Bar Chart for Points
            points_chart = alt.Chart(chart_df).mark_bar().encode(
                x=alt.X('year', title='Year', sort=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y('points', title='Total Points For'),
                color=alt.Color('points', title="Points", scale=alt.Scale(
                    domain=[min_points, max_points],
                    range=["#4393c3", "#d6604d"] # Blue-to-Red gradient
                )),
                tooltip=['year', 'points', 'team']
            ).properties(
                title='Points Per Season'
            )
            st.altair_chart(points_chart, use_container_width=True)
            
            # Line Chart for Rank
            max_rank = season_log['rank'].max()
            rank_chart = alt.Chart(chart_df).mark_line(point=True).encode(
                x=alt.X('year', title='Year', sort=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y('rank', title='Regular Season Rank', scale=alt.Scale(reverse=True, domain=[max_rank + 1, 1])),
                tooltip=['year', 'rank', 'record']
            ).properties(
                title='Rank Per Season'
            )
            st.altair_chart(rank_chart, use_container_width=True)

# =================================================================================================
# Tab 8: Ties
# =================================================================================================
with tab8:
    st.header("Tied Matchups")
    ties_df = get_all_ties_cached()
    if not ties_df.empty:
        st.dataframe(
            prepare_df_for_display(ties_df),
            column_config={col: {"label": COLUMN_NAME_MAP.get(col, col), "alignment": "center"} for col in ties_df.columns},
            hide_index=True, use_container_width=True
        )
    else:
        st.info("No tied matchups found.")
