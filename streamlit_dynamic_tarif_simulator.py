#to run the app: streamlit run streamlit_test3.py

import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import datetime
import random as rnd

#home made:
from groupe_e_access_functions import *
#from meteo_access_functions import *
from solarsystem import *


#initialisation des variables d'état:
if "ran" not in st.session_state:
    st.session_state["ran"] = rnd.randint(1,10000)



def gen_number():
    st.session_state["ran"] = rnd.randint(1,10000)
    return


st.set_page_config(page_title="Albedo Engineering", page_icon='❄️',layout="wide")

# Title
st.title("📊 Battery Planner  with Dynamic Prices")


### Create sidebar
with st.sidebar:

    st.title("Simulation Parameter")
    # st.markdown("This is where you select the total number of randomly generated \
    # points you want to use to estimate what Pi is:")
    # iterations = st.number_input("Total Number of Points:", min_value=1,max_value= 10000, value=st.session_state["ran"])
    # st.button("Random number", on_click=gen_number)

    st.write(""" Dynamic prices of the Groupe-E, what do you want to display? """)

    tommorrow_checkbox = st.checkbox("Include tomorrow price prevision (after 18h)", key="graph_1")
    print("tommorrow_checkbox" , tommorrow_checkbox)

    number_of_days_user = st.number_input("Number of days in the past:", min_value=0,max_value= 200, value= 0)

    st.markdown("---")

    st.write("⏱️📈 Planification with simple charge and discharge setpoint")

    threshold_discharge = st.slider("⚡ Discharge when energy is expensive above (CHF/kWh): ", min_value=0.0, max_value=0.5, value=0.3, step=0.01)
    threshold_charge  = st.slider("⚡ Charge when energy is cheap below (CHF/kWh): ", min_value=0.0, max_value=0.5, value=0.2, step=0.01)
    st.write("between those levels nothing happens")

    st.markdown("---")
    st.write("🔋 Storage used for simulation")
    battery_size_kwh = st.slider("Battery capacity (kWh): ", min_value=1.0, max_value=20.0, value=10.0, step=1.0)
    battery_charge_power_kw = st.slider("Battery max charge power (kW): ", min_value=1.0, max_value=20.0, value=10.0, step=1.0)
    st.write("C/2 would be a reasonable charge/discharge limit, note it is applied all day")
    st.markdown("---")
    st.write("✌️ Moix P-O, 2025")


st.write("Visualizing daily electricity prices and planning **storage** with **solar power production** and **consumption** usage")

st.write("""
    - **Why?** price fluctuation will be a hot subject in the future morrow with increasing solar capacity distributed in the grid. 
    - **POC?** An proof of concept of next3 control done with the Vario dynamic price of the Groupe-E
    - **Design and Visuals?** I explore streamlit. Nice! Quickly put in place for simple interactive dashboards...
    - **Click here** if you want to know more about [Vario](https://www.groupe-e.ch/fr/energie/electricite/clients-prives/vario)""")

st.markdown("---")

st.write("The first example of use is simple, there is a threshold level to charge the battery when the energy is cheap and threshold to discharge when the energy is expensive. ")


#check of inputs
if number_of_days_user == None :
    number_of_days_in_past = 0
else:   
    number_of_days_in_past = int(number_of_days_user)


if tommorrow_checkbox:
    next_day_wanted = True
else:   
    next_day_wanted = False


# Current local datetime
now = datetime.datetime.now()
now_string_timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

#API to the electricity price:
df_price_varioplus = get_groupe_e_consumption_price(now, number_of_days_in_past, next_day_wanted)


    # #Two methods to create the figure: one with matplotlib that generate a png picture and one with plotly that generates an html to insert
    # #everything is stored in the static/image folder
    # plot_and_store_prices_picture(df_price_varioplus)
    # plot_and_store_prices_picture_plotly(df_price_varioplus)

print("Timestamp: " + now_string_timestamp)
    


length_profile = len(df_price_varioplus.index)

threshold_charge_profile = np.ones(length_profile)* threshold_charge
threshold_discharge_profile = np.ones(length_profile)* threshold_discharge

#Add the two columns to the dataframe:
df_price_varioplus["Charge"] = threshold_charge_profile 
df_price_varioplus["Discharge"] = threshold_discharge_profile 

#Activation orders:
df_price_varioplus["ChargeCommand"] = (df_price_varioplus["Charge"]  >= df_price_varioplus["Varioplus"]).astype(int)   #note, result is true/false, and .astype(int) convert to 1/0
df_price_varioplus["DischargeCommand"] = (df_price_varioplus["Discharge"]  <= df_price_varioplus["Varioplus"]).astype(int)



#And plot it:
fig_levels = px.line(df_price_varioplus, 
                            x=df_price_varioplus.index, 
                            y=["Varioplus", "Charge", "Discharge", "Double Tarif"], 
                            title="⚡ Electricity price with 💸 Prices Threshold", 
                            labels={"value": "Energy price (CHF/kWh)", "variable": "Legend"})
st.plotly_chart(fig_levels)

st.write("The comparison with the prices gives directly some setpoints for the battery. ")

