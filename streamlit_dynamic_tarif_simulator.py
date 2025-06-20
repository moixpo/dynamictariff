#to run the app: streamlit run streamlit_test3.py

import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import datetime
import random as rnd

#home made import:
from groupe_e_access_functions import *
#from meteo_access_functions import *
from solarsystem import *


# #initialisation des variables d'état:
# if "ran" not in st.session_state:
#     st.session_state["ran"] = rnd.randint(1,10000)


# def gen_number():
#     st.session_state["ran"] = rnd.randint(1,10000)
#     return


st.set_page_config(page_title="Albedo Engineering", page_icon='❄️',layout="wide")

# Title
st.title("📊 Dynamic Electricity Prices with Solar and Storage")


### Create sidebar with the options for simulation
with st.sidebar:

    st.title("Simulation Parameters")
    # st.markdown("This is where you select the total number of randomly generated \
    # points you want to use to estimate what Pi is:")
    # iterations = st.number_input("Total Number of Points:", min_value=1,max_value= 10000, value=st.session_state["ran"])
    # st.button("Random number", on_click=gen_number)

    st.write(""" Dynamic prices of the Groupe-E, what do you want to display? """)

    tommorrow_checkbox = st.checkbox("Include tomorrow price prevision (after 18h)", key="graph_1")
    print("tommorrow_checkbox" , tommorrow_checkbox)

    number_of_days_user = st.number_input("Number of days in the past:", min_value=0,max_value= 365, value= 0)

    st.markdown("---")

    st.write("⏱️📈 Planification with simple charge and discharge setpoint")

    threshold_discharge = st.slider("⚡ Discharge when energy is expensive above (CHF/kWh): ", min_value=0.0, max_value=0.5, value=0.25, step=0.01)
    threshold_charge  = st.slider("⚡ Charge when energy is cheap below (CHF/kWh): ", min_value=0.0, max_value=0.5, value=0.17, step=0.01)
    st.write("between those levels nothing happens")

    st.markdown("---")
    st.write("🔋 Storage used for simulation")
    battery_size_kwh = st.slider("Battery capacity (kWh): ", min_value=1.0, max_value=20.0, value=10.0, step=1.0)
    battery_charge_power_kw = st.slider("Battery max charge power (kW): ", min_value=1.0, max_value=20.0, value=10.0, step=1.0)
    st.write("C/2 would be a reasonable charge/discharge limit, note it is applied all day")
    soc_init = st.slider("Battery initial SOC (%): ", min_value=20.0, max_value=100.0, value=20.0, step=1.0)

    st.markdown("---")
    st.write("Scale solar used for simulation, original (100%) is a 10kWp installation")
    solar_scale = st.slider("🌞 Solar insalled (%): ", min_value=10.0, max_value=200.0, value=100.0, step=10.0)
    st.markdown("---")

    st.write("✌️ Moix P-O, 2025")
    st.write("I explored streamlit. Nice! Quite easily put in place for simple interactive dashboards...")


st.write(""" Visualizing daily electricity prices and planning **storage** with **solar** power production and **consumption** usage
    - **Why?** Dynamic price will be a hot subject in the future with increasing solar production capacity distributed in the grid. There will be so much production in the afternoon that the way we consume must be adapted. Live with the sun... 
    - **POC?** An proof of concept of what could be done with Studer next3 hybrid inverter (best and most flexible inverters in the world to control!). The idea is to quantify the possible gain of an control done with the dynamic price of the Swiss DSO Groupe-E (called Vario). This is available with an API and published everyday at 18h for the next day.
    - **Info?** if you want to know more about [Vario](https://www.groupe-e.ch/fr/energie/electricite/clients-prives/vario)""")

st.markdown("---")

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


print("Timestamp: " + now_string_timestamp)
#df_price_varioplus.head()
#st.dataframe(df_price_varioplus.head())


#create the control vectors with the same lenght:
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





##########################################
#Let's simulate with a battery:
##############

st.subheader(" The battery alone")
st.write("The first use case is simple: you discovered that during the day there are some hours with cheap electricity and some with expensive. And you wonder: 💡 if I had a battery I would charge at low price and use it during the rest of the day! Then I would spare money! ")
            
