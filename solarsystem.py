#solarsystem.py
#representation of a solar system with storage
#posibility to update the model and simulate it with methods
#Moix P-O
#Albedo Engineering 
#MIT license
#last modif 1 avril 2024
#last modif 6 august 2024
#last modif 7 april 2025


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt



class SolarSystem:
    """
    representation of a next3 solar system
    """
    
    comment = ""  # available for a note about the system

    ##properties (created at construction but not supplied in constructor)
    #roof
    gps_location = [0.0, 0.0]   #LATITUDE, LONGITURE
    pv_kW_installed = 0.0       #power installed on the roof
    roof_orientation = 0.0      # Orientation (azimuth) angle of the (fixed) PV system, 0=south, 90=west, -90=east.
    roof_slope = 0.0            # 0 to 90°, 20° is common

    #battery
    batt_capacity_kWh = 10.0        # in kWh, 10kWh default value, to be updated if available
    soc_init = 20.0                 # by default, used at begining of simulation, that should be updated with the real value
    soc_for_backup_user = 20.0      # minimal level in battery when grid connected
    current_adaptive_soc_for_backup = soc_for_backup_user #that is the level that increases if the battery was not full in the last days
    soc_for_gf_user = 100.0
    soc_for_end_of_charge = 100.0
    max_power_charge = batt_capacity_kWh/2      #here it is C/2 (for lithium) for rough estimation, that should be readed on the device
    max_power_discharge = -batt_capacity_kWh/2
    
    max_power_charge_over_95_percent_soc = batt_capacity_kWh/10 #C/10 end of charge close to 100% like every BMS do.
    

    #inverter
    inverter_model="next3"
    max_inverter_power = 15.0       #kW   15 by default for the nx3, to be updated if another model
    max_grid_injection_power = max_inverter_power
    
    #the battery and inverter system itself has a consumption of 50W / 0.05kW
    selfpowerconsumption = 0.055

    #properties in operation:
    state = ""
    on_state = False
    error_log = ""
    live_values = []
    #...an so on...




    #####################
    # Physical Simulation:
    # with timeseries, all variable with _profile at the end are arrays
    # the data for simulation (solar and consumption) will be provided
    # with historical data from a csv, or directly given with dedicated methods

    # very simple model of efficiency for the moment: an constant, only on battery charged-discharged TODO: better model
    EFFICIENCY_BATT_ONE_WAY = 0.95 # total for 2 ways: 0.95*0.95=0.9025

    #properties for simulation: use of numpy arrays
    #load_profile = [] # empty array for init
    #solar_production_profile = [] # empty array for init
    #grid_profile = []
    #net_power_balance_profile = []
    #battery_power_profile = []
    #battery_soc_profile = []

    sim_step = 1 # [h] in hours by default, that will be updated later
    time_steps  = np.array(range(0,24)) #by default the 24h hours of one day in steps of 1h, profiles filled with 0

    #used for simulation: initialized at 0, that will be updated when run_the_day is called.
    solar_power_profile = np.zeros(len(time_steps))  #solar production for each step of the period of simulation
    load_power_profile = np.zeros(len(time_steps))

    #battery simulation: profiles of the energy in the battery and limits for each hours     
    energy_in_batt_profile = np.ones(len(time_steps)) * soc_init/100.0 * batt_capacity_kWh  #initialised for the whole day at the initial SOC
    soc_profile = np.ones(len(time_steps)) * soc_init  #init by default with constant SOC over the whole day
    #control vectors:
    battery_max_charge_setpoint_profile = np.ones(len(time_steps)) * max_power_charge  #max charge and discharge power, that is/can be use to control the max charging power, initial values that should be readed on the device 
    battery_max_discharge_setpoint_profile = np.ones(len(time_steps)) * max_power_discharge 
    
    clamped_batt_pow_profile = np.zeros(len(time_steps)) #that is an internal array with the  charging power computed during the simulation
    
    delta_p_on_ac_source_profile = np.zeros(len(time_steps)) #for an direct control with power setpoint, per example to discharge the battery. 
    net_power_balance_profile_with_ac_setpoint = np.zeros(len(time_steps))
    max_injection_power_profile = np.ones(len(time_steps))*(-max_grid_injection_power) #for an direct control with power setpoint for the max injection power, warning, it is an negative number 
    grid_setpoint_profile = np.zeros(len(time_steps))

    lostproduction = np.zeros(len(time_steps))

    #result of simulation: kept in a property of the object for later display, initialized at 0
    net_power_balance_profile = np.zeros(len(time_steps))  # solar-load
    net_grid_balance_profile = np.zeros(len(time_steps))   # load-solar-battpow with max injection power
    net_grid_balance_unlimited_profile = np.zeros(len(time_steps))   # load-solar-battpow 




    def __init__(self, owner_name, adress):
        #give only minimal information of the system for creating it: owner and adress
        #else there are too many to enter and it's not convenient, there will be specific methods for updating the power profiles and the control.
        
        self.owner_name = owner_name
        self.adress = adress




    #*************************************************
    #simple basic methods to display info on the system
        
    def display(self):
        '''
        Simply plot a few indications about the system in the console
        
        Returns
        -------
        None.

        '''
        print("The system has " + str(self.pv_kW_installed) + " kW of solar installed with an " + str(self.max_inverter_power) + " kW inverter")
        print("The system belongs to  " + self.owner_name + " and is situated: " + self.adress)      
        print("Comment: " + self.comment)      
        print("-----------------------------")


    def compute_energy_potential(self):
        '''
        estimation of the yearly production

        Returns
        -------
        year_energy : float
            the number of kWh that this installation could produce.

        '''
        
        #TODO, here is a very basic model first with 1000kWh production by kWp installed
        #TODO that could be improved with API to PVGIS using the coordinate per example
        year_energy = self.pv_kW_installed*1000
        if self.pv_kW_installed == 0 :
            print("Warning the installed power is 0, probably it was never given")
        return year_energy
    



    #*************************************************
    #update data for simulation methods: from file or direct input
    
    def load_csv_data_for_simulation(self, filename, load_column_name, solar_column_name, timestep):
        '''
        it load an csv and take only the 2 columns with the given name

        Parameters
        ----------
        filename : string
            name of file.
        load_column_name : string
            column name in the header for the consumption
        solar_column_name : string
            column name in the header for the solar production
        timestep : float
            the timestep used for the sampling, given in hour  (15min = 0.25 hour)

        Returns
        -------
        None.  but it updates the internal variables of the object SolarSystem

        '''
        
        
        #note: prepare a csv file with colums containing powers in kW
        try:
            rawdata = pd.read_csv(filename)
            
            #print(rawdata)
            #print(rawdata.index)
            #print(rawdata.columns)
            self.load_power_profile = np.array(rawdata[load_column_name].values)
            self.solar_power_profile = np.array(rawdata[solar_column_name].values)
            self.sim_step = timestep
            self.time_steps  = np.array(range(0,len(self.load_power_profile)))*timestep  #in hours


            #battery simulation: profiles initialisation of all the profiles with the same length of array for simulation
            self.net_grid_balance_profile = self.load_power_profile-self.solar_power_profile
            self.net_power_balance_profile = self.load_power_profile - self.solar_power_profile
            self.energy_in_batt_profile = np.ones(len(self.load_power_profile))*self.soc_init/100.0*self.batt_capacity_kWh  #initialised for the whole day at the initial SOC
            self.soc_profile = np.ones(len(self.load_power_profile))*self.soc_init  #init by default with constant SOC over the whole day
            self.battery_max_charge_setpoint_profile = np.ones(len(self.load_power_profile))*self.max_power_charge  #max charge and discharge power, here it is C/3 (for lithium) for rough estimation, that should be readed on the device 
            self.battery_max_discharge_setpoint_profile = np.ones(len(self.load_power_profile))*self.max_power_discharge
            self.clamped_batt_pow_profile = np.zeros(len(self.load_power_profile)) #that is an internal array with the  charging power computed during the simulation
            self.delta_p_on_ac_source_profile = np.zeros(len(self.load_power_profile)) #for an direct control with power setpoint, per example to discharge the battery.
            self.max_injection_power_profile = np.ones(len(self.load_power_profile))*(-self.max_grid_injection_power) #for an direct control of max injected power
            self.lostproduction = np.zeros(len(self.load_power_profile)) 

            #print(self.load_power_profile)
            print("\n Data are loaded from csv\n")

        except:
            print("\n ! No file with this filename or not correct format\n")



    def load_data_for_simulation(self, load_power_profile, solar_power_profile, timestep):
         '''
         it load an profile given in an array  and take only the 2 columns with the given name
        
         Parameters
         ----------
         explicit in names, the size of the profiles must match and timestep is in h
        
         Returns
         -------
         None.  but it updates the internal variables of the object SolarSystem
        
         '''
         #this method is to give data that don't come from a csv file like the method load_csv_data_for_simulation
         #prepare data with powers in kW and the time step in h
         self.load_power_profile = np.array(load_power_profile)
         self.solar_power_profile = np.array(solar_power_profile)
         self.sim_step = timestep
         self.time_steps  = np.array(range(0,len(self.load_power_profile)))*timestep  #in hours

         #battery simulation: profiles initialisation with the same lenght of array 
         self.net_grid_balance_profile = self.load_power_profile-self.solar_power_profile
         self.net_power_balance_profile = self.load_power_profile - self.solar_power_profile
         self.energy_in_batt_profile = np.ones(len(self.load_power_profile))*self.soc_init/100.0*self.batt_capacity_kWh  #initialised for the whole day at the initial SOC
         self.soc_profile = np.ones(len(self.load_power_profile))*self.soc_init  #init by default with constant SOC over the whole day
         self.battery_max_charge_setpoint_profile = np.ones(len(self.load_power_profile))*self.max_power_charge  #max charge and discharge current 
         self.battery_max_discharge_setpoint_profile = np.ones(len(self.load_power_profile))*self.max_power_discharge
         self.clamped_batt_pow_profile = np.zeros(len(self.load_power_profile)) #that is an internal array with the  charging power computed during the simulation
         self.delta_p_on_ac_source_profile = np.zeros(len(self.load_power_profile)) #for an direct control with power setpoint, per example to discharge the battery.
         self.max_injection_power_profile = np.ones(len(self.load_power_profile))*(-self.max_grid_injection_power) #for an direct control of max injected power
         self.lostproduction = np.zeros(len(self.load_power_profile)) 

         #print(self.load_power_profile)
         print("\n Data are updated \n")



    #*************************************************
    #simulation methods: without (simple) or with storage 
         
    def run_simple_simulation(self, print_res=True):
         #let's consider just the power balance, everything in AC, without storage, that will be for later...
         self.net_grid_balance_profile = self.load_power_profile-self.solar_power_profile
         self.net_grid_balance_unlimited_profile = self.net_grid_balance_profile.copy() #copy values (not ref!)
         
         net_power_balance_neg = np.zeros(len(self.net_grid_balance_profile))
         net_power_balance_pos = np.zeros(len(self.net_grid_balance_profile))

         #check the maximal grid injection:
         k = 0
         for pow in self.net_grid_balance_profile:
             if pow < self.max_injection_power_profile[k]:
                 self.lostproduction[k] = self.max_injection_power_profile[k]-pow
                 self.net_grid_balance_profile[k] = self.max_injection_power_profile[k]
                 
             if pow < 0:
                net_power_balance_neg[k] = self.net_grid_balance_profile[k]
             else :
                net_power_balance_pos[k] = self.net_grid_balance_profile[k]

             k = k+1
                 


         if print_res:  #used to avoid plenty of terminal print
            print("\n*************\nSimulation without storage: ")
            print("The solar energy produced is " + str(sum(self.solar_power_profile) * self.sim_step) + " kWh")
            print("The energy consumed is " + str(sum(self.load_power_profile) * self.sim_step) + " kWh")
            print("The energy taken from the grid is " + str(sum(net_power_balance_pos) * self.sim_step) + " kWh")
            print("The energy sold to the grid is " + str(sum(net_power_balance_neg) * self.sim_step) + " kWh")
            print("The energy lost due to production limitation is " + str(sum(self.lostproduction) * self.sim_step) + " kWh")

            print("The peak power taken on the grid is " + str(max(self.net_grid_balance_profile) ) + " kW")


    def display_simple_simulation(self):
         '''       
         Returns
         -------
         a matplotlib fig of the simulation result
         '''
         
         #display that in a figure:
         fig_pow, axes_pow = plt.subplots(nrows=1, ncols=1, figsize=(10, 5))
         axes_pow.fill_between(self.time_steps  , self.solar_power_profile, color='y')
         axes_pow.plot(self.time_steps  , self.load_power_profile, 'r-')
         axes_pow.plot(self.time_steps  , self.net_grid_balance_profile, 'b-')
         axes_pow.plot(self.time_steps  , self.max_injection_power_profile, 'm:')
         axes_pow.plot(self.time_steps  , self.net_grid_balance_unlimited_profile, 'b:')
         #axes_pow.plot(self.time_steps  , self.lostproduction, 'c')



         axes_pow.set_ylabel('Power activ [kW]', fontsize=12)
         axes_pow.set_title('System Powers, simple simulation without storage', fontsize=12, weight="bold")
         axes_pow.legend(["Solar","Loads","Grid", "Max inject"])
         axes_pow.grid(True)

         return fig_pow




    def run_storage_simulation(self, print_res=True):
         #method to simulate the day with storage with the previously loaded data for solar and consumption 
         
         # #The control arrays for each timesteps must be passed to 
         #     self.battery_max_discharge_setpoint_profile  must be <0
         #     self.battery_max_charge_setpoint_profile     must be >0
         #     self.delta_p_on_ac_source_profile            can be positive or negative
         #     self.max_injection_power_profile             must be <0
                 

         #compute/update the balance, including the consumption and selfdischarge of the system: everything is counted on AC-side, including solar (like AC-coupling)
         #the balance is what's left for charging/discharging the battery
         self.net_power_balance_profile = self.load_power_profile - self.solar_power_profile + np.ones(len(self.solar_power_profile)) * self.selfpowerconsumption
         self.net_power_balance_profile_unlimited_profile = self.net_power_balance_profile.copy() #copy values (not ref!)

         #The grid setpoint is limited by the max_injection_power_profile power toward negative power 
         self.grid_setpoint_profile = np.maximum(self.delta_p_on_ac_source_profile, self.max_injection_power_profile)
         
         #self.net_power_balance_profile_with_ac_setpoint = self.load_power_profile - self.solar_power_profile + np.ones(len(self.solar_power_profile)) * self.selfpowerconsumption - self.delta_p_on_ac_source_profile    
         self.net_power_balance_profile_with_ac_setpoint = self.net_power_balance_profile - self.grid_setpoint_profile    

         #reset some variable to be sure it is not affected by a previous simulation:
         self.lostproduction = np.zeros(len(self.load_power_profile)) 
         grid_pos_profile = np.zeros(len(self.load_power_profile))
         grid_neg_profile = np.zeros(len(self.load_power_profile))
        

         #what's negative is to charge the battery, or goes to the grid when battery is limited (full or max charging current)
         #what's positive must be discharged or taken from the grid when the battery is empty
         
         #let's separate the positive and negative power that will be handled differently (charge or discharge the battery)
         net_power_balance_pos = np.zeros(len(self.net_power_balance_profile))
         net_power_balance_neg = np.zeros(len(self.net_power_balance_profile))
     
         k = 0
         for value in self.net_power_balance_profile:   
             if value > 0:   
                 net_power_balance_pos[k] = value
             else:       
                 net_power_balance_neg[k] = value
             k = k + 1
     
         
         #in some cases the external control wants to add/inject some power from the battery and not have a zero balaance: 
         net_power_balance_with_ac_setpoint_pos = np.zeros(len(self.net_power_balance_profile))
         net_power_balance_with_ac_setpoint_neg = np.zeros(len(self.net_power_balance_profile))

         k = 0
         for value in self.net_power_balance_profile_with_ac_setpoint:   
             if value > 0:   
                 net_power_balance_with_ac_setpoint_pos[k] = value
             else:       
                 net_power_balance_with_ac_setpoint_neg[k] = value
             k = k + 1
            
        
        
         #HERE ADD THE SIMULATION OF THE NEXT3 its default behaviour/energy management     
         #conditions:
         #   -is there enough space for energy in the battery to charge (without considering limited end of charge current given by the bms)
         #   -is there enough space for energy in the battery to discharge 
         #   -charge only with excess solar if the AC-source setpoint is zero, else try to add the AC-source setpoint to the grid input
         #   -discharge only for consumption, not grid injection with battery power (if the AC-source setpoint is zero, else try to add the AC-source setpoint to the grid input)
         #   -respect the soc for backup and soc for gridfeeding.
         #   -respect the max charge/discharge power of the battery (that can be used for control variable)
         #   -respect the max injection power to the grid  (that can be used for control variable)
         #
         #the efficiency model is not absolutely exact compared to the physics of the nx3 inverter, it is like an AC-coupling of a pure battery inverter

         #Power is in kW and energy stored in batt in kWh, the time_step in hour is the conversion ratio, 15 min = 0.25h at 1kW is 0.25 kWh
         #kW on battery side


         #above a given level, the batt is stopped to charge:
         max_energy_in_batt = self.batt_capacity_kWh*min(self.soc_for_gf_user,self.soc_for_end_of_charge )/100.0
         #under a given level, the batt is forced to stop to discharge:
         min_energy_in_batt = self.batt_capacity_kWh*self.current_adaptive_soc_for_backup/100.0
        

         #do the battery simulation for each step of the profiles given, reinitialize the energy with the initial value of SOC, if if was changed inbetween
         #self.soc_profile = np.ones(len(self.load_power_profile))*self.soc_init  #init by default with constant SOC over the whole day
         self.energy_in_batt_profile = np.ones(len(self.load_power_profile)) * self.soc_init / 100.0 * self.batt_capacity_kWh  #initialised for the whole day at the initial SOC

         
        #Lets do the step by step simulation with the integration of the battery: 
         k = 0
         for time in self.time_steps:

             #convention for charging  is positive power, the smallest positive is the limitation:          
             possible_p_charge = min((max_energy_in_batt-self.energy_in_batt_profile[k])/self.EFFICIENCY_BATT_ONE_WAY/self.sim_step,
                                       -net_power_balance_with_ac_setpoint_neg[k],
                                       self.battery_max_charge_setpoint_profile[k])
                 
           
             #convention for discharge power is negative power, max is the minimal discharge:
             # when discharging and injecting back to the grid, this must take into account the max injection current: self.max_injection_power_profile[k]                 
             possible_p_discharge = max((min_energy_in_batt-self.energy_in_batt_profile[k])*self.EFFICIENCY_BATT_ONE_WAY/self.sim_step,
                                     -net_power_balance_with_ac_setpoint_pos[k],
                                     self.battery_max_discharge_setpoint_profile[k],
                                     self.max_injection_power_profile[k]-net_power_balance_neg[k])
                 
                      
             #mix with the  default behaviour of the next3 which is to compensate grid power 
             batt_pow=-self.net_power_balance_profile_with_ac_setpoint[k] 
            
            
             #print(np.clip( batt_pow, possible_p_discharge, possible_p_charge) ) # test

             self.clamped_batt_pow_profile[k] = np.clip( batt_pow, possible_p_discharge, possible_p_charge) 
            
            
            
             #now integrate the storage for each time step:
             if k+1 < len(self.energy_in_batt_profile):
                 # now compute the power balance:
                 if self.clamped_batt_pow_profile[k] > 0.0:
                     #here battery charge efficiency
                     self.energy_in_batt_profile[k+1] = self.energy_in_batt_profile[k] + self.clamped_batt_pow_profile[k] * self.sim_step * self.EFFICIENCY_BATT_ONE_WAY
                 else:
                     #here battery discharge efficiency
                     self.energy_in_batt_profile[k+1] = self.energy_in_batt_profile[k] + self.clamped_batt_pow_profile[k] * self.sim_step / self.EFFICIENCY_BATT_ONE_WAY
                
             
                
             #the grid power is the netpower plus what's going to the battery:
             self.net_grid_balance_profile[k] = self.net_power_balance_profile[k] + self.clamped_batt_pow_profile[k] #* self.EFFICIENCY_BATT_ONE_WAY
             
             #but this is limited by the max injection current:
             if self.net_grid_balance_profile[k] < self.max_injection_power_profile[k]:
                 #production limitation:
                 self.lostproduction[k] = self.max_injection_power_profile[k]-self.net_grid_balance_profile[k]
                 self.net_grid_balance_profile[k] = self.max_injection_power_profile[k]
                     
             #separate the positive power on the grid (buy energy) and the negative power (solar excess injection to the grid)
             if self.net_grid_balance_profile[k] > 0:
                 grid_pos_profile[k] = self.net_grid_balance_profile[k]
             else:
                 grid_neg_profile[k] = self.net_grid_balance_profile[k]
                        
                   
                    
             k = k + 1
        
            
        
         #compute the SOC from the energy in the battery:
         self.soc_profile = self.energy_in_batt_profile/self.batt_capacity_kWh*100
        

         #compute the sums over the day:
             
         e_solar = sum(self.solar_power_profile) * self.sim_step
         e_load = sum(self.load_power_profile) * self.sim_step
         e_grid_consumption = sum(grid_pos_profile) * self.sim_step
         e_grid_injection = sum(grid_neg_profile) * self.sim_step

         if e_load > 0:
             autarky_rate = (e_load-e_grid_consumption) / e_load * 100
         else:
             autarky_rate = 0
             

         if print_res:  #used to avoid plenty of terminal print
            print("\n*************\nSimulation with storage: ")
            print("The solar energy produced is " + str(e_solar) + " kWh")
            print("The energy consumed is " + str(e_load) + " kWh")
            print("The energy taken from the grid is " + str(e_grid_consumption) + " kWh")
            print("The energy injected back to the grid is " + str(e_grid_injection) + " kWh")
            print("The peak power taken on the grid is " + str(max(self.net_grid_balance_profile) ) + " kW")
            print("The energy lost due to production limitation is " + str(sum(self.lostproduction) * self.sim_step) + " kWh")

            print("The AUTARKY rate is " + str(autarky_rate) + "%")



    def display_storage_simulation(self):
         '''       
         Returns
         -------
         a matplotlib fig of the simulation result
         '''
         
         #And display that in a figure:
         

         
         fig_pow, (axes_sys_pow, axes_batt_SOC) = plt.subplots(nrows=2, ncols=1, figsize=(10, 7))
         axes_batt_pow=axes_batt_SOC.twinx() #second axe for the state of charge scale

         axes_sys_pow.fill_between(self.time_steps  , self.solar_power_profile, color='y')
         axes_sys_pow.plot(self.time_steps  , self.load_power_profile, 'r-')
         axes_sys_pow.plot(self.time_steps  , self.net_grid_balance_profile, 'b-')
         axes_sys_pow.plot(self.time_steps  , self.delta_p_on_ac_source_profile, 'k:')
         axes_sys_pow.plot(self.time_steps  , self.max_injection_power_profile, 'm:')
         
         #axes_sys_pow.plot(self.time_steps  , self.net_power_balance_profile_with_ac_setpoint, 'c:')
         axes_sys_pow.plot(self.time_steps  , self.net_power_balance_profile_unlimited_profile, 'b:')
         axes_sys_pow.plot(self.time_steps  , self.lostproduction, 'c')

         
         axes_sys_pow.set_ylabel('Power activ [kW]', fontsize=12)
         axes_sys_pow.set_title('System Powers with storage', fontsize=12, weight="bold")
         axes_sys_pow.legend(["Solar","Loads","Grid", "$\\Delta$ P", "Max inject", "unlim bal","lost sol"])
         axes_sys_pow.grid(True)

         #put the fill_between first so that it is at the back
         axes_batt_SOC.fill_between(self.time_steps  , self.soc_profile, color='c')
         axes_batt_SOC.set_ylabel('SOC [%]', fontsize=12)
         axes_batt_SOC.legend(["SOC"], loc='upper left')

         #Then the battery power:
         axes_batt_pow.plot(self.time_steps  , self.net_power_balance_profile, 'm-')
         axes_batt_pow.plot(self.time_steps  , self.clamped_batt_pow_profile, 'k-')
         #axes_batt_pow.plot(xtime, self.solar_power_profile, 'k-')
         axes_batt_pow.set_ylabel('Power activ [kW]', fontsize=12)

         axes_batt_pow.plot(self.time_steps  , self.battery_max_charge_setpoint_profile,
                              color='g',
                              linestyle=':')
        
         axes_batt_pow.plot(self.time_steps  , self.battery_max_discharge_setpoint_profile ,
                              color='b',
                              linestyle=':')
        

         #axes_batt_pow.set_title('System Powers', fontsize=12, weight="bold")
         axes_batt_pow.legend(["Balance","Battery", "max ch", "min dis"], loc='upper right')
         axes_batt_pow.grid(True)

         return fig_pow




    def display_storage_energy(self):
         '''       
         Returns
         -------
         a matplotlib fig of the energy of the battery during simulation
         '''
         
         #And display that in a figure:
         
         #define the x axis with time in hours:
         #xtime=np.array(range(1,len(self.load_power_profile)+1))*self.sim_step #TODO: better than this, the first column of csv has a the time and date to build a timeserie
         #print(xtime) #test
         
         fig_e, axes_e = plt.subplots(nrows=1, ncols=1, figsize=(10, 7))

         axes_e.plot(self.time_steps  , self.energy_in_batt_profile , 'r-o')


         
         axes_e.set_ylabel('Energy in batt [kWh]', fontsize=12)
         axes_e.set_title('storage', fontsize=12, weight="bold")
        # axes_e.legend(["Solar","Loads","Grid", "\DeltaP", "Max inject"])
         axes_e.grid(True)

        

         return fig_e




    def display_storage_debug(self):
         '''       
         Returns
         -------
         a matplotlib fig of the simulation result
         '''
         #for tests...
         
         fig_debug, axes_d = plt.subplots(nrows=1, ncols=1, figsize=(10, 7))

         axes_d.fill_between(self.time_steps  , self.solar_power_profile, color='y')
         #axes_d.plot(self.time_steps  , self.load_power_profile, 'r-')
         #axes_d.plot(self.time_steps  , self.net_grid_balance_profile, 'b-')
         axes_d.plot(self.time_steps  , self.delta_p_on_ac_source_profile, 'k:')
         axes_d.plot(self.time_steps  , self.max_injection_power_profile, 'm:')
         
         axes_d.plot(self.time_steps  , self.net_power_balance_profile, 'm-')

         axes_d.plot(self.time_steps  , self.net_power_balance_profile_with_ac_setpoint, 'c')
         #axes_d.plot(self.time_steps  , self.net_power_balance_profile_unlimited_profile, 'm:')
         axes_d.plot(self.time_steps  , self.grid_setpoint_profile, 'g:')

         

         axes_d.plot(self.time_steps  , self.clamped_batt_pow_profile, 'k-')

  
         axes_d.set_ylabel('Power activ [kW]', fontsize=12)
         axes_d.set_title('DEBUG with storage', fontsize=12, weight="bold")
         #axes_d.legend()
         axes_d.grid(True)

        
            

         return fig_debug



