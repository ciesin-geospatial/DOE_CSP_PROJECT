# -*- coding: utf-8 -*-
"""
Created on Tue Sep  3 13:52:41 2019
Reverse Osmosis Design Model- Fixed Load, fixed pump efficiency, fixed salinity 
Notes:
Can later insert flags for fixed load operation and variable load operation. 
If variable load operation, there would need to be some given relationship between 
pump power consumption and flow/pressure provided to RO. Also, if using centrifugal pumps 
(would use this for RO system > ~4000 m3/day), there is a variable pump efficiency profile 
to consider. If using positive displacement pumps (use for smaller RO systems < 4000 m3/day), 
can assume a relatively constant efficiency but different relationships between power and 
flow/pressure. Typically, pressure varies less, while flow rate is more significantly
altered as power shifts. 
@author: adama
"""
from numpy import array,cumprod,insert
from numpy.matlib import repmat
from math import ceil, exp
from warnings import warn

#class RODesign:
#
#    def __init__(self,
###### (soon to be)JSON Inputs (Inputs available in GUI for user to modify)
# Fluid properties
Cf=32#,                # Feed TDS, g/L or parts per trillion
T=298.15#,            # Feedwater Temperature [Kelvin]


#Pump and ERD Parameters
nERD=0.95#,            # Energy recovery device efficiency
nBP=0.8
nHP=0.8
nFP=0.8


#RO Plant Design Specifications
nominal_daily_cap_tmp=550000#,
Nel1=8#,              #number elements per vessel in stage 1
R1=0.4#,               #Desired overall recovery rate







# RO Membrane Property Inputs: 
#load in from a table of membrane types w/properties or enter manually.
# Using default values here based on manufacturer's datasheet for seawater RO membrane element: SWC4B MAX
Qpnom1=27.3/24.0#,      #nominal permeate production per membrane element (m3/hr)
Am1=40.8#,            #membrane area per membrane element (m^2) 
Pmax1=82.7#,          #Max pressure of membrane element (bar)
Ptest1=55.2#,         #Applied test pressure for each mem element
Ctest1=32#,           #membrane manufacturer's test feed salinity (TDS) for each element (parts per thousand)
SR1=99.8#,            #rated salt rejection of each element (%)
Rt1=.1#,              #Test recovery rate for each element
Pdropmax=1           #maximum pressure drop per membrane element (bar)
Pfp=1
Tmax=318.15
minQb=2.7            #minimum concentrate flow per module (m3/h)
maxQf=17             #maximum feed flow per module (m3/h)
#                ):

   
#                self.CP=CP
#                self.nERD=nERD
#                self.nominal_daily_cap_tmp=nominal_daily_cap_tmp
#                self.Nel1=Nel1
#                self.R1=R1
#                self.Cf=Cf    
#                
#                    
#                self.T=T
#                
#                if(self.T>343.15):
#                    self.T=343.15
#                    warn("The temperature should be below 45 degrees Celsius (343.15 K) to avoid membrane damage.")

# Constants################################################################
# Osmotic pressure calculated assuming the van't Hoff equation and NaCl
vhfactor=2          # van't Hoff factor

MW_nacl=58.443      # molecular weight of NaCl
Ru=0.0831           # Universal Ideal Gas constant
Rel=1/6             #max element recovery rate based on manufacturer's recommended ratio of 5:1 for Qb:Qp
Rel_avg=1-(1-R1)**(1/Nel1)             #average recovery rate per element based on DOW Filmtec Technical Guide documentation
CPavg=exp(0.7*Rel_avg)#,    # empirical relationship for average concentration polarization factor from DOW Filmtec documentation
CPb=exp(0.7*Rel)
CPtest=exp(0.7*Rt1)
#Intermediate Computations
#Bs salt permeability
Bs1=Qpnom1/Am1*(1-SR1/100)*Ctest1/CPtest/(Ctest1/(1-Rt1)-(1-SR1/100)*Ctest1)
#estimated osmotic pressure for test conditions corresponding to each element
Posm1=vhfactor*Ru*T*CPtest/MW_nacl*Ctest1*(1-(1-SR1/100))/(1-Rt1)
#estimated net driving pressure used in testing each element
NDP1=Ptest1-Posm1
#assuming constant membrane water permeability for each element, calculated
#from test conditions
A1=Qpnom1/(Am1*NDP1)                 # membrane water permeability ###COULD ALSO BE AN INPUT

