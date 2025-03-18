
from datetime import datetime, timedelta 
import pandas as pd
import pycountry
import os
import plotly.graph_objects as go

import contextlib
import io

buffer = io.StringIO()
with contextlib.redirect_stdout(buffer):  
    import fastf1
    import fastf1.plotting


# Enabling the cache system in a specific folder
#fastf1.Cache.enable_cache('cache') 

def get_drivers_short_name(session: fastf1.core.Session):
    """
    Returns a list of short names of drivers in the given session.

    Parameters:
    - session: A fastf1.core.Session object representing the F1 session.

    Returns:
    - driver_list: A list of short names of drivers in the session.
    """
    driver_list = []
    for drv in session.drivers:
        drv_laps = session.laps.pick_driver(drv)
        abbreviation = drv_laps['Driver'].iloc[0]
        driver_list.append(abbreviation)
    return driver_list


def get_driver_team_and_color(session, driver_abbr):
    """
    Retrieves the team name and color for a given driver abbreviation.

    Parameters:
    - session: The F1 session object.
    - driver_abbr: The abbreviation of the driver.

    Returns:
    - team_name: The name of the driver's team.
    - team_color: The color associated with the driver's team.
    """
    # Get the driver information from the session
    driver_info = session.get_driver(driver_abbr)
    
    # Extract team name
    team_name = driver_info['TeamName']
    
    # Get team colors using the plotting module
    team_color = fastf1.plotting.team_color(team_name)
    
    return team_name, team_color

def get_driver_full_name(session, driver_abbr):
    """
    Retrieves the full name of a driver based on their abbreviation.

    Args:
        session (Session): The session object used to interact with the F1 API.
        driver_abbr (str): The abbreviation of the driver.

    Returns:
        str: The full name of the driver.
    """
    driver_info = session.get_driver(driver_abbr)
    return driver_info['LastName']


from datetime import datetime, timedelta

def events_of_last_n_year(n_years: int):
    """
    Retrieves the names of Formula 1 events from the last n years.

    Args:
        n_years (int): The number of years to retrieve events from.

    Returns:
        list: A list of event names in the format "year: event_name".
    """
    event_name_list = []
    current_year = datetime.now().year

    for year in reversed(range(current_year - n_years, current_year + 1)):
        schedule = fastf1.get_event_schedule(year)
        
        # Sort schedule DataFrame by 'EventDate' in descending order
        schedule_sorted = schedule.sort_values(by='EventDate', ascending=False)
        
        for _, row in schedule_sorted.iterrows():
            if row['EventDate'] < (datetime.now() - timedelta(days=1)):
                event_name_list.append(f"{year}: {row['EventName']}")
        
    return event_name_list


def get_sessions_names_of_event(event_name: str):
    """
    Retrieves the session data for a given event.

    Parameters:
    event_name (str): The name of the event in the format 'year: name'.

    Returns:
    list: A list of session data for the event, in reverse order.
    """

    name = event_name.split(":")[1].strip()
    year = int(event_name.split(":")[0].strip())

    session_data = fastf1.get_event(year, name)

    session_list = []
    for i in reversed(range(0, 5)):
        session_list.append(session_data['Session' + str(i + 1)])

    return session_list


def load_session(event_name, session_name):
    """
    Load the specified session for a given event.

    Parameters:
    - event_name (str): The name of the event in the format "year: name".
    - session_name (str): The name of the session to load.

    Returns:
    - session: The loaded session object.
    """
    name = event_name.split(":")[1].strip()
    year = int(event_name.split(":")[0].strip())

    session = fastf1.get_session(year, name, session_name)
    session.load()

    return session


def get_avg_speed_between_corners(session, driver_abbr):
    """
    Calculate the average speed between corners for a given driver in a session.

    Args:
        session (Session): The session object containing lap and telemetry data.
        driver_abbr (str): The abbreviation of the driver.

    Returns:
        DataFrame: A DataFrame containing the average speed, corner number, start distance, and end distance for each corner.
    """
    
    lap = session.laps.pick_driver(driver_abbr).pick_fastest()
    telemetry = lap.get_car_data().add_distance()
    circuit_info = session.get_circuit_info()
    ticks_list = []

    avg_speed_x_corner = []
    start = 0
    end = 0

    df = pd.DataFrame(columns=['avg_speed', 'corner_number','start_dist', 'end_dist'])
    for _, corner in circuit_info.corners.iterrows():
        ticks = 0
        avg_speed_accumulator = 0
        
        for telemetry_tick in telemetry.iterrows():
            
            if telemetry_tick[1]['Distance'] > corner['Distance']:
                ticks_list.append(ticks)
                df.loc[corner['Number']] = [round(avg_speed_accumulator/ticks, 2)] + [int(corner['Number'])] + [start] + [end] #saves everything in dataframe
                start = end
                break
            elif telemetry_tick[1]['Distance'] > start:
                avg_speed_accumulator += telemetry_tick[1]['Speed']
                ticks += 1
                end = telemetry_tick[1]['Distance']
    
    return df


