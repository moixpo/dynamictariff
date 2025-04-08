#test_of_solarsystems.py
#Test of class SolarSystem: classes and constructor, methods for simulations,...
#examples with some csv files  
#Moix P-O
#update: 1 april 2024
#update: 6 august 2024


#separation of the class definition in file solarsystem.py and its example of use here: 
# a few different simulations using real datas with different sampling is done here

    
    

from solarsystem import*  #let's use it directly 

#for displaying figures:
import matplotlib.pyplot as plt

plt.close("all")



print("\nTest of the class: 1st instance \n")
solar_syst_Vex = SolarSystem("M-P-O","Impasse du Solaire 6, 2050 Transition" )

#and properties initialisation  
solar_syst_Vex.gps_location = [46.208, 7.394] 
solar_syst_Vex.pv_kW_installed = 9.24 #power installed on the roof
solar_syst_Vex.roof_orientation = -10 # 0=S, 90°=W, -90°=E, -180°=N (or -180)
solar_syst_Vex.roof_slope = 20.0
solar_syst_Vex.batt_capacity_kWh = 10*1 # in kWh
solar_syst_Vex.max_inverter_power = 15 #kW
solar_syst_Vex.comment = "installed in June 2022"

solar_syst_Vex.display()
print("Production expected is " + str(solar_syst_Vex.compute_energy_potential()) + " kWh per year")
print(" - - - - - - - - - ")





###################################
# Examples of data loaded from various CSV

#load data stored in a csv file for simulation
filename = "nxt-sys-export.csv"
load_column_name = "Consommation [kW]"
solar_column_name = "Solaire [kW]"
time_step = 0.25 #every 15 minutes in that file

# #another file with 4 days:
# filename = "nxt-sys-export_17_20janv.csv"
# load_column_name = "Consumption [kW]"
# solar_column_name = "Solar [kW]"
# time_step = 0.25 #every 15 minutes in that file

# #another file 1 day with 1 min steps:
# filename = "nxt-sys-export_1min_23janvier.csv"
# load_column_name = "Consommation [kW]"
# solar_column_name = "Solaire [kW]"
# time_step = 1.0 / 60 #every 1 minute in that file


# #another file 1 day with 1 min steps: in that file there is a charge constraint in morning: 50A from 6 to 7h, 4A until 11h, 50A 11h to 12h, 100A then. That should be added to simulation
# filename = "nxt-sys-export_29_mars_1min.csv"
# load_column_name = "Consommation [kW]"
# solar_column_name = "Solaire [kW]"
# time_step = 1.0 / 60 #every 1 minute in that file


#another file with 4 days:
filename = "15min_pow.csv"
load_column_name = "15min mean System Pout Consumption power (ALL) [kW]"
solar_column_name = "15min mean Solar power (ALL) [kW]"
time_step = 0.25 #every 15 minutes in that file


# #another file 1 day with 1 min steps: in that file there is a charge constraint in morning: 50A from 6 to 7h, 4A until 11h, 50A 11h to 12h, 100A then. That should be added to simulation
# filename = "nxt-sys-export_4_5aout2024.csv"
# load_column_name = "Consommation [kW]"
# solar_column_name = "Solaire [kW]"
# time_step = 1.0 / 60 #every 1 minute in that file



#load data and simulate the system with one of the three above:
solar_syst_Vex.load_csv_data_for_simulation(filename, load_column_name, solar_column_name, time_step)
#and the initial state of charge at the beggining of the simulation
solar_syst_Vex.soc_init = 65


# #manual update of the limits with the values tested (note: that could come from the csv export of the battery... TODO)
# # 50A from 6 to 7h, 4A until 11h, 50A 11h to 12h, 100A then.
# solar_syst_Vex.battery_max_charge_setpoint_profile[:] = 100*50/1000
# solar_syst_Vex.battery_max_charge_setpoint_profile[6*60:7*60] = 50*50/1000
# solar_syst_Vex.battery_max_charge_setpoint_profile[6*60:10*60] = 4*50/1000
# solar_syst_Vex.battery_max_charge_setpoint_profile[11*60:12*60] = 50*50/1000

# solar_syst_Vex.battery_max_discharge_setpoint_profile[17*60:22*60] = -10*50/1000


# # #################################################################
# # # #For test on the forced charging and discharging effect on the battery without the load profile 
# # solar_syst_Vex.load_power_profile[:] = 0.50
# # solar_syst_Vex.solar_power_profile[:] = 0.0
# # solar_syst_Vex.selfpowerconsumption = 0.0  #for test on the battery without self discharge
# # # #############################################################    
    
# #solar_syst_Vex.delta_p_on_ac_source_profile[2*60:4*60] = 1.0
# #solar_syst_Vex.delta_p_on_ac_source_profile[10*60+30:12*60] = 5.0
# solar_syst_Vex.delta_p_on_ac_source_profile[13*60:18*60] = -4.0

# solar_syst_Vex.max_injection_power_profile[:] = -solar_syst_Vex.max_inverter_power/2
# solar_syst_Vex.max_injection_power_profile[5*60:16*60] = -3

# #solar_syst_Vex.soc_for_gf_user=85  #limit charging to 85%, inject in the grid excess at that point
# #solar_syst_Vex.current_adaptive_soc_for_backup=45  #limit discharging to 45%


solar_syst_Vex.run_simple_simulation()
figure_vex=solar_syst_Vex.display_simple_simulation()


plt.show()
print("\n")



solar_syst_Vex.run_storage_simulation()
figure_vex2 = solar_syst_Vex.display_storage_simulation()   #and we can compare to what's happening on the real system that day for validation of the storage model
#figure_e=solar_syst_Vex.display_storage_energy()
#figure_d=solar_syst_Vex.display_storage_debug()