#And plot it:
fig_activation = px.area(df_price_varioplus, 
                            x=df_price_varioplus.index, 
                            y=["ChargeCommand", "DischargeCommand"],
                            color_discrete_sequence=["lightblue", "lightcoral"], 
                            title="Charge and discharge activation 🕹️", 
                            labels={"value": "Activate", "variable": "Legend"}
                            )

# Move legend below the graph
fig_activation.update_layout(
    legend=dict(
        orientation="h",
        yanchor="top",
        y=-0.2,  # Position below the graph
        xanchor="center",
        x=0.1
    )
)
st.plotly_chart(fig_activation)

st.write("""How those order are applied to the real world?  Here a understanding of how the system work is necessary, the basic idea "charge when cheap, discharge when expensive" is just the surface of the problem.
         A few examples: """)
st.write("""
         - the battery is charged but maybe there is no consumption in the building to discharge that energy at the high peak time.
         - if there is solar energy, maybe it is best to let the battery be charged with solar than buying, even at low price.

         *Note:* Injecting stored energy in the grid is not allowed for the moment (in Switzerland) and there is no tariff for this.""")
st.write("""Here is a simulation on an real house load profile (real data but not time sychronised with tarif, just to see the behaviour) : """)


# Load Data
df_pow_profile = pd.read_csv("15min_pow.csv")

# Ensure 'Time' is a DateTime type#
df_pow_profile["Time"] = pd.to_datetime(df_pow_profile["Time"])

# # Show dataset preview
# st.write("📋 **Data Overview**")
# st.dataframe(df_pow_profile.head())

#take the data of the power profile with the same length as the simulation
pow_array_all = df_pow_profile["15min mean System Pout Consumption power (ALL) [kW]"].to_numpy()
pow_array = pow_array_all[-1-length_profile:-1]
#pow_array = df_pow_profile["15min mean System Pout Consumption power (ALL) [kW]"][:length_profile].to_numpy()
solar_array_all = df_pow_profile["15min mean Solar power (ALL) [kW]"].to_numpy()
solar_array = solar_array_all[-1-length_profile:-1]
#solar_array = df_pow_profile["15min mean Solar power (ALL) [kW]"][:length_profile].to_numpy()

#Add the column to the dataframe:
df_price_varioplus["Consumption"] = pow_array 
consumption_kWh = df_price_varioplus["Consumption"].sum()/4.0

df_price_varioplus["Solar"] = solar_array 

#and compute the price with that power profile
df_price_varioplus["PricePaidVario"] = (df_price_varioplus["Consumption"] * df_price_varioplus["Varioplus"]/4.0)   #note, result is true/false, and .astype(int) convert to 1/0
cost_normal_profile_with_vario = df_price_varioplus["PricePaidVario"].sum()
print("Price paid:", cost_normal_profile_with_vario)

df_price_varioplus["PricePaidDT"] = (df_price_varioplus["Consumption"] * df_price_varioplus["Double Tarif"]/4.0)   #note, result is true/false, and .astype(int) convert to 1/0
cost_normal_profile_with_dt = df_price_varioplus["PricePaidDT"].sum()
print("Price paid DT:", cost_normal_profile_with_dt)





st.markdown("---")

#########################################################################
#Now let's simulate the system with the solarsystem.py object:
solar_syst_Vex = SolarSystem("M-P-O","Impasse du Solaire 6, 2050 Transition" )

#and properties initialisation  
solar_syst_Vex.gps_location = [46.208, 7.394] 
solar_syst_Vex.pv_kW_installed = 9.24 #power installed on the roof
solar_syst_Vex.roof_orientation = -10 # 0=S, 90°=W, -90°=E, -180°=N (or -180)
solar_syst_Vex.roof_slope = 20.0
solar_syst_Vex.batt_capacity_kWh = battery_size_kwh #10*1 # in kWh
solar_syst_Vex.max_power_charge = battery_charge_power_kw #to update the max charge used by default independently of the battery size
solar_syst_Vex.max_power_discharge = -battery_charge_power_kw
solar_syst_Vex.max_inverter_power = 15 #kW
solar_syst_Vex.comment = "installed in June 2022"



#load data in the module for simulation without solar:
solar_syst_Vex.load_data_for_simulation(pow_array, solar_array*0.0, timestep=0.25)

# #Test of some control variable:
charge_command_array= df_price_varioplus["ChargeCommand"].to_numpy()
discharge_command_array= df_price_varioplus["DischargeCommand"].to_numpy()


#force charging on the grid:
solar_syst_Vex.delta_p_on_ac_source_profile = charge_command_array * battery_charge_power_kw
#let discharging only during this time:
solar_syst_Vex.battery_max_discharge_setpoint_profile = - discharge_command_array * battery_charge_power_kw


#and run the simulation of the system with the loaded datas:
solar_syst_Vex.run_storage_simulation()

#and retrieve the grid power and inject it in the vario dataframe:
grid_power_with_storage_array = solar_syst_Vex.net_grid_balance_profile
df_price_varioplus["Grid with storage"] = grid_power_with_storage_array 