st.write("**How much?**  Let's simulate")  
st.write("A threshold level to charge the battery when the energy is cheap and threshold to discharge when the energy is expensive. The comparison directly gives some setpoints for the battery.")



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
         - if there is solar energy, maybe it is best to let the battery be charged with solar than buying, even at low price.""")

st.write("""Let's see below the simulation on an real house load profile with the activation orders computed above. Change the simuation parameters on the left (period of simulation, size of battery,..): """)


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





#st.markdown("---")

#########################################################################
#Now let's simulate the system with the solarsystem.py object:
solar_syst_Vex = SolarSystem("M-P-O","Impasse du Solaire 6, 2050 Transition" )

#and properties initialisation  
solar_syst_Vex.gps_location = [46.208, 7.394] 
solar_syst_Vex.pv_kW_installed = 9.24 #power installed on the roof
solar_syst_Vex.roof_orientation = -10 # 0=S, 90°=W, -90°=E, -180°=N (or -180)
solar_syst_Vex.roof_slope = 20.0
solar_syst_Vex.batt_capacity_kWh = battery_size_kwh #10*1 # in kWh
solar_syst_Vex.soc_init = soc_init # in %
solar_syst_Vex.max_power_charge = battery_charge_power_kw #to update the max charge used by default independently of the battery size
solar_syst_Vex.max_power_discharge = -battery_charge_power_kw
solar_syst_Vex.max_inverter_power = 15 #kW  for the next3
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



#bilan batterie  
delta_e_batt=(soc_array[-1]-soc_array[0])/100.0*battery_size_kwh  #last SOC - first SOC of the simulation
#valorisé au prix moyen de la journée:
mean_price_vario_with_storage = cost_normal_profile_with_vario_with_storage/consumption_kWh_with_storage
storage_value = delta_e_batt * mean_price_vario_with_storage # np.mean(cost_normal_profile_with_vario_with_storage/consumption_kWh)

gain_dt_to_vario = cost_normal_profile_with_dt - cost_normal_profile_with_vario_with_storage + storage_value


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
                        labels={"value": "State of charge (%)", "variable": "Consumption"}
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
st.write(" **Some results**")
st.markdown(f""" Reference
    - The consumption of electricity for this period is {consumption_kWh:.2f} kWh 🔌
    - The cost of electricity is  {cost_normal_profile_with_dt:.2f} CHF with Double tariff without storage
    - The cost of electricity is  {cost_normal_profile_with_vario:.2f} CHF with Vario without storage, mean price is {cost_normal_profile_with_vario/consumption_kWh:.3f} CHF/kWh""")

st.markdown(f""" 🔋 With storage controled in price signal:
    - The consumption of electricity on the grid for this period is {consumption_kWh_with_storage:.2f} kWh with storage
    - The cost of electricity from grid is  {cost_normal_profile_with_vario_with_storage:.2f} CHF with Vario with storage, mean price is {cost_normal_profile_with_vario_with_storage/consumption_kWh_with_storage:.3f} CHF/kWh
    - The states of charge of the battery at beggining ({soc_array[0]:.0f} %) and end of the period ({soc_array[-1]:.0f} %) are not the same, that is {delta_e_batt:.1f} kWh and must be counted in the final price. 
    - The value of the stored energy left in the battery with mean price is {storage_value:.2f} CHF
    - **TOTAL gain** with storage and use of vario tariff is {gain_dt_to_vario:.2f} CHF, that is  {( gain_dt_to_vario / cost_normal_profile_with_dt * 100.0) : .1f} % gain """)
   


#st.metric(label="gain with storage", value=4, delta=-0.5, delta_color="inverse")


st.write(f" Note: the selfconsumption power of storage system of 55W, that is 1.32 kWh/day. Plus there is an efficiency of 0.95 counted.")



st.markdown("---")




######################################
#Lets study the impact of solar in conjunction with the Vario tariff

st.title("🌞 Solar impact")


st.write("Lets study the impact of solar in conjunction with the Vario tariff")


#reload the data with solar production:
solar_syst_Vex.load_data_for_simulation(pow_array, solar_array * solar_scale/100.0, timestep=0.25)

solar_syst_Vex.run_simple_simulation()