Pd=Pdropmax*Nel1                     #(simplified/conservative) MAX Pressure drop across feed channel per element * number of elements [bar]

i_nel=cumprod(repmat((1-Rel),(Nel1-1),1)) # fraction of feed volume entering elements 2 - final element, Nel
i_nel=insert(i_nel,0,1)             # fraction of feed volume entering elements 1 - Nel

## Computed values that can/should be displayed to the user upon entering inputs in GUI

R1_max=sum(Rel*(i_nel))                         #max recovery for stage by summing recovered fraction of each element
#NV1=ceil(nominal_daily_cap_tmp/Qpnom1/Nel1/24)  # Compute number of pressure vessels
NV1=ceil(nominal_daily_cap_tmp/24/17/R1)  # Compute number of pressure vessels

nominal_daily_cap=Qpnom1*Nel1*NV1*24            # Compute daily RO permeate production in m3/day

Qp1=nominal_daily_cap_tmp/24                    # use the input provided by user for daily capacity desired
NDP1=Qp1/(Nel1*NV1*Am1*A1)

Posm_f=vhfactor*Ru*T/MW_nacl*Cf
Posm_b=vhfactor*Ru*T/MW_nacl*Cf/(1-R1)
Posm_avgmem=CPavg*(Posm_f+Posm_b)*0.5    #average feed-side osmotic pressure at the membrane interface

Cm_avg=CPavg*(Cf+Cf/(1-R1))*0.5

Cp=Bs1*Cm_avg*Nel1*NV1*Am1/Qp1    #permeate concentration from DOW system average performance equations
Posm_perm=vhfactor*Ru*T/MW_nacl*Cp

#Pf1=Posm_b + Pd
#NDPf=Pf1-Posm_f
#NDPb=Pf1-Posm_b-Pd
#R1=1-vhfactor*Ru*T*CP/MW_nacl*Cf/(Pf1tmp-Pd-NDP1)
#NDPavg=Pf1-(CPavg*(Posm_f+Posm_b)+Pd)*0.5


Pf1=NDP1 + Posm_avgmem + Pd*0.5 - Posm_perm
Pb1=Pf1-Pd
Pbp=Pf1-nERD*Pb1

Qf1=Qp1/R1
Qb1=Qf1-Qp1
Qbp=Qb1
Qhp=Qp1

Qp1
if(Qb1>minQb*NV1)==0: 
    print("\nConcentrate flow rate is %s m3/h but should be greater than %s m3/h" % (Qb1,(2.7*NV1)))
    
if(Qf1<maxQf*NV1)==0:
    print("\nFeed flow rate is %s m3/h but should be less than %s m3/h" % (Qf1,(17*NV1)))
if(Pf1<=Pmax1)==0:
    print("\nFeed pressure is %s bar but should be less than %s bar" % (Pf1,(Pmax1)))
if T>Tmax:
    print("\nFeed temperature is %s K but should be less than %s K" % (T,(Tmax)))


BP_power=Qbp*Pbp/nBP/36
HP_power=Qhp*Pf1/nHP/36
FP_power=Qf1*Pfp/nFP/36
PowerTotal=FP_power+HP_power+BP_power
PowerRO=HP_power+BP_power
SEC=PowerTotal/Qp1
SEC_RO=PowerRO/Qp1

print("\nFeed flow rate, m3/h = %.2f\nBrine flow rate, m3/h = %.2f\nPermeate flow rate, m3/h = %.2f\nSpecific Energy Consumption, kWh/m3 = %.2f\nSpecific Energy Consumption of RO, kWh = %.2f\nTotal Power Consumption, kW= %.2f\nRO Power Consumption, kW = %.2f\nPermeate Concentration, mg/L = %.1f\n"\
      % (Qf1,Qb1,Qp1,SEC,SEC_RO,PowerTotal,PowerRO,Cp*1000))

#print("\nNDP1 = %.2f\nNDPf = %.2f\nNDPb = %.2f\nPf1 = %.2f\n" % (NDP1,NDPf,NDPb,Pf1))