# -*- coding: utf-8 -*-
"""
Created on Thu Feb  6 14:04:17 2020

@author: zzrfl
"""

import numpy as np

class Generic_cost(object):
    def __init__(self,
                 Capacity = 1000, # Desalination plant capacity (m3/day)
                 Prod = 328500, # Annual permeate production (m3)
                 downtime = 10,
                 fuel_usage = 0, # %
                 unit_cost = 1000, # $/m3/day
                 STEC = 60 , # Thermal energy consumption (kW)
                 SEEC = 1.5, # Specifc Electricity energy consumption (kWh/m3)
                 
                 # OPEX parameters
                 Chemicals = 0.04, # Chemical unit cost ($/m3)
                 Labor = 0.033, # Labor unit cost ($/m3)
                 Miscellaneous = 0.1, # Other direct/indirect cost ($/m3)
                 Discharge = 0.02, # Water discharge/disposal cost ($/m3)
                 Maintenance = 2, # Percentage to the capital cost (%)
                 Insurance = 0.5, # Percentage to the capital cost (%)
#                 GOR = 10.475,  # Gained output ratio
                # downtime = 0.1, # Yearly downtime of the plant (ratio)
                 yrs = 20, # Expected plant lifetime
                 int_rate = 0.04 , # Average interest rate
                 coe = 0.04 , # Unit cost of electricity ($/kWh)
                 coh = 0.01 , # Unit cost of heat ($/kWh)
                 solar_coh = '',
                 sam_coh = 0.02, # Unit cost of heat from SAM ($/kWh)
                 cost_storage = 26 , # Cost of thermal storage ($/kWh)
                 storage_cap = 0 # Capacity of thermal storage (kWh)

                 ):
        
        self.operation_hour = 24 #* (1-downtime) # Average daily operation hour (h/day)
        self.unit_cost = unit_cost
        self.Capacity = Capacity
        self.STEC = STEC
        self.coe = coe
        self.fuel_usage = fuel_usage/100
        self.coh = coh
        if solar_coh != '':
            self.sam_coh = float(solar_coh)
        else:
            self.sam_coh = sam_coh
        self.Prod = Prod * (1 - downtime /100 )
        self.SEEC = SEEC
        self.Chemicals = Chemicals
        self.Labor = Labor
        self.Maintenance = Maintenance
        self.Insurance = Insurance
        self.Miscellaneous = Miscellaneous
        self.Discharge = Discharge
        self.yrs = yrs
        self.int_rate = int_rate
        self.cost_storage = cost_storage
        self.storage_cap = storage_cap
        
    def lcow(self):
        
        self.CAPEX = ((self.unit_cost*self.Capacity+ self.cost_storage * self.storage_cap)*self.int_rate*(1+self.int_rate)**self.yrs) / ((1+self.int_rate)**self.yrs-1) / self.Prod 
        
        

        self.OPEX = self.STEC * (self.fuel_usage * self.coh + (1-self.fuel_usage) * self.sam_coh) \
            + self.coe * self.SEEC + self.Chemicals + self.Labor + self.Maintenance/100*self.CAPEX \
            + self.Miscellaneous + self.Discharge + self.Insurance/100*self.CAPEX 
        
        self.LCOW = self.CAPEX + self.OPEX
        
        cost_output = []
        cost_output.append({'Name':'Desal CAPEX','Value':self.CAPEX,'Unit':'$/m3'})
        cost_output.append({'Name':'Desal OPEX','Value':self.OPEX,'Unit':'$/m3'})
        cost_output.append({'Name':'Levelized cost of water','Value':self.LCOW,'Unit':'$/m3'})
        cost_output.append({'Name':'Levelized cost of heat (from fossile fuel)','Value':self.coh,'Unit':'$/m3'})
        cost_output.append({'Name':'Levelized cost of heat (from solar field)','Value':self.sam_coh,'Unit':'$/m3'})
        cost_output.append({'Name':'Energy cost','Value':self.STEC * (self.fuel_usage * self.coh + (1-self.fuel_usage) * self.sam_coh) + self.coe * self.SEEC,'Unit':'$/m3'})
         
        
        return cost_output
#%%

# case = LTMED_cost(Capacity = 1000,Prod = 328500,HEX_area = 400)
# print(case.lcow())