#and retrieve the grid power and inject it in the vario dataframe:
grid_power_with_solar_array = solar_syst_Vex.net_grid_balance_profile
grid_power_pos_with_solar_array = grid_power_with_solar_array.copy()
grid_power_pos_with_solar_array[grid_power_pos_with_solar_array < 0] = 0

df_price_varioplus["Grid with solar only"] = grid_power_with_solar_array 
df_price_varioplus["Grid pos with solar only"] = grid_power_pos_with_solar_array 


#and compute the price with that power profile
df_price_varioplus["PricePaidVarioWithSolarOnly"] = (df_price_varioplus["Grid pos with solar only"] * df_price_varioplus["Varioplus"]/4.0)   #note, result is true/false, and .astype(int) convert to 1/0
cost_normal_profile_with_vario_with_solar_only = df_price_varioplus["PricePaidVarioWithSolarOnly"].sum()
print("Price paid with solar only:", cost_normal_profile_with_vario_with_solar_only)
df_price_varioplus["PricePaidDTSolarOnly"] = (df_price_varioplus["Grid pos with solar only"] * df_price_varioplus["Double Tarif"]/4.0)   #note, result is true/false, and .astype(int) convert to 1/0
cost_normal_profile_with_dt_with_solar_only = df_price_varioplus["PricePaidDTSolarOnly"].sum()
print("Price paid DT with solar only:", cost_normal_profile_with_dt_with_solar_only)


consumption_kWh_with_solar_only = df_price_varioplus["Grid pos with solar only"].sum()/4.0


