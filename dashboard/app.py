import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
import pandas as pd
import traceback
try:
    from dashboard import queries
except ImportError:
    import queries

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(className='header p-4 bg-primary text-white', children=[
        html.H1('Fantasy League Legacy Dashboard', className='display-4'),
        html.P("A comprehensive history of our ESPN fantasy football league.", className="lead"),
    ]),
    dbc.Tabs([
        dbc.Tab(label="Home & Champions", tab_id="home"),
        dbc.Tab(label="All-Time Records", tab_id="records"),
        dbc.Tab(label="Head-to-Head", tab_id="h2h"),
        dbc.Tab(label="Luck Metrics", tab_id="luck"),
        dbc.Tab(label="Manager Profiles", tab_id="profile"),
    ], id="tabs", active_tab="home", className="mb-4"),
    html.Div(id='page-content', className='p-4')
])

@app.callback(dash.dependencies.Output('page-content', 'children'), [dash.dependencies.Input('tabs', 'active_tab')])
def render_content(active_tab):
    if active_tab == "home":
        try:
            df = queries.get_league_champions()
            if df.empty: return html.Div("No data.")
            # Updated Table Headers for Runner-Up and Score
            header = [html.Thead(html.Tr([
                html.Th("Year"), 
                html.Th("Champion Team"), 
                html.Th("Champion Owner"), 
                html.Th("Record"), 
                html.Th("Runner-Up"), 
                html.Th("Final Score")
            ]))]
            rows = []
            for _, row in df.iterrows():
                rows.append(html.Tr([
                    html.Td(row['year']), 
                    html.Td(row['team_name']), 
                    html.Td(row['owner_name'], className="text-success font-weight-bold"), 
                    html.Td(row['record']), 
                    html.Td(row['runner_up']),
                    html.Td(row['score'])
                ]))
            return html.Div([
                html.H2("League Champions", className="mb-3"), 
                dbc.Table(header + [html.Tbody(rows)], striped=True, bordered=True, hover=True, color="dark")
            ])
        except Exception as e: return html.Div(f"Error: {e}")

    elif active_tab == "records":
        try:
            reg = queries.get_all_time_standings('Regular Season')
            play = queries.get_all_time_standings('Playoffs')
            def make_table(df, title):
                h = [html.Thead(html.Tr([html.Th("Owner"), html.Th("G"), html.Th("W"), html.Th("L"), html.Th("Win %"), html.Th("Avg Pts")]))]
                r = []
                for _, row in df.iterrows():
                    r.append(html.Tr([html.Td(row['owner_name']), html.Td(row['games_played']), html.Td(row['wins']), html.Td(row['losses']), html.Td(f"{row['win_pct']:.3f}"), html.Td(f"{row['avg_points']:.1f}")]))
                return html.Div([html.H3(title, className="mt-4"), dbc.Table(h + [html.Tbody(r)], striped=True, bordered=True, hover=True, color="dark")])
            return html.Div([html.H2("All-Time Records"), make_table(reg, "Regular Season"), make_table(play, "Playoffs")])
        except Exception as e: return html.Div(f"Error: {e}")

    elif active_tab == "h2h":
        owners = queries.get_all_owners()
        options = [{'label': o, 'value': o} for o in owners]
        return html.Div([
            html.H2("Head-to-Head Analysis"),
            dbc.Row([
                dbc.Col(dcc.Dropdown(id='owner1-dropdown', options=options, placeholder="Owner 1", className="text-dark"), width=6),
                dbc.Col(dcc.Dropdown(id='owner2-dropdown', options=options, placeholder="Owner 2", className="text-dark"), width=6),
            ], className="mb-4"),
            html.Div(id='h2h-content')
        ])

    elif active_tab == "luck":
        try:
            m = queries.get_luck_metrics()
            if not m: return html.Div("No metrics.")
            
            ap_h = [html.Thead(html.Tr([html.Th("Owner"), html.Th("Real Record"), html.Th("Real %"), html.Th("All-Play Record"), html.Th("AP %"), html.Th("Luck Diff")]))]
            ap_r = []
            for _, row in m['all_play'].iterrows():
                diff = row['luck_diff']
                color = "text-success" if diff > 0.05 else ("text-danger" if diff < -0.05 else "text-white")
                ap_r.append(html.Tr([
                    html.Td(row['owner']),
                    html.Td(row['real_record']),
                    html.Td(f"{row['real_pct']:.3f}"),
                    html.Td(row['ap_record']),
                    html.Td(f"{row['ap_pct']:.3f}"),
                    html.Td(f"{diff:+.3f}", className=f"{color} font-weight-bold")
                ]))
            ap_table = dbc.Table(ap_h + [html.Tbody(ap_r)], striped=True, bordered=True, hover=True, color="dark")
            
            hb_h = [html.Thead(html.Tr([html.Th("Owner"), html.Th("Year"), html.Th("Week"), html.Th("Score"), html.Th("Opponent"), html.Th("Opp Score")]))]
            hb_r = []
            for _, r in m['heartbreak'].iterrows():
                hb_r.append(html.Tr([html.Td(r['owner']), html.Td(r['year']), html.Td(r['week']), html.Td(f"{r['score']:.2f}", className="text-danger font-weight-bold"), html.Td(r['opponent']), html.Td(f"{r['opp_score']:.2f}")]))
            hb_table = dbc.Table(hb_h + [html.Tbody(hb_r)], striped=True, bordered=True, hover=True, color="dark")
            
            ld_h = [html.Thead(html.Tr([html.Th("Owner"), html.Th("Year"), html.Th("Week"), html.Th("Score"), html.Th("Opponent"), html.Th("Opp Score")]))]
            ld_r = []
            for _, r in m['lucky_duck'].iterrows():
                ld_r.append(html.Tr([html.Td(r['owner']), html.Td(r['year']), html.Td(r['week']), html.Td(f"{r['score']:.2f}", className="text-success font-weight-bold"), html.Td(r['opponent']), html.Td(f"{r['opp_score']:.2f}")]))
            ld_table = dbc.Table(ld_h + [html.Tbody(ld_r)], striped=True, bordered=True, hover=True, color="dark")
            
            return html.Div([
                html.H2("Luck Metrics"),
                html.P("Difference = (Real Win % - All-Play Win %). Negative means you played better than your record shows (Bad Luck)."),
                dbc.Row([dbc.Col([html.H3("All-Play vs Real Records"), ap_table], width=12, className="mb-5")]),
                dbc.Row([
                    dbc.Col([html.H3("Heartbreak Index (High Score Loss)"), hb_table], width=6),
                    dbc.Col([html.H3("Lucky Duck Index (Low Score Win)"), ld_table], width=6),
                ])
            ])
        except Exception as e: return html.Div(f"Error: {e}")

    elif active_tab == "profile":
        owners = queries.get_all_owners()
        options = [{'label': o, 'value': o} for o in owners]
        return html.Div([
            html.H2("Manager Profile"),
            dcc.Dropdown(id='profile-owner-dropdown', options=options, placeholder="Select Manager", className="mb-4 text-dark"),
            html.Div(id='profile-content')
        ])

