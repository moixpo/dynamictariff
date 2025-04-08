#meteo_access_functions.py

#Started with an example directly taken from: https://open-meteo.com/en/docs#latitude=46.2291&longitude=6.9501&minutely_15=&hourly=temperature_2m,direct_radiation_instant,diffuse_radiation_instant,global_tilted_irradiance_instant&past_days=1&forecast_days=3&tilt=25&azimuth=-7
#adaptation and additions of the plots with matplotlib
#Moix P-O 21 may 2024 for the TCC course


import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
import datetime

#for displaying figures:
import matplotlib.pyplot as plt

#general constants:
FIGSIZE_WIDTH = 8
FIGSIZE_HEIGHT = 6
PV_INSTALLED = 9.24 #kWp  constant for tests, that will come from the user data
FILE_NAME_FOR_PREDICTIONS = "saved_meteo predictions.csv"


def get_meteo_forecast(params, installed_kwp):
    '''
    The input parameters are given in a dict with that format:
        params = {
         "latitude": 46.2291,
         "longitude": 6.9501,
         "hourly": ["temperature_2m", "direct_radiation_instant", "diffuse_radiation_instant", "global_tilted_irradiance_instant"],
         "past_days": 1,
         "forecast_days": 3,
         "tilt": 25,
         "azimuth": -7
        }

    The  return is a dataframe with the meteo forcast 

    '''



    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"
    # params = {
    #     "latitude": 46.2291,
    #     "longitude": 6.9501,
    #     "hourly": ["temperature_2m", "direct_radiation_instant", "diffuse_radiation_instant", "global_tilted_irradiance_instant"],
    #     "past_days": 1,
    #     "forecast_days": 3,
    #     "tilt": 25,
    #     "azimuth": -7
    # }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_direct_radiation_instant = hourly.Variables(1).ValuesAsNumpy()
    hourly_diffuse_radiation_instant = hourly.Variables(2).ValuesAsNumpy()
    hourly_global_tilted_irradiance_instant = hourly.Variables(3).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
        end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = hourly.Interval()),
        inclusive = "left"
    )}
    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["direct_radiation_instant"] = hourly_direct_radiation_instant
    hourly_data["diffuse_radiation_instant"] = hourly_diffuse_radiation_instant
    hourly_data["global_tilted_irradiance_instant"] = hourly_global_tilted_irradiance_instant

    hourly_dataframe = pd.DataFrame(data = hourly_data, index = hourly_data["date"])


    
    #******* PV PREDICTION  ******** 
    #create a new column in the dataframe with the estimation:
    pv_production_prediction=hourly_dataframe[hourly_dataframe.columns[4]].values*installed_kwp/1000.0

    #and add it to the dataframe:
    #Create a new entry called PV production estimation [kW]
    hourly_dataframe['PV production estimation [kW]']=pv_production_prediction
        
    #print(hourly_dataframe)

    return hourly_dataframe




def plot_meteo_forcast(hourly_dataframe):


    now = datetime.datetime.now()


    #******* Irradiance PREDICTION FIGURE ********
    fig_irrad_data, [axes_irrad_data, axes_production_estimation] = plt.subplots(nrows=2, 
                                ncols=1,
                                figsize=(FIGSIZE_WIDTH, FIGSIZE_HEIGHT))
    
    #plot the irradiance:
    hourly_dataframe.plot(y=hourly_dataframe.columns[2:5],
                            grid=True,
                            ax=axes_irrad_data)

    axes_irrad_data.axvline(now, color='b', alpha=0.5, linestyle='dashed', linewidth=2)

    axes_irrad_data.legend(["Direct", "Diffuse", "Global tilt"])
    axes_irrad_data.set_ylabel('Irradiance [W/m2]', fontsize=12)
    #axes_irrad_data.set_xlabel('hours', fontsize=12) 

    axes_irrad_data.set_title('Irradiance (from openmeteo)', fontsize=12, weight="bold")
    axes_irrad_data.grid(True) 


    #and then plot the estimated PV production:
    hourly_dataframe.plot(y='PV production estimation [kW]',
                            grid=True,
                            ax=axes_production_estimation,
                            color='r',
                            legend="Solar prod estimations")
    
    axes_production_estimation.axvline(now, color='b', alpha=0.5, linestyle='dashed', linewidth=2)
    axes_production_estimation.set_ylabel('Solar power [kW]', fontsize=12, color='r')
    axes_production_estimation.set_xlabel('hours', fontsize=12)
    axes_production_estimation.legend(["Solar prod estimations", "now"])
    
    #save the figure in a file:
    fig_irrad_data.savefig("static/images/meteo/last_meteo.png")

    return fig_irrad_data









if __name__ == "__main__":

    #here the script for tests of the functions defined here above:

    plt.close("all")
    now = datetime.datetime.now()



    params = {
        "latitude": 46.2291,
        "longitude": 6.9501,
        "hourly": ["temperature_2m", "direct_radiation_instant", "diffuse_radiation_instant", "global_tilted_irradiance_instant"],
        "past_days": 1,
        "forecast_days": 5,
        "tilt": 25,
        "azimuth": -7
    }

    hourly_dataframe = get_meteo_forecast(params, PV_INSTALLED)


    #print(hourly_dataframe)
    fig_irrad_data = plot_meteo_forcast(hourly_dataframe)
    


    #******* TEMPERATURE FIGURE ********
    #this one is not used in the website, just to see it:
    fig_temp_data, axes_temp_data = plt.subplots(nrows=1, 
                                ncols=1,
                                figsize=(FIGSIZE_WIDTH, FIGSIZE_HEIGHT))

    hourly_dataframe.plot(y=hourly_dataframe.columns[1],
                            grid=True,
                            title='temperature data',
                            ax=axes_temp_data,
                            color='r')
    axes_temp_data.axvline(now, color='b', alpha=0.5, linestyle='dashed', linewidth=2)

    axes_temp_data.set_ylabel('Temperature [°C]', fontsize=12)
    axes_temp_data.set_title('Temperature data from openmeteo', fontsize=12, weight="bold")
    axes_temp_data.grid(True) 


    #save the data in a csv file for an later display of the evolution of the prediction
    #FILE_NAME_FOR_PREDICTIONS = "saved_meteo predictions.csv"
    
    # Format the date and time
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

    # Define the filename with timestamp
    filename = f"saved_meteo_predictions_{timestamp}.csv"

    # Export DataFrame to CSV
    hourly_dataframe.to_csv(filename, index=False)
    
    #finally display it all:
    plt.show()

	