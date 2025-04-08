# -*- coding: utf-8 -*-
"""
Created on Mon Feb  5 17:36:18 2024
Mod: 27.05.2024
@author: pierre-olivier.moix
"""


#########
# Documentation about the groupe-e API is here:
#       https://www.groupe-e.ch/fr/energie/electricite/clients-prives/vario
#       https://groupee.sharepoint.com/sites/MediaPoint/Supports%20publicitaires/02_Fiches%20produits/Smart%20meter/vario-integration-web-api-fr.pdf?ga=1
#
# Comment consulter les prix du tarif Vario sur le WEB-API ?
#   Les détails techniques ci-dessous permettent à votre système de gestion énergétique de consulter les tarifs :
#   • URL : https://api.tariffs.groupe-e.ch
#   • Type de requête : HTTP GET
#   • Format des données : json
#   • Ressources :
#       o /v1/tariffs/vario_grid (uniquement le tarif réseau vario)
#       o /v1/tariffs/vario_plus (tarif vario intégré)
#       o /v1/tariffs/dt_plus (tarif double intégré)
#       o /v1/tariffs (tous les tarifs publiés sur la WEB API)
#   • Variables pour la période de requête (format ISO 8601) :
#       o start_timestamp=AAAA-MM-JJTHH:MM:SS+FF:ff
#       o end_timestamp=AAAA-MM-JJTHH:MM:SS+FF:ff
#   Exemple de requête pour le tarif vario_grid pour la journée du 06.09.2023 : (see document)
#
#####################################


#from datetime import date, datetime, timedelta
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px

import requests

#general constants
FIGSIZE_WIDTH = 7
FIGSIZE_HEIGHT = 5



def get_groupe_e_consumption_price(dt, number_of_days_in_past=0, next_day_wanted=False):
    '''
    Use of the API function to get the prices of today and if wanted of tomorrow and the past
    returns an pandas dataframe with the available informations.
    '''
    
    # ###########
    # # Current local datetime
    # now = datetime.now()
    
    today_em = dt #- datetime.timedelta(days=365) #for tests for a longer period
    begining_em = dt - datetime.timedelta(days=number_of_days_in_past) #for tests for a longer period

    if next_day_wanted == False: 
        #end the next day at 0h, that means it is not included
        tomorrow_em = dt + datetime.timedelta(days=1)  # now.astimezone(ZoneInfo("Europe/Madrid")).date()
    else:
        #end the next day at 23h59 or we can simply say the following at 0h to include tomorrow  
        tomorrow_em = dt + datetime.timedelta(days=2)  # now.astimezone(ZoneInfo("Europe/Madrid")).date()
    

    #TODO: check that everything concerning timezones is correct  WARNING: NO it is not! +1h in winter +2h in summer
    start_dt = today_em.strftime("%Y-%m-%dT00:00:00+01:00") #"%H:%M:%S+%F:%f")
    start_dt = begining_em.strftime("%Y-%m-%dT00:00:00+02:00") #"%H:%M:%S+%F:%f")
    end_dt = tomorrow_em.strftime("%Y-%m-%dT00:00:00+02:00") #with this, it ends tommorrow at 0h, that means the prices of tomorrow are not included
    
    
    ENDPOINT = 'https://api.tariffs.groupe-e.ch'
    ARCHIVE = '/v1/tariffs/vario_grid?start_timestamp={}&end_timestamp={}'  #date to be updated
    ARCHIVE = '/v1/tariffs?start_timestamp={}&end_timestamp={}'  #date to be updated
    
    API_URL = ENDPOINT+ARCHIVE
    price_unit = "CHF/kWh"
    
          
    # Prepare URL with date
    url = API_URL.format(start_dt,end_dt)
    
    # Make request to the API
    res = requests.get(url)
    
    # Check response status
    if res.status_code != 200:
        raise Exception(res.reason)
    
    # Read response data to get the PVPC prices (in €/MWh)
    data = res.json()
      
    price_variogrid = []
    price_varioplus = []
    price_dt_plus = []
    time_resp = []
    
    #print(' \n *** Prices for electricity retail Variogrid of GROUPE-E:')   
    for hour_slice in data: 
        #print( hour_slice['start_timestamp']  + ' ' +  str(hour_slice['vario_grid']) + '  ' + hour_slice["unit"])
        
        #Create a dictionnary with the data:
        hour_slice["vario_grid"] #for ESIOS: peninsula, canarias, balear
    
        #hour_slice['Dia']  + ' ' +  hour_slice['Hora'] + '  ' + 
        price_varioplus.append(float(hour_slice["vario_plus"])/100) #with conversion from ct/kWh to CHF/kWh)
        price_dt_plus.append(float(hour_slice["dt_plus"])/100) #with conversion from ct/kWh to CHF/kWh)
        price_variogrid.append(float(hour_slice["vario_grid"])/100) #with conversion from ct/kWh to CHF/kWh)
    
        time_resp.append(hour_slice['start_timestamp'] ) #+ ' ')      
    

    #let's read the timestamp and convert it to datetime:
    #print(time_resp)

    #The format is:2024-05-31T19:30:00+02:00 # Warning there is a space at the end
    #test=datetime.datetime.fromisoformat('2011-11-04T00:05:23+04:00')  

    fmt = "%Y-%m-%dT%H:%M:%S%z"
    mydateparser = lambda x: datetime.datetime.strptime(x, fmt)

    timestamps_converted = []
    for timestamp in time_resp:
        #one_ts_converted = datetime.datetime.fromisoformat(timestamp)  #other method tried
        #one_ts_converted = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S%z") #other method tried
        timestamps_converted.append(mydateparser(timestamp))
    #print(timestamps_converted)

    #plotly use pandas dataframes to handle data, so let's recreate one that is a proper time serie:
    time_quarters = np.arange(0,len(price_varioplus)/4,0.25) #that is the time in hours
    df_price_varioplus = pd.DataFrame({"Varioplus":price_varioplus, "Double Tarif": price_dt_plus,"Time in hours":time_quarters}, index=timestamps_converted)


    return df_price_varioplus 
    
    #return price_varioplus, price_dt_plus, time_resp





