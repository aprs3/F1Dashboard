import plotly.graph_objects as go
from utils import  *
import fastf1.plotting
from datetime import datetime, timedelta
import pandas as pd

def plot_lap_telemetry_comparison(session, driver1, driver2, metric):
    """
    Plots a comparison of lap telemetry data between two drivers. Using line mode of scatter plot.

    Args:
        session (Session): The session object containing lap and circuit information.
        driver1 (str): The name of the first driver.
        driver2 (str): The name of the second driver.
        metric (str): The metric to be plotted, either 'Speed' or 'Throttle Percentage'.

    Returns:
        fig (go.Figure): The plotly figure object containing the comparison plot.
    """
    # Getting the fastest lap info of each driver
    driver1_lap = session.laps.pick_driver(driver1).pick_fastest()
    driver2_lap = session.laps.pick_driver(driver2).pick_fastest()

    # Getting the telemetry data of the fastest lap of each driver
    driver1_telemetry = driver1_lap.get_car_data().add_distance()
    driver2_telemetry = driver2_lap.get_car_data().add_distance()

    # Getting the team color of the drivers for the plot
    driver1_teamColor = get_driver_team_and_color(session, driver1)[1]
    driver2_teamColor = get_driver_team_and_color(session, driver2)[1]

    # Getting the full name of the drivers
    driver1_fullName = get_driver_full_name(session, driver1)
    driver2_fullName = get_driver_full_name(session, driver2)

    # Circuit info to retrieve corners
    circuit_info = session.get_circuit_info()

    measure_unit = ''
    if(metric == 'Speed'):
        measure_unit = 'Km/h'
    else:
        measure_unit = '%'

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=driver1_telemetry['Distance'], y=driver1_telemetry[metric],
                            mode='lines', name=driver1_fullName, line=dict(color=driver1_teamColor), hovertemplate=f'<b>{driver1}</b><br><b>{metric}: %{{y}} {measure_unit}</b><extra></extra>'))
    fig.add_trace(go.Scatter(x=driver2_telemetry['Distance'], y=driver2_telemetry[metric],
                            mode='lines', name=driver2_fullName, line=dict(color=driver2_teamColor), hovertemplate=f'<b>{driver2}</b><br><b>{metric}: %{{y}} {measure_unit}</b><extra></extra>'))

    # Adding corners annotations
    for _, row in circuit_info.corners.iterrows():
        fig.add_shape(
            type='line',
            x0=row['Distance'], x1=row['Distance'],
            y0=0, y1=0.9,  # Stop the line slightly above the annotation
            xref='x', yref='paper',
            line=dict(color='grey', width=1, dash='dot')
        )
        fig.add_annotation(
            x=row['Distance'],
            y=0.95,  # Positioning annotation just above the end of the line
            xref='x', yref='paper',
            text=f"C{row['Number']}",
            showarrow=False,
            font=dict(size=10),
            align='center'
        )

    title = 'Speed' if metric == 'Speed' else 'Throttle Percentage'
    y_axis_title = 'Speed (Km/h)' if metric == 'Speed' else 'Throttle (%)'

    # Adding the legend and layout settings
    fig.update_layout(
        title={'text': f'Fastest Lap: Driver {title} Comparison', 'x': 0.5, 'xanchor': 'center'},
        xaxis_title='Distance (m)',
        yaxis_title=y_axis_title,
        margin=dict(l=50, r=50, t=50, b=50), 
        plot_bgcolor='#1a1a1a',
        paper_bgcolor='#1a1a1a',
        font=dict(
            family="Arial",
            size=12,
            color="white"
        )
    )

    return fig