# Energy Consumption Plot using Plotly
fig_simstorage_profile = px.line(df_price_varioplus, 
                        x=df_price_varioplus.index, 
                        y=[ "Consumption","Grid with solar only","Grid pos with solar only"], 
                        title="⚡ Consumption from the grid with solar", 
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


st.write(f""" Results with solar only:
    - The consumption of electricity  on the grid for this period is {consumption_kWh_with_solar_only:.2f} kWh with solar only
    - The cost of electricity bought is  {cost_normal_profile_with_vario_with_solar_only:.2f} CHF with Vario with solar only, mean price is {cost_normal_profile_with_vario_with_storage/consumption_kWh_with_storage:.3f} CHF/kWh
    - The cost of electricity bought is  {cost_normal_profile_with_dt_with_solar_only:.2f} CHF with Double Tariff with solar only""")


st.write(" \n ")

st.write("**Second example With 🌞 Solar Production and storage 🔋**")
st.write("First a standard control of storage (charge with solar excess) is done. There is no optimization done for the price.")



#and run the simulation of the system with the loaded datas:
solar_syst_Vex.run_storage_simulation()

#and retrieve the grid power and inject it in the vario dataframe:
grid_power_with_solar_and_storage_array = solar_syst_Vex.net_grid_balance_profile
df_price_varioplus["Grid with solar and storage"] = grid_power_with_storage_array 

grid_power_pos_with_solar_and_storage_array = grid_power_with_solar_and_storage_array.copy()
grid_power_pos_with_solar_and_storage_array[grid_power_pos_with_solar_and_storage_array < 0] = 0

df_price_varioplus["Grid with solar and storage"] = grid_power_with_solar_and_storage_array 
df_price_varioplus["Grid pos with solar and storage"] = grid_power_pos_with_solar_and_storage_array 

soc_array = solar_syst_Vex.soc_profile
df_price_varioplus["SOC solar"] = soc_array 

#and compute the price with that power profile
df_price_varioplus["PricePaidVarioWithSolarStorage"] = (df_price_varioplus["Grid pos with solar and storage"] * df_price_varioplus["Varioplus"]/4.0)   #note, result is true/false, and .astype(int) convert to 1/0
cost_normal_profile_with_vario_with_solar_and_storage = df_price_varioplus["PricePaidVarioWithSolarStorage"].sum()
print("Price paid with solar and storage:", cost_normal_profile_with_vario_with_solar_and_storage)
df_price_varioplus["PricePaidDTSolarStorage"] = (df_price_varioplus["Grid pos with solar and storage"] * df_price_varioplus["Double Tarif"]/4.0)   #note, result is true/false, and .astype(int) convert to 1/0
cost_normal_profile_with_dt_with_solar_and_storage = df_price_varioplus["PricePaidDTSolarStorage"].sum()
print("Price paid DT with solar only:", cost_normal_profile_with_dt_with_solar_only)


consumption_kWh_with_solar_and_storage = df_price_varioplus["Grid pos with solar and storage"].sum()/4.0



#st.write(" The cost of electricity for this period is " + str(cost_normal_profile_with_vario) + " CHF ")
st.write(f""" Results with solar and storage:
    - The consumption of electricity on the grid for this period is {consumption_kWh_with_solar_and_storage:.2f} kWh
    - The cost of electricity is  {cost_normal_profile_with_vario_with_solar_and_storage:.2f} CHF with Vario solar and storage, mean price is {cost_normal_profile_with_vario_with_solar_and_storage/consumption_kWh_with_solar_and_storage:.3f} CHF/kWh
    - The cost of electricity is  {cost_normal_profile_with_dt_with_solar_and_storage:.2f} CHF with Double tariff solar and storage""")



# Energy Consumption Plot using Plotly
fig_simstorage_profile = px.line(df_price_varioplus, 
                        x=df_price_varioplus.index, 
                        y=[ "Consumption","Grid with solar and storage", "Grid pos with solar and storage"], 
                        title="⚡ Consumption from the grid with solar 🌞 and storage 🔋", 
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
                        y=[ "SOC solar"], 
                        title=" 🔋 State of charge of the battery", 
                        labels={"value": "State of charge (%)", "variable": "Consumption"}
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








st.markdown("---")


st.title("Conclusion")
st.write(""" Make your own ideas by playing with this simulator...  here are mine:
         
    - If you have no solar, jump to the vario prices and start to act like if you had some: put your loads during the day. That was the case with the consumption profile used and we see that it's cheaper. Let's consume the cheap solar of your neighbors!
    - Addition of a storage without solar can save 200 to 300CHF per year with Vario 
    - The double tariff is the best for houses with solar installed, because the low price is mainly during the PV production and during that time you have your own energy to cover the loads
    - With houses with solar and storage, the difference between one and the other tariff is not big but an smart control has not been tested yet... that can make a difference during the winter when the battery is there but there is not much solar.
    - This is with Vario of Groupe-E that is based on the grid loading and that could be very different with an dynamic tarif based on market price, don't make a generalization.
         

    """)






st.markdown("---")

st.title("Next steps 👨‍💻")



st.write(""" Solar, storage and optimization: the smart control 🏆
         
         This simulation is to come yet...
         The best energy management requires an optimization to obtain good results . 
         This will be perfomed with day by day optimization.
         It's less obvious, but not rocket science ;-) 
         
         Then there will be real world control: to apply this strategy to the next3, 
         transmit the orders with the API or locally with Modbus... 
         - Without solar: give directly the power setpoint on the grid input (AC-Source) 
            to force charging and set discharge current to 0 when you want to avoid discharge 
         - With solar: choose the time when to charge, discharge and force charge from the grid
         - that was already tested here: https://github.com/moixpo/nxcontrol
         - a good control sould take the weather forcast into account, that was tested with Openmeteo
             but now all the pieces of the puzzle must be put together...  
         
         ...see you later """)






# st.markdown("---")
# st.markdown("---")

# # Show dataset preview
# st.title("📋 **Data Overview, for debug purpose**")
# st.dataframe(df_price_varioplus.head())

# st.dataframe(df_price_varioplus.tail())


# # Combined Solar Power and Energy Consumption Plot using Plotly
# if "15min mean System Pout Consumption power (ALL) [kW]" in df_pow_profile.columns:
#     fig_combined = px.line(df_pow_profile, x="Time", 
#                             y=["15min mean Solar power (ALL) [kW]", "15min mean System Pout Consumption power (ALL) [kW]"], 
#                             title="ORIGINAL DATA 🌞 Solar Production vs ⚡ Energy Consumption", 
#                             labels={"value": "Energy (kWh)", "variable": "Legend"},
#                             color_discrete_sequence=["lightcoral", "lightblue"] )
    
#     # Move legend below the graph
#     fig_combined.update_layout(
#         legend=dict(
#             orientation="h",
#             yanchor="top",
#             y=-0.2,  # Position below the graph
#             xanchor="center",
#             x=0.1
#         )
#     )
#     st.plotly_chart(fig_combined)