###########################
# OTHER FUNCTIONS 
############## 
#not in the solarsystem object for an more general use:

 
def cost_function_economic(net_grid_simulation, delta_e_batt, prices_consumption, prices_injection, timestep ):
    '''
    give grid power in kW, and prices in €/kWh with the same sampling, as arrays of the same length.
    timestep in hour
    delta_e_batt is the difference of energy in the battery in kWh at begining and end of the simulation that must be values
    
    it returns:[result_sim, balance_cost, cost_consumption, payback_injection ]
        result_sim: the final cost, including the value given to the energy left/missing in the storage
                balance_cost: what would be paid to the DSO
                cost_consumption: price of the energy bought to the DSO
                payback_injection: price for the solar sold to the DSO        
        
    '''
    
    #let's separate the positive and negative 
    net_grid_simulation_pos = np.zeros(len(net_grid_simulation))
    net_grid_simulation_neg = np.zeros(len(net_grid_simulation))
    k = 0
    for value in net_grid_simulation:
        if value > 0:   
            net_grid_simulation_pos[k] = value
            #print('pos')          
        else:       
            net_grid_simulation_neg[k] = value     
            #print(value)
        k = k+1
    
    
    cost_consumption = (net_grid_simulation_pos*prices_consumption).sum() * timestep
    payback_injection = -(net_grid_simulation_neg*prices_injection).sum() * timestep
    balance_cost = cost_consumption-payback_injection

    #bilan batterie   
    #valorisé au prix moyen de la journée:
    storage_value = -delta_e_batt*np.mean(prices_consumption)
    
    result_sim = balance_cost+storage_value
    
    
    return [result_sim, balance_cost, cost_consumption, payback_injection ]
    