def plot_speed_diff_drivers(session, driver1, driver2):
    """
    Plots the speed difference between two drivers at each corner. Using bar plots.

    Args:
        session (str): The session identifier.
        driver1 (str): The name of the first driver.
        driver2 (str): The name of the second driver.

    Returns:
        fig (go.Figure): The plotted figure.
    """

    # Getting the speed difference between the drivers at each corner
    df = get_avg_speed_diff_drivers(session, driver1, driver2)

    fig = go.Figure()

    # Add the bar trace
    fig.add_trace(go.Bar(
        x=df['corner_number'], 
        y=df['speed_diff'],
        base=0,
        marker_color=['green' if diff >= 0 else 'red' for diff in df['speed_diff']],
        name='Speed Difference',
        showlegend=False,
        customdata=round(df['speed_diff'], 2),
        hovertemplate='%{customdata} Km/h<extra></extra>',  # Custom hover text
        text=round(df['speed_diff'], 2),  # Add the speed difference as text
        textposition='inside',  # Position the text inside the bar
        insidetextanchor='middle' 
    ))

    # Add scatter traces for the legend
    fig.add_trace(go.Scatter(
        x=[None], 
        y=[None], 
        mode='markers', 
        marker=dict(size=10, color='green'), 
        legendgroup=f'Gains', 
        showlegend=True, 
        name=f'{driver1} Gain'
    ))

    fig.add_trace(go.Scatter(
        x=[None], 
        y=[None], 
        mode='markers', 
        marker=dict(size=10, color='red'), 
        legendgroup='Losses', 
        showlegend=True, 
        name=f'{driver1} Loss'
    ))

    fig.update_layout(
        title={'text': f'Fastest lap: speed diff {driver1}-{driver2} at Each Corner', 'x': 0.5, 'xanchor': 'center'},
        xaxis_title='Corner Number',
        yaxis_title='Speed Difference (km/h)',
        showlegend=True,
        xaxis=dict(
            tickmode='array', #Shows all corners number in x axis
            tickvals=df['corner_number'],
            ticktext=df['corner_number']
        ),
        plot_bgcolor='#1a1a1a',
        paper_bgcolor='#1a1a1a',
        font=dict(
            family="Arial",
            size=12,
            color="white"
        )
    )

    return fig



def plot_session_laptimes_with_compound_type(session, driver):
    """
    Plots the lap times of a specific driver in a session with different compound types.

    Args:
        session (Session): The session object containing lap data.
        driver (str): The name of the driver.

    Returns:
        fig (plotly.graph_objects.Figure): The scatter plot figure showing lap times with compound types.
    """

    # Setup FastF1 and load data 
    fastf1.plotting.setup_mpl(misc_mpl_mods=False)

    # Extract lap data for a specific driver
    driver_laps = session.laps.pick_driver(driver).pick_quicklaps().reset_index()

    # Get compound colors from fastf1.plotting.COMPOUND_COLORS
    compound_colors = fastf1.plotting.COMPOUND_COLORS

    # Create Plotly scatter plot with traces for each compound type
    fig = go.Figure()

    # Iterate over each compound type and add a trace to the plot
    for compound in compound_colors.keys():
       
        compound_data = driver_laps[driver_laps['Compound'] == compound] #Selects the laps of a specific compound
        
        converted_lap_time = convert_timedelta_to_datetime(compound_data['LapTime']) #Converts the lap time to a datetime object

        fig.add_trace(go.Scatter(
            x=compound_data['LapNumber'],
            y=converted_lap_time,
            mode='markers',
            marker=dict(color=compound_colors[compound], size = 8),
            name=compound,  # Compound type as legend label
            text=[f"Lap {str(int(lap))} Time: {str(t.components.minutes)+":"+str(t.components.seconds)+":"+str(t.components.milliseconds)}" for lap, t in zip(compound_data['LapNumber'], compound_data['LapTime'])],
            hoverinfo='text'
        ))

    fig.update_layout(
        yaxis=dict(tickformat='%M:%S.%f'), #Display of the time given a datatime to the plot
        title={'text': f'{driver} {session.name} Lap Times with Compound Type', 'x': 0.5, 'xanchor': 'center'},
        xaxis_title='Lap Number',
        yaxis_title='Lap Time',
        paper_bgcolor='#1a1a1a',
        plot_bgcolor='#1a1a1a',  # Set background color to black
        showlegend=True,       # Show legend
        legend=dict(
            title='Compound',  # Legend title
            orientation='v',   # Vertical legend orientation
            yanchor='top',     # Anchor legend to the top
            xanchor='right',   # Anchor legend to the right
            x=1.12,            # Position legend outside the plot
            y=1                # Position legend at the top
        ),
        font=dict(
            family="Arial",
            size=12,
            color="white"
        )
    )

    return fig