def get_avg_speed_diff_drivers(session, driver_abbr1, driver_abbr2):
    """
    Calculates the average speed difference between two drivers for each corner.

    Args:
        session (str): The session identifier.
        driver_abbr1 (str): The abbreviation of the first driver.
        driver_abbr2 (str): The abbreviation of the second driver.

    Returns:
        pandas.DataFrame: A DataFrame containing the average speed difference between the two drivers for each corner.
    """
    df1 = get_avg_speed_between_corners(session, driver_abbr1)
    df2 = get_avg_speed_between_corners(session, driver_abbr2)
    
    df1 = df1.rename(columns={'avg_speed': f'{driver_abbr1}_avg_speed'})
    df2 = df2.rename(columns={'avg_speed': f'{driver_abbr2}_avg_speed'})
    df2.drop(columns=['corner_number'], inplace=True)
    df = pd.concat([df1, df2], axis=1)
    df['speed_diff'] = (df[f'{driver_abbr1}_avg_speed'] - df[f'{driver_abbr2}_avg_speed'])
    return df



def convert_timedelta_to_datetime(data : pd.core.series.Series):
    """
    Converts a series of timedelta values to datetime objects.

    Args:
        data (pd.core.series.Series): A series of timedelta values.

    Returns:
        list: A list of datetime objects converted from the timedelta values.
    """
    converted_lap_time = []
    reference_datetime = datetime(2024, 1, 1, 0, 0, 0)

    for t in data:
        datetime_result = reference_datetime + t
        formatted_time_as_str = datetime_result.strftime("%M:%S.%f")[:-3] # Converting first the Timedelta to a String
        datetime_converted = datetime.strptime(formatted_time_as_str, "%M:%S.%f")
        converted_lap_time.append(datetime_converted)
        
    return converted_lap_time


def create_race_winners_dataset():
    """
    Creates a dataset of race winners from 1980 to 2024.

    This function retrieves the race results for each season from 1980 to 2024,
    extracts the winner of each race, and stores the results in a DataFrame.
    The DataFrame is then saved to a CSV file.

    Returns:
        None
    """
    # Enable caching 
    fastf1.Cache.enable_cache('cache') 

    # Initialize an empty list to store the race results
    all_race_results = []

    # Iterate over each season from 1980 to 2024
    for season in range(1980, 2024 + 1):
        try:
            # Get the schedule for the current season
            schedule = fastf1.get_event_schedule(season)
            
            # Iterate over each event in the schedule
            for index, event in schedule.iterrows():
                try:
                    # Load the race session
                    race = fastf1.get_session(season, event['EventName'], 'R')
                    race.load()  # Load the session data
                    
                    # Extract the winner
                    winner = race.results.iloc[0]
                    all_race_results.append({
                        'Season': season,
                        'Race': event['EventName'],
                        'Winner': winner['FullName'],
                        'Team': winner['TeamName']
                    })
                except Exception as e:
                    print(f"Could not load data for {event['EventName']} in {season}: {e}")
        except Exception as e:
            print(f"Could not load schedule for {season}: {e}")

    # Convert the results to a DataFrame
    race_winners_df = pd.DataFrame(all_race_results)

    # Save the DataFrame to a CSV file
    race_winners_df.to_csv('data/race_winners_1980_to_2024.csv', index=False)


def create_race_calendar_dataset():
    """
    Creates a race calendar dataset by retrieving event schedules for each year from 1980 to 2024.
    
    Returns:
        None
    """
    df = pd.DataFrame()
    for i in range(1980, 2025):
        temp_df = pd.DataFrame()
        temp_schedule = fastf1.get_event_schedule(i)
        temp_df['Country'] = temp_schedule['Country']
        temp_df['Location'] = temp_schedule['Location']
        temp_df['EventDate'] = temp_schedule['EventDate']
        temp_df['EventName'] = temp_schedule['EventName']
        temp_df['OfficialEventName'] = temp_schedule['OfficialEventName']
        df = pd.concat([df, temp_df])

    df.to_csv('data/schedule1980-2024.csv', sep=';', encoding='utf-8', index=False)


import pycountry

def get_iso_code(country_name):
    """
    Retrieves the ISO code for a given country name.

    Parameters:
        country_name (str): The name of the country.

    Returns:
        str: The 3-letter ISO code for the country, or None if the country name is not found.
    """
    try:
        country = pycountry.countries.lookup(country_name)
        return country.alpha_3 # 3 letters ISO code
    except LookupError:
        return None
    