@app.callback(dash.dependencies.Output('h2h-content', 'children'), [dash.dependencies.Input('owner1-dropdown', 'value'), dash.dependencies.Input('owner2-dropdown', 'value')])
def update_h2h(o1, o2):
    if not o1 or not o2: return html.Div("Select two owners.")
    if o1 == o2: return html.Div("Select different owners.")
    try:
        df = queries.get_head_to_head(o1, o2)
        if df.empty: return html.Div("No history.")
        w = len(df[df['outcome']=='WIN']); l = len(df[df['outcome']=='LOSS']); t = len(df[df['outcome']=='TIE'])
        rec = f"{o1} leads {w}-{l}-{t}" if w > l else (f"{o2} leads {l}-{w}-{t}" if l > w else f"Tied {w}-{l}-{t}")
        h = [html.Thead(html.Tr([html.Th("Year"), html.Th("Week"), html.Th(f"{o1}"), html.Th(f"{o2}"), html.Th("Result")]))]
        r = []
        for _, row in df.iterrows():
            c = "text-success" if row['outcome']=='WIN' else ("text-danger" if row['outcome']=='LOSS' else "text-warning")
            s1 = {"fontWeight":"bold"} if row['points'] > row['opponent_points'] else {}
            s2 = {"fontWeight":"bold"} if row['opponent_points'] > row['points'] else {}
            r.append(html.Tr([html.Td(row['year']), html.Td(row['week']), html.Td(f"{row['points']:.2f}", style=s1), html.Td(f"{row['opponent_points']:.2f}", style=s2), html.Td(row['outcome'], className=c)]))
        return html.Div([html.H3(rec, className="text-info"), dbc.Table(h + [html.Tbody(r)], striped=True, bordered=True, hover=True, color="dark")])
    except Exception as e: return html.Div(f"Error: {e}")