def plot_and_store_prices_picture(df_price_varioplus): 
    '''
    An matplotlib figure is created and saved in png format to be displayed in the web page
    '''
    
    now = datetime.datetime.now()
    fig_prices, axes_prices = plt.subplots(nrows=1, 
                                ncols=1,
                                figsize=(FIGSIZE_WIDTH, FIGSIZE_HEIGHT))
    

    axes_prices.plot(df_price_varioplus['Time in hours'].values, df_price_varioplus[["Double Tarif", "Varioplus"]].values) #,color='b'
    axes_prices.set_ylabel('Price [CHF/kWh]', fontsize=12)
    axes_prices.set_xlabel('Time [h]', fontsize=12)
    axes_prices.set_title('Dynamic tariff Groupe-E, today: '+str(now)[0:10], fontsize=12, weight="bold")
    axes_prices.grid(True) 

    fig_prices.savefig("static/images/prices/last_elec_price_groupe_e.png")
    
    #return the fig for reuse:
    return fig_prices



def plot_and_store_prices_picture_plotly(df_price_varioplus):  
    '''
    Here 2 plots in plotly format are realised and saved in an html file
    One is returned for display in tests
    '''
    #now = datetime.datetime.now()
    fig_prices = px.line(df_price_varioplus,  y=["Double Tarif", "Varioplus"],
                         labels={"index" : "", 
                                 "value" : "Electricity price [CHF/kWh]",
                                 "Double Tarif": "Standard double tarif [CHF/kWh]",
                                 "Varioplus" : "Dynamic price [CHF/kWh]"
                                 },
                         title="Groupe-E variable electricity price",
                         template="seaborn"
                        )  


    #test with histogram
    fig_prices2 = px.scatter(df_price_varioplus, y="Varioplus", marginal_y="histogram",
                         labels={"index" : "", 
                                 "Varioplus" : "Electricity price [CHF/kWh]"
                                 },
                         title="Groupe-E variable electricity price",
                         template="seaborn" #"seaborn" "plotly_dark" 
                        )                          #"seaborn"


    fig_prices.write_html("static/images/prices/last_elec_price_groupe_e.html")
    fig_prices2.write_html("static/images/prices/last_elec_price_groupe_e_histo.html")

    #return one of the fig for reuse:
    return fig_prices



def main():
    #The main here is for tests and example of the request functions
    
    ###########
    # Current local datetime
    now = datetime.datetime.now()
    number_of_days_in_past = 1
    next_day_wanted = True
    df_price_varioplus = get_groupe_e_consumption_price(now, number_of_days_in_past, next_day_wanted)
    
    price_varioplus = df_price_varioplus['Varioplus'].values
    price_dt_plus = df_price_varioplus['Double Tarif'].values
    time_resp= df_price_varioplus['Time in hours'].values

    print(time_resp[0:5])
    print("Last point: ")
    print(time_resp[-1])
    
    
    #create the figures and the html for plotly:
    fig_prices = plot_and_store_prices_picture(df_price_varioplus)
    fig_prices_plotly = plot_and_store_prices_picture_plotly(df_price_varioplus)

    plt.show() #for matplotlib

    fig_prices_plotly.show() # for plotly





##################################
if __name__ == "__main__":
    main()
	
    
    