def plot_laptime_compound_comparison_merged(session, driver1, driver2):
    """
    Plots the lap times and compounds of two drivers in a session.

    Args:
        session (Session): The session object containing lap data.
        driver1 (str): The name of the first driver.
        driver2 (str): The name of the second driver.

    Returns:
        fig (plotly.graph_objects.Figure): The scatter plot figure showing lap times with compound types.
    """

    # Setup FastF1 and load data 
    fastf1.plotting.setup_mpl(misc_mpl_mods=False)
   

    # Extract lap data for a specific driver 
    #Taking only quicklaps to avoid outliers
    driver1_laps = session.laps.pick_driver(driver1).pick_quicklaps().reset_index()
    driver2_laps = session.laps.pick_driver(driver2).pick_quicklaps().reset_index()

    driver1_teamColor = get_driver_team_and_color(session, driver1)[1]
    driver2_teamColor = get_driver_team_and_color(session, driver2)[1]


    # Get compound colors from fastf1.plotting.COMPOUND_COLORS
    compound_colors = fastf1.plotting.COMPOUND_COLORS

    # Create Plotly scatter plot with traces for each compound type
    fig = go.Figure()

    # Add trace for driver 1
    for compound in compound_colors.keys():
        compound_data = driver1_laps[driver1_laps['Compound'] == compound]
        y_values = convert_timedelta_to_datetime(compound_data['LapTime'])
        fig.add_trace(go.Scatter(
            x=compound_data['LapNumber'],
            y=y_values,
            mode='markers',
            marker=dict(
                color=driver1_teamColor,
                size=10,
                line=dict(color=compound_colors[compound], width=2)
            ),
            name=f'{driver1 }- {compound}',
            text=[f"{driver1}-{compound} - Lap {str(int(lap))}: {str(t.components.minutes)+":"+str(t.components.seconds)+":"+str(t.components.milliseconds)}" for lap, t in zip(compound_data['LapNumber'], compound_data['LapTime'])],

            hoverinfo='text'
        ))

    # Add trace for driver 2
    for compound in compound_colors.keys():
        compound_data = driver2_laps[driver2_laps['Compound'] == compound]
        y_values = convert_timedelta_to_datetime(compound_data['LapTime'])
        fig.add_trace(go.Scatter(
            x=compound_data['LapNumber'],
            y=y_values,
            mode='markers',
            marker=dict(
                color=driver2_teamColor,
                size=10,
                line=dict(color=compound_colors[compound], width=2)
            ),
            name=f'{driver2} - {compound}',
            text=[f"{driver2}-{compound} - Lap {str(int(lap))}: {str(t.components.minutes)+":"+str(t.components.seconds)+":"+str(t.components.milliseconds)}" for lap, t in zip(compound_data['LapNumber'], compound_data['LapTime'])],
            hoverinfo='text'
        ))

    fig.update_layout(
        yaxis=dict(tickformat='%M:%S.%f'),
        title={'text': f'{driver1} - {driver2} - Lap Times with Compound Comparison', 'x': 0.5, 'xanchor': 'center'},
        xaxis_title='Lap Number',
        yaxis_title='Lap Time',
        plot_bgcolor='#1a1a1a',
        paper_bgcolor='#1a1a1a',
        showlegend=True,         # Show legend
        legend=dict(
            title='Driver - Compound',
            orientation='v',    # Vertical legend orientation
            yanchor='top',      # Anchor legend to the top
            xanchor='right',    # Anchor legend to the right
            x=1.27,             # Position legend outside the plot
            y=1                 # Position legend at the top
        ),
        font=dict(
            family="Arial",
            size=12,
            color="white"
        )
    )

    return fig


def plot_map_races_per_country(start_year, end_year):
    """
    Plots a choropleth map showing the number of races per country within a given time range.

    Parameters:
    - start_year (int): The starting year of the time range.
    - end_year (int): The ending year of the time range.

    Returns:
    - fig (plotly.graph_objects.Figure): The choropleth map figure.
    """

    df = get_country_counts_ISO(start_year, end_year)

    fig = go.Figure(data=go.Choropleth(
        locations=df['ISO'],
        z=df['Count'],
        text=df['Country'],
        colorscale=[[0.0, 'white'], [1.0, 'blue']],  # Custom color scale from white to blue
        autocolorscale=False,
        reversescale=False,
        marker_line_color='black',
        marker_line_width=0.8,
        colorbar_tickprefix='',
        colorbar_title='Number of races',
    ))

    fig.update_layout(
        title={
            'text': f'Races per country ({start_year}-{end_year})',
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {
                'size': 24
            }
        },
        geo=dict(
            showframe=False,
            showcoastlines=False,
            projection_type='equirectangular',
            lonaxis=dict(range=[-180, 180]),
            lataxis=dict(range=[-60, 90])
        ),
        margin=dict(l=0, r=0, t=50, b=0),
        plot_bgcolor='#1a1a1a',
        paper_bgcolor='#1a1a1a',
        font=dict(
            family="Arial",
            size=12,
            color="white"
        )
    )

    return fig


