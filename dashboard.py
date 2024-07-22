from dash import Dash, dcc, html, Input, Output, State
import plotly.express as px
from utils import get_drivers_short_name, events_of_last_n_year, get_sessions_names_of_event, load_session
from plots import *
import fastf1
import plotly.graph_objects as go

# Enabling the cache system in a specific folder
fastf1.Cache.enable_cache('cache') 

app = Dash(__name__)

events = events_of_last_n_year(1)

# Initial session details
initial_event = events[0]  # Loads the last event of the current year
initial_sessions = get_sessions_names_of_event(initial_event)

session = load_session(initial_event, initial_sessions[0])  # Default last race and race session

driver_list = get_drivers_short_name(session)

f1_years = list(range(1980, 2025))

app.layout = html.Div(
    style={
        'backgroundColor': '#1a1a1a', 
        'color': 'white', 
        'padding': '20px', 
        'fontFamily': 'Arial, sans-serif'
    },
    children=[
        # Header
        html.Div(
            children=html.H1("F1 Dashboard", style={'textAlign': 'center', 'fontFamily': 'Helvetica, sans-serif'}),
            style={'padding': '20px'}
        ),
        
        # Sidebar
        html.Div(
            style={
                'padding': '20px', 
                'backgroundColor': '#333',
                'width': '15%',
                'float': 'left',
                'height': '100vh',
                'overflow': 'auto'
            },
            children=[
                html.H3("Historic Data", style={'color': 'white', 'margin-bottom': '10px'}),
                dcc.Dropdown(
                    id='start_year-dropdown',
                    options=[{'label': year, 'value': year} for year in f1_years],
                    value=f1_years[0],
                    placeholder='Select a year',
                    style={'margin-bottom': '10px', 'color': 'black'}
                ),
                dcc.Dropdown(
                    id='end_year-dropdown',
                    options=[{'label': year, 'value': year} for year in f1_years],
                    value=f1_years[-1],  
                    placeholder='Select a year',
                    style={'margin-bottom': '10px', 'color': 'black'}
                ),
                
                html.H3("Event and Session", style={'color': 'white', 'margin-top': '20px', 'margin-bottom': '10px'}),
                dcc.Dropdown(
                    id='event-dropdown',
                    options=[{'label': event, 'value': event} for event in events],
                    value=initial_event,
                    placeholder='Select an event',
                    style={'margin-bottom': '10px', 'color': 'black'}
                ),
                dcc.Dropdown(
                    id='session-dropdown',
                    options=[{'label': session, 'value': session} for session in initial_sessions],
                    value=initial_sessions[0],  
                    placeholder='Select a session',
                    style={'margin-bottom': '10px', 'color': 'black'}
                ),
                
                html.H3("Drivers Selection", style={'color': 'white', 'margin-top': '20px', 'margin-bottom': '10px'}),
                dcc.Dropdown(
                    id='driver1-dropdown',
                    placeholder='Select driver 1',
                    style={'margin-bottom': '10px', 'color': 'black'}
                ),
                dcc.Dropdown(
                    id='driver2-dropdown',
                    placeholder='Select driver 2',
                    style={'margin-bottom': '10px', 'color': 'black'}
                ),
            ]
        ),
        
        # Main content
        html.Div(
            style={'margin-left': '17%', 'padding': '20px'},
            children=[
                # Historical section
                html.H2("Historical", style={'color': 'white', 'fontFamily': 'Helvetica, sans-serif','margin-top': '30px', 'textAlign': 'center'}),
                dcc.Graph(id='race_per_country_map', style={'margin-bottom': '30px'}),
                dcc.Graph(id='race_wins_per_team_map', style={'margin-bottom': '30px'}),
                
                # Single Lap Analysis section
                html.H2("Single Lap Analysis", style={'color': 'white', 'fontFamily': 'Helvetica, sans-serif','margin-top': '30px', 'textAlign': 'center'}),
                dcc.RadioItems(
                    id='metric-switch',
                    options=[
                        {'label': 'Speed', 'value': 'Speed'},
                        {'label': 'Throttle', 'value': 'Throttle'}
                    ],
                    value='Speed',
                    inline=True,
                    style={'margin-bottom': '10px'}
                ),
                dcc.Graph(id='telemetry-comparison-graph', style={'margin-bottom': '30px'}),
                dcc.Graph(id='speed-comparison-graph', style={'margin-bottom': '30px'}),
                
                # Session Analysis section
                html.H2("Session Analysis", style={'color': 'white', 'fontFamily': 'Helvetica, sans-serif', 'margin-top': '30px', 'textAlign': 'center' }),
                dcc.RadioItems(
                    id='laptime-graph-mode',
                    options=[
                        {'label': 'Driver 1', 'value': 'Driver1'},
                        {'label': 'Driver 2', 'value': 'Driver2'},
                        {'label': 'Merge', 'value': 'Merge'}
                    ],
                    value='Driver1',
                    inline=True,
                    style={'margin-bottom': '10px'}
                ),
                dcc.Graph(id='laptime-compound-graph', style={'margin-bottom': '30px'}),
                dcc.Graph(id='parallel-coordinates-graph', style={'margin-bottom': '30px'}),
            ]
        ),
    ]
)