soc_array = solar_syst_Vex.soc_profile
df_price_varioplus["SOC"] = soc_array 

#and compute the price with that power profile
df_price_varioplus["PricePaidVarioWithStorage"] = (df_price_varioplus["Grid with storage"] * df_price_varioplus["Varioplus"]/4.0)   #note, result is true/false, and .astype(int) convert to 1/0
cost_normal_profile_with_vario_with_storage = df_price_varioplus["PricePaidVarioWithStorage"].sum()
print("Price paid with storage:", cost_normal_profile_with_vario_with_storage)
consumption_kWh_with_storage = df_price_varioplus["Grid with storage"].sum()/4.0

# Energy Consumption Plot using Plotly
fig_simstorage_profile = px.line(df_price_varioplus, 
                        x=df_price_varioplus.index, 
                        y=[ "Consumption","Grid with storage"], 
                        title="⚡ Consumption from the grid", 
                        labels={"value": "Power (kW)", "variable": "Legend"},
)
    
# Move legend below the graph
fig_simstorage_profile.update_layout(
    legend=dict(
        orientation="h",
        yanchor="top",
        y=-0.2,  # Position below the graph
        xanchor="center",
        x=0.1
    )
)
st.plotly_chart(fig_simstorage_profile)


# Energy Consumption Plot using Plotly
fig_soc_profile = px.area(df_price_varioplus, 
                        x=df_price_varioplus.index, 
                        y=[ "SOC"], 
                        title=" 🔋 State of charge of the battery", 
                        labels={"value": "Power (kW)", "variable": "Consumption"}
)
    
# Move legend below the graph
fig_soc_profile.update_layout(
    legend=dict(
        orientation="h",
        yanchor="top",
        y=-0.2,  # Position below the graph
        xanchor="center",
        x=0.1
    )
)
st.plotly_chart(fig_soc_profile)



#st.write(" The cost of electricity for this period is " + str(cost_normal_profile_with_vario) + " CHF ")
st.write(f" The consumption of electricity for this period is {consumption_kWh:.2f} kWh without storage")
st.write(f"The cost of electricity is  {cost_normal_profile_with_vario:.2f} CHF with Vario without storage, mean price is {cost_normal_profile_with_vario/consumption_kWh:.3f} CHF/kWh")
st.write(f"The cost of electricity is  {cost_normal_profile_with_dt:.2f} CHF with Double tarif without storage")

st.write(f" The consumption of electricity for this period is {consumption_kWh_with_storage:.2f} kWh with storage")
st.write(f" The cost of electricity is  {cost_normal_profile_with_vario_with_storage:.2f} CHF with Vario with storage, mean price is {cost_normal_profile_with_vario_with_storage/consumption_kWh_with_storage:.3f} CHF/kWh")

#bilan batterie  
delta_e_batt=(soc_array[-1]-soc_array[0])/100.0*battery_size_kwh  #last SOC - first SOC of the simulation
#valorisé au prix moyen de la journée:
storage_value = delta_e_batt*np.mean(cost_normal_profile_with_vario_with_storage/consumption_kWh)
st.write(f" The states of charge of the battery at beggining ({soc_array[0]:.0f} %) and end of the period ({soc_array[-1]:.0f} %) are not the same, that is {delta_e_batt:.1f} kWh and must be counted in the final price. With mean price, its value is {storage_value:.2f} CHF")
st.write(f" The total gain with storage on vario tariff is {cost_normal_profile_with_vario - cost_normal_profile_with_vario_with_storage + storage_value:.2f} CHF")



st.write(f" Note: the selfconsumption power of storage system of 55W, that is 1.32 kWh/day")


st.markdown("---")

st.write("""
    Then to apply this strategy to the next3, transmit those orders with the API or locally with Modbus...
    - Without solar: give directly the power setpoint on the grid input (AC-Source) to force charging and set discharge current to 0 when you want to avoid discharge 
    - With solar: that is another story, see next chapter """)

st.markdown("---")

st.write(""" Second example With 🌞 Solar Production and storage 🔋
         
         This simulation is to come...
         In the best energy management requires an optimization to obtain good results.
         It's less obvious, but not rocket science ;-) """)








# Combined Solar Power and Energy Consumption Plot using Plotly
if "15min mean System Pout Consumption power (ALL) [kW]" in df_pow_profile.columns:
    fig_combined = px.line(df_pow_profile, x="Time", 
                            y=["15min mean Solar power (ALL) [kW]", "15min mean System Pout Consumption power (ALL) [kW]"], 
                            title="🌞 Solar Production vs ⚡ Energy Consumption", 
                            labels={"value": "Energy (kWh)", "variable": "Legend"},
                            color_discrete_sequence=["lightcoral", "lightblue"] )
    
    # Move legend below the graph
    fig_combined.update_layout(
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,  # Position below the graph
            xanchor="center",
            x=0.1
        )
    )
    st.plotly_chart(fig_combined)




st.markdown("---")

# Show dataset preview
st.write("📋 **Data Overview, for debug purpose**")
st.dataframe(df_price_varioplus.head())

st.dataframe(df_price_varioplus.tail())