def get_country_counts_ISO(start_year: int, end_year: int):
    """
    Retrieves the count of unique occurrences of each country in a given time range,
    along with their ISO codes.

    Args:
        start_year (int): The starting year of the time range.
        end_year (int): The ending year of the time range.

    Returns:
        pandas.DataFrame: A DataFrame containing the country names, their counts,
        and their ISO codes.
    """
    df = pd.read_csv('data/schedule1980-2024.csv', sep=';', encoding='utf-8')

    df['EventDate'] = pd.to_datetime(df['EventDate'])  # Convert to datetime
    df = df[(df['EventDate'].dt.year >= start_year) & (df['EventDate'].dt.year <= end_year)]

    # Count unique occurrences of each country
    country_counts = df['Country'].value_counts()

    # Convert the series to a dataframe
    country_counts_df = country_counts.reset_index()

    country_counts_df.columns = ['Country', 'Count']

    for index, row in country_counts_df.iterrows():
        country_counts_df.at[index, 'ISO'] = get_iso_code(row['Country'])

    country_counts_df = country_counts_df.dropna(subset=['ISO'])

    return country_counts_df


def get_parallel_coordinates_plot_dataset(event_name):
    """
    Retrieves the dataset for creating a parallel coordinates plot for a given F1 event.

    Parameters:
    event_name (str): The name of the F1 event in the format 'year: name'.

    Returns:
    pandas.DataFrame: The dataset containing driver information, stint details, compound strategy, qualifying position, and finishing position.
    """

    name = event_name.split(":")[1].strip()
    year = int(event_name.split(":")[0].strip())

    session_race = fastf1.get_session(year, name, 'R')
    session_race.load()
    
    laps = session_race.laps

    drivers = session_race.drivers # Get drivers numbers

    drivers = [session_race.get_driver(driver)["Abbreviation"] for driver in drivers] #Convert numbers to abbreviation

    # Get driver with stint and compound information
    stints = laps[["Driver", "Stint", "Compound", "LapNumber"]]
    stints = stints.groupby(["Driver", "Stint", "Compound"])
    stints = stints.count().reset_index()
    stints = stints.rename(columns={"LapNumber": "StintLength"})


    #Converting fastf1 format to dataframe
    df = pd.DataFrame(columns=["Driver", "Stint", "Compound", "StintLength"])
    for driver in drivers:
        driver_stints = stints.loc[stints["Driver"] == driver]
        df = pd.concat([df, driver_stints])

    #Creating a new dataframe to store the compound strategy for each driver
    df2 = pd.DataFrame(columns=["Driver", "Stops", "CompoundStrategy"])

    ####Getting the compound strategy for each driver with the number of stops####
    for row in df.iterrows():
        driver = row[1]["Driver"]
        stint = row[1]["Stint"]
        compound = row[1]["Compound"]

        stops = (df.loc[df["Driver"] == driver]["Stint"].max()) - 1 # -1 because the first stint is not a pitstop
        compound_strategy = df.loc[df["Driver"] == driver]["Compound"].to_list()
        df2.loc[len(df2)] = [driver, int(stops), compound_strategy]
    
    df2 = df2.drop_duplicates(subset=["Driver"])


    session_quali = fastf1.get_session(year, name, 'Q')
    session_quali.load()

    # Create a list of dictionaries with driver abbreviations and positions
    data = [{'Driver': driver, 'QualiPosition': i} for i, driver in enumerate(session_quali.results['Abbreviation'], 1)]

    # Convert the list of dictionaries to a DataFrame
    qualifying_results = pd.DataFrame(data)

    session_race = fastf1.get_session(year, name, 'R')
    session_race.load()

    data = [{'Driver': driver, 'FinishPosition': i} for i, driver in enumerate(session_race.results['Abbreviation'], 1)]

    race_results = pd.DataFrame(data)

    merged_df = pd.merge(df2, qualifying_results, on="Driver")
    merged_df = pd.merge(merged_df, race_results, on="Driver")

    # Sort the DataFrame by QualiPosition from first to last
    sorted_merged_df = merged_df.sort_values('QualiPosition')
  
    return sorted_merged_df

def create_black_figure():
    """
    Create a black figure with the specified color.

    Returns:
        fig (go.Figure): The black figure with the specified color.
    """
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor='#1a1a1a',  # Background color of the figure
        plot_bgcolor='#1a1a1a',   # Background color of the plot
        xaxis=dict(showgrid=False),  # Hide gridlines
        yaxis=dict(showgrid=False)   # Hide gridlines
    )
    return fig