def plot_race_wins_per_team(start_year, end_year):
    """
    Plots the cumulative wins by team from the specified start year to end year.

    Args:
        start_year (int): The starting year for the analysis.
        end_year (int): The ending year for the analysis.

    Returns:
        fig (go.Figure): The plot showing the cumulative wins by team.
    """
    
    race_winners_df = pd.read_csv('data/race_winners_1980_to_2024.csv', sep=',', encoding='utf-8')

    # Filter the DataFrame to include only the target years
    race_winners_df= race_winners_df[(race_winners_df['Season'] >= start_year) & (race_winners_df['Season'] <= end_year)]

    # Calculate the cumulative wins for each team
    team_wins = race_winners_df['Team'].value_counts().reset_index()
    team_wins.columns = ['Team', 'Wins']

    # Sort the teams by number of wins for better visualization
    team_wins = team_wins.sort_values(by='Wins', ascending=False)

    fig = go.Figure()

    # Get the colors of each team 
    for idx, row in team_wins.iterrows():
        try:
            team_name = row['Team']
            team_wins.at[idx, 'Color'] = fastf1.plotting.team_color(team_name)
        except Exception as e:
            print(f"Color could not be loaded for {team_name}: {e}")
            team_wins.at[idx, 'Color'] = 'white'

    fig.add_trace(go.Bar(
        x=team_wins['Team'],
        y=team_wins['Wins'],
        marker_color=team_wins['Color'],
        text=team_wins['Wins'],  # Add the win count as text
        textposition='inside',  # Position the text inside the bar
        insidetextanchor='middle'  # Center the text inside the bar
    ))

    fig.update_layout(
        title={'text': f'Cumulative Wins by Team from {start_year} to {end_year}', 'x': 0.5, 'xanchor': 'center'},
        xaxis_title='Team',
        yaxis_title='Wins',
        xaxis_tickangle=-45,
        plot_bgcolor='#1a1a1a',
        paper_bgcolor='#1a1a1a',
        font=dict(
            family="Arial",
            size=12,
            color="white"
        )
    )

    return fig


def plot_parallel_coordinates(event_name):
    """
    Plots a parallel coordinates chart for the given event name that contains multiple data, such as Qualifying position, 
    Compound strategy, Number of pitstops and Finish position in the race.

    Parameters:
    - event_name (str): The name of the event.

    Returns:
    - fig (go.Figure): The parallel coordinates chart figure.
    """

    # Get just the grand prix name without the year  
    name = event_name.split(":")[1].strip()

    df = get_parallel_coordinates_plot_dataset(event_name)

    # Get unique lists
    unique_lists = df['CompoundStrategy'].apply(tuple).unique().tolist()

    reduced_list = []

    # Get the first letter of each word in the list to reduce the space of the text
    for item in unique_lists:
        first_letters = [word[0] for word in item]
        reduced_list.append(first_letters)

    # Create a mapping from list to index
    unique_list_map = {tuple(lst): i for i, lst in enumerate(unique_lists)}

    # Replace lists in 'CompoundStrategy' with their index
    df['CompoundStrategyIndex'] = df['CompoundStrategy'].apply(lambda x: unique_list_map[tuple(x)])

    # Create a color scale using the 'FinishPosition' column mapped to range [1, 20]
    min_val = df['FinishPosition'].min()
    max_val = df['FinishPosition'].max()
    df['colorVal'] = 1 + (df['FinishPosition'] - min_val) * (19 / (max_val - min_val))

    # Flatten unique lists for ticktext
    unique_lists_str = [', '.join(lst) for lst in reduced_list]

    fig = go.Figure(data=
        go.Parcoords(
            line=dict(color=df['colorVal'],
                    colorscale=[[0, 'red'],[1, 'white']],  # White to red color scale
                    showscale=True,
                    cmin=1,
                    cmax=20),
            dimensions=[
                dict(range=[1, 20],
                    constraintrange=[1, 20],
                    label="Starting position", values=df['QualiPosition']),
                dict(tickvals=list(range(len(unique_lists))),
                    ticktext=unique_lists_str,
                    label='Compound Strategy', values=df['CompoundStrategyIndex']),
                dict(range=[0, df['Stops'].max() + 1],
                    tickvals=list(range(0, df['Stops'].max() + 1)),
                    label='Stops', values=df['Stops'],
                    ),

                dict(range=[1, 20],
                    label='Finish Position', values=df['FinishPosition'])
            ],
            unselected = dict(line = dict(color = 'green', opacity = 0.5)),
            customdata=df[['Driver']],
            
        )
    )

    fig.update_layout(
        title={
            'text': f'{name}: Compound and Stops Strategy Analysis',
            'x': 0.5,
            'xanchor': 'center',
            'font': {
                'size': 20,
                'color': 'white'
            }
        },
        plot_bgcolor='#1a1a1a',
        paper_bgcolor='#1a1a1a',
        font=dict(
            family="Arial",
            size=12,
            color="white"
        )
    )

    return fig