@app.callback(dash.dependencies.Output('profile-content', 'children'), [dash.dependencies.Input('profile-owner-dropdown', 'value')])
def render_profile(owner):
    if not owner: return html.Div("Select a manager.")
    try:
        data = queries.get_owner_profile(owner)
        if not data: return html.Div("No data.")
        c = data['career']
        
        cards = dbc.Row([
            dbc.Col(dbc.Card([dbc.CardBody([html.H4("Wins", className="card-title"), html.H2(c['wins'])])], color="success", inverse=True), width=3),
            dbc.Col(dbc.Card([dbc.CardBody([html.H4("Losses", className="card-title"), html.H2(c['losses'])])], color="danger", inverse=True), width=3),
            dbc.Col(dbc.Card([dbc.CardBody([html.H4("Win %", className="card-title"), html.H2(f"{c['win_pct']:.3f}")])], color="info", inverse=True), width=3),
            dbc.Col(dbc.Card([dbc.CardBody([html.H4("Points", className="card-title"), html.H2(f"{c['points']:.0f}")])], color="warning", inverse=True), width=3),
        ], className="mb-4")
        
        log = data['season_log']
        log_h = [html.Thead(html.Tr([html.Th("Year"), html.Th("Team"), html.Th("Record"), html.Th("Points")]))]
        log_r = []
        for _, r in log.iterrows():
            year_display = f"{r['year']} 🏆" if r['is_champion'] else str(r['year'])
            log_r.append(html.Tr([html.Td(year_display), html.Td(r['team']), html.Td(r['record']), html.Td(f"{r['points']:.2f}")]))
        log_table = dbc.Table(log_h + [html.Tbody(log_r)], striped=True, bordered=True, hover=True, color="dark")
        
        riv = data['rivalries']
        
        if not riv.empty and 'win_pct' in riv.columns:
            riv_h = [html.Thead(html.Tr([html.Th("Opponent"), html.Th("Record"), html.Th("Win %")]))]
            riv_r = []
            for _, r in riv.iterrows():
                riv_r.append(html.Tr([html.Td(r['opponent']), html.Td(r['record']), html.Td(f"{r['win_pct']:.3f}")]))
            riv_table = dbc.Table(riv_h + [html.Tbody(riv_r)], striped=True, bordered=True, hover=True, color="dark")
        else:
            riv_table = html.Div("No sufficient rivalry data (min 3 games).")

        return html.Div([
            html.H2(f"{owner} Profile", className="mb-3"),
            cards,
            dbc.Row([
                dbc.Col([html.H3("Season History"), log_table], width=6),
                dbc.Col([html.H3("Rivalry Matrix (Min 3 Games)"), riv_table], width=6)
            ])
        ])
    except Exception as e:
        traceback.print_exc()
        return html.Div(f"Error: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8051, debug=True)