# Callback to update session dropdown based on selected event
@app.callback(
    Output('session-dropdown', 'options'),
    Input('event-dropdown', 'value')
)
def update_sessions(event):
    sessions = get_sessions_names_of_event(event)
    return [{'label': session, 'value': session} for session in sessions]

# Reset dropdowns when event changes
@app.callback(
    [Output('session-dropdown', 'value'),
     Output('driver1-dropdown', 'value'),
     Output('driver2-dropdown', 'value')],
    Input('event-dropdown', 'value')
)
def reset_dropdowns_on_event_change(event):
    # Reset all dropdowns to default values when event changes
    return None, None, None

# Callback to update driver dropdowns based on selected session
@app.callback(
    [Output('driver1-dropdown', 'options'),
     Output('driver2-dropdown', 'options')],
    Input('session-dropdown', 'value'),
    State('event-dropdown', 'value')
)
def update_drivers(session_name, event_name):
    if session_name and event_name:
        session = load_session(event_name, session_name)
        driver_list = get_drivers_short_name(session)
        options = [{'label': driver, 'value': driver} for driver in driver_list]
        return options, options
    else:
        return [], []

#TELEMETRY COMPARISON GRAPH
@app.callback(
    Output('telemetry-comparison-graph', 'figure'),
    [Input('driver1-dropdown', 'value'),
     Input('driver2-dropdown', 'value'),
     Input('metric-switch', 'value'),
     Input('session-dropdown', 'value'),
     Input('event-dropdown', 'value')]
)
def update_graph(driver1, driver2, metric, session_name, event_name):
    if driver1 and driver2 and session_name and event_name:
        session = load_session(event_name, session_name)
        return plot_lap_telemetry_comparison(session, driver1, driver2, metric)
    else:
        return create_black_figure()
    
#SPEED COMPARISON GRAPH
@app.callback(
    Output('speed-comparison-graph', 'figure'),
    [Input('driver1-dropdown', 'value'),
     Input('driver2-dropdown', 'value'),
     Input('session-dropdown', 'value'),
     Input('event-dropdown', 'value')]
)
def update_graph(driver1, driver2, session_name, event_name):
    if driver1 and driver2 and session_name and event_name:
        session = load_session(event_name, session_name)
        return plot_speed_diff_drivers(session, driver1, driver2)
    else:
        return create_black_figure()
    

#LAPT TIME COMPOUND GRAPH
@app.callback(
    Output('laptime-compound-graph', 'figure'),
    [Input('driver1-dropdown', 'value'),
     Input('driver2-dropdown', 'value'),
     Input('laptime-graph-mode', 'value'),
     Input('session-dropdown', 'value'),
     Input('event-dropdown', 'value')]
)
def update_graph(driver1, driver2, mode, session_name, event_name):
    if driver1 and driver2 and mode and session_name and event_name:
        session = load_session(event_name, session_name)
        if(mode == 'Driver1'):
            return plot_session_laptimes_with_compound_type(session, driver1)
        elif(mode == 'Driver2'):
            return plot_session_laptimes_with_compound_type(session, driver2)
        else:
            return plot_laptime_compound_comparison_merged(session, driver1, driver2)
    else:
        return create_black_figure()
    
# MAP RACE PER COUNTRY
@app.callback(
    Output('race_per_country_map', 'figure'),
    [Input('start_year-dropdown', 'value'),
     Input('end_year-dropdown', 'value')]
)
def update_graph(start_year, end_year):
    if start_year and end_year:
        return plot_map_races_per_country(start_year,end_year)
        
    else:
        return create_black_figure()
    
# RACE WINS PER TEAM
@app.callback(
    Output('race_wins_per_team_map', 'figure'),
    [Input('start_year-dropdown', 'value'),
     Input('end_year-dropdown', 'value')]
)
def update_graph(start_year, end_year):
    if start_year and end_year:
        return plot_race_wins_per_team(start_year,end_year)
    else:
        return create_black_figure()
    

# PARALLEL COORDINATES MULTIDATA GRAPH
@app.callback(
    Output('parallel-coordinates-graph', 'figure'),
    [Input('event-dropdown', 'value')]
)
def update_graph(event_name):
    if event_name:
        return plot_parallel_coordinates(event_name)
    else:
        return create_black_figure()

if __name__ == '__main__':
    app.run_server(debug=True)