plt.show()
print("\n")








# print("\n#######################*\n 24 STEPS SIMULATION  \n")

# ###############################
# #Let's try to run the simulation with manual inputs rather than an csv file obtained from datalog
# #that is how it can be used in an optimization: it will come from forecast and predictions, one every day in 1 hour step
# #that will be used for optimal control of the solar system in function of the prices of energy

# load_prediction = [0.93133333, 0.88738889, 0.97338889, 0.989     , 0.91516667,
#         1.07666667, 1.0025    , 0.94477778, 2.089     , 2.40116667,
#         1.81966667, 1.55544444, 1.337     , 1.06811111, 1.55277778,
#         1.07605556, 1.38377778, 1.26811111, 1.733     , 1.591     ,
#         1.21038889, 1.03955556, 0.95622222, 1.00361111]


# solar_prediction = [0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00,
#         0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 3.77777778e-03,
#         1.63055556e-01, 1.82855556e+00, 3.17444444e+00, 3.90694444e+00,
#         4.10261111e+00, 4.17488889e+00, 1.73188889e+00, 2.70944444e-01,
#         1.64444444e-01, 1.90555556e-02, 0.00000000e+00, 0.00000000e+00,
#         0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00]


# # #For test on the forced chargin and discharging: set the 
# # for n in range(len(load_prediction)):
# #     load_prediction [n] = 0.0
# #     solar_prediction [n] = 0.0


# solar_syst_Vex.load_data_for_simulation(load_prediction, solar_prediction, timestep=1)




# #####
# #Test of some control variable:
# #forbidden to charge between 9 o'clock and 12 o'clock:
# solar_syst_Vex.battery_max_charge_setpoint_profile[9:12] = 0
# solar_syst_Vex.battery_max_discharge_setpoint_profile[8:10] = 0

# #force charging on the grid from 2 o'clock to 5 o'clock:
# solar_syst_Vex.delta_p_on_ac_source_profile[2:5] = 5.0
# solar_syst_Vex.delta_p_on_ac_source_profile[10:15] = -5.0


# #solar_syst_Vex.delta_p_on_ac_source_profile[:] = 5.5
# solar_syst_Vex.max_injection_power_profile[7:23] = -2.0


# #and run the simulation of the system with the loaded datas:
# solar_syst_Vex.run_storage_simulation()

# #The results are embedded in the object and we can display the simulation result with a method:
# figure_vex3 = solar_syst_Vex.display_storage_simulation()



# plt.show()
# #print("\n")





# #####################################################
# #computation of the costs with that simulation:

    
# net_grid_simulation = solar_syst_Vex.net_grid_balance_profile
# delta_e_batt = solar_syst_Vex.energy_in_batt_profile[-1] - solar_syst_Vex.energy_in_batt_profile[0]
# prices_consumption = [0.10096, 0.10065, 0.10128, 0.10178, 0.10022, 0.10402, 0.10951,
#         0.13085, 0.1632 , 0.15569, 0.19162, 0.17644, 0.17061, 0.16954,
#         0.12013, 0.12468, 0.12815, 0.146  , 0.21258, 0.23482, 0.25207,
#         0.22469, 0.15797, 0.14854]
# prices_injection = [0.04514, 0.03993, 0.03326, 0.02303, 0.02613, 0.03809, 0.04717,
#         0.0732 , 0.09111, 0.08506, 0.06949, 0.06039, 0.05609, 0.0569 ,
#         0.05829, 0.05841, 0.06448, 0.07738, 0.09654, 0.10304, 0.11731,
#         0.10146, 0.09256, 0.07422]
# timestep = 1

# [result_sim, balance_cost, cost_consumption, payback_injection ] = cost_function_economic(net_grid_simulation, delta_e_batt, prices_consumption, prices_injection, timestep )


# print("\n*************\nResult of the simulation with storage:  \n")
# print("The energy produced is paid " + str(payback_injection) + " €")
# print("The energy consumed is paid " + str(cost_consumption) + "  €")
# print("The energy bill is " + str(balance_cost) + "  €")
# print("The global result of the day is " + str(result_sim) + "  €")



# #second sim example without storage
# solar_syst_Vex.run_simple_simulation()
# figure_vex=solar_syst_Vex.display_simple_simulation()


# net_grid_simulation = solar_syst_Vex.net_grid_balance_profile
# delta_e_batt = solar_syst_Vex.energy_in_batt_profile[-1] - solar_syst_Vex.energy_in_batt_profile[0]
# [result_sim, balance_cost, cost_consumption, payback_injection ] = cost_function_economic(net_grid_simulation, delta_e_batt, prices_consumption, prices_injection, timestep )
# print("\n*************\nResult of the simulation without storage:  \n")
# print("The energy produced is paid " + str(payback_injection) + " €")
# print("The energy consumed is paid " + str(cost_consumption) + "  €")
# print("The energy bill is " + str(balance_cost) + "  €")
# print("The global result of the day is " + str(result_sim) + "  €")









''' NOTES from the tests

The automatic resizing of the prices arrays to match the power profiles arrays is not done. 
That would be good to make the system more flexible (simulation in minutes, prices for quarters).


(That could also go the other way: resize the sim step and profiles to match the prices resolution.)

The simulation take the timesteps as fixed, that could evolve to take the real timestamps and pass timeseries (but at the cost of performance? numpy is performant).

The end of charge power should be reduced down to C/10 when approaching 100%, like what almost all BMS do, TODO



in practice: the SOC for backup for the simulation should take into account the adaptive SOC



docstrings to document to fisnish

'''