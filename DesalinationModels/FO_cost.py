# -*- coding: utf-8 -*-
"""
Created on Thu Feb  6 14:04:17 2020

@author: zzrfl
"""

import numpy as np

class FO_cost(object):
    def __init__(self,
                 Capacity = 1000, # Desalination plant capacity (m3/day)
                 Prod = 328500, # Annual permeate production (m3)


                 # OPEX parameters
                 STEC = 30 , # Specifc thermal energy consumption (kWh/m3)
                 SEEC = 1, # Specifc electric energy consumption (kWh/m3)
                 Maintenance = 0.05, # Unit maintenance cost ($/m3)
                 
                 # Capital items
                 total_CAPEX     = 1345000, # Total capital cost ($)
                 Cap_membrane    = 11.5, # FO membrane cost (per unit capacity) ($ per m3/day)
                 Cap_HXs         = 13.8,
                 Cap_construct   = 22.3,
                 Cap_DS          = 8.9,
                 Cap_coalescers  = 4.8,
                 Cap_structural  = 4.5,
                 Cap_polishing   = 8.2,
                 Cap_pipes       = 5.2,
                 Cap_filtration  = 4.8,
                 Cap_electrical  = 3.3 ,
                 Cap_pumps       = 4.7,
                 Cap_instrumentation = 3.5,
                 Cap_valves      = 3.4,
                 Cap_CIP         = 1.1,
                 Cap_tanks       = 1.0,
                 Cap_pretreatment= 0.9, 
                 Cap_others      = 0,
                 
#                 GOR = 10.475,  # Gained output ratio
                # downtime = 0.1, # Yearly downtime of the plant (ratio)
                 yrs = 20, # Expected plant lifetime
                 int_rate = 0.04 , # Average interest rate
                 coe = 0.04 , # Unit cost of electricity ($/kWh)
                 coh = 0.01 , # Unit cost of heat ($/kWh)
                 sam_coh = 0.02, # Unit cost of heat from SAM ($/kWh)
                 cost_storage = 26 , # Cost of thermal storage ($/kWh)
                 storage_cap = 13422 # Capacity of thermal storage (kWh)

                 ):
        
        self.operation_hour = 24 #* (1-downtime) # Average daily operation hour (h/day)

        self.Capacity = Capacity
        self.STEC = STEC
        self.coe = coe

        self.coh = coh
        self.sam_coh = sam_coh
        self.total_CAPEX = total_CAPEX
        self.Prod = Prod
        self.SEEC = SEEC
        self.CAP_system =Cap_membrane + Cap_HXs + Cap_construct + Cap_DS + Cap_coalescers + Cap_structural + Cap_polishing \
                        + Cap_pipes + Cap_filtration + Cap_electrical +  Cap_pumps + Cap_instrumentation + Cap_valves \
                        + Cap_CIP  + Cap_tanks + Cap_pretreatment
        self.Maintenance = Maintenance


        self.yrs = yrs
        self.int_rate = int_rate
        self.cost_storage = cost_storage
        self.storage_cap = storage_cap
        
    def lcow(self):
        
        self.CAPEX = ((self.CAP_system * self.total_CAPEX /100+ self.cost_storage * self.storage_cap)*self.int_rate*(1+self.int_rate)**self.yrs) / ((1+self.int_rate)**self.yrs-1) / self.Prod 
        
        self.OPEX = self.coh * self.STEC + self.coe * self.SEEC + self.Maintenance
        
        self.LCOW = self.CAPEX + self.OPEX
        
        cost_output = []
        cost_output.append({'Name':'Desal Annualized CAPEX','Value':self.CAPEX,'Unit':'$/m3'})
        cost_output.append({'Name':'Desal OPEX','Value':self.OPEX,'Unit':'$/m3'})
        cost_output.append({'Name':'Levelized cost of water','Value':self.LCOW,'Unit':'$/m3'})
        cost_output.append({'Name':'Levelized cost of heat','Value':self.coh,'Unit':'$/m3'})
        cost_output.append({'Name':'Energy cost','Value':self.coh * self.STEC + self.coe * self.SEEC,'Unit':'$/m3'})
         
        
        return cost_output
#%%
if __name__ == '__main__':
    case = FO_cost(Capacity = 1000,Prod = 365000)
    print(case.lcow())