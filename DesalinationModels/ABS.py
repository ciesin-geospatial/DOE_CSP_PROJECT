# -*- coding: utf-8 -*-
"""
Converted from PSA's LT-MED general design model
Created on Wed Aug 28 10:01:06 2019

@author: Zhuoran Zhang
"""

import numpy as np
import math
import DesalinationModels.IAPWS97_thermo_functions as TD_func
# from DesalinationModels.LT_MED_calculation import lt_med_calculation
from scipy.optimize import fmin
from DesalinationModels.VAGMD_batch.SW_functions import SW_Density, BPE, SW_Enthalpy
from iapws import IAPWS97, SeaWater

class ABS(object):
    
    def __init__(self,
         Xf      =  35 , # Feedwater salinity  (g/L)
         Ts      =  80     , # The temperature of the steam at the inlet of the first bundle tube, C
         Nef     =  14  , # The feed water salinity, ppm
         Capacity = 2000,    # Capacity of the plant (m3/day)
         Tin     = 15 , # Inlet seawater temperature
         RR      = 50 , # recovery ratio
         Tcond   = 35, # Temperature of end condenser
         pump_type = 1, # Absorption Heat Pump type ('1' for single effect, '2' for double effect (serial flow), '3' for double effect (parallel flow))
         Fossil_f = 1 # Fossil fuel fraction
         ):
        
        self.Ts = Ts
        self.Nef = Nef
        self.Capacity = Capacity
        self.Fossil_f = Fossil_f
        self.Xf = Xf *1000
        self.RR = RR / 100
        self.Tin  = Tin
        self.Tcond = Tcond
        self.pump_type = pump_type
        self.TN = Tin +10
    def design(self):
        p1 = self.Xf
        p2 = self.RR
        p3 = self.Tin
        p4 = self.Capacity
        p5 = self.Ts
        qF_paras = [p1, p1**2, p2, p2*p1, p2*p1**2, p2**2, p2**2*p1, p3, p3*p1, p3*p1**2, p3**p2, p3*p2*p1, p3*p2**2, p3**2,
                    p3**2*p1, p3**2*p2, p4, p4*p1, p4*p1**2, p4*p2, p4*p2*p1, p4*p2**2, p4*p3, p4*p3*p1, p4*p3*p2, p4*p3**2, p4**2, p4**2*p1,
                    p4**2*p2, p4**2*p3, p5, p5*p1, p5*p1**2, p5*p2, p5*p2*p1, p5*p2**2, p5*p3, p5*p3*p1, p5*p3*p2, p5*p3**2, p5*p4, p5*p4*p1,
                    p5*p4*p2, p5*p4*p3, p5*p4**2, p5**2, p5**2*p1, p5**2*p2, p5**2*p3, p5**2*p4, 1, p5**3, p4**3, p3**3, p2**3, p1**3]
        paras = [p1, p2, p2*p1, p3, p3*p1, p3*p2, p4, p4*p1, p4*p2, p4*p3, p5, p5*p1, p5*p2, p5*p3, p5*p4, 1, p5**2, p4**2, p3**2, p2**2,p1**2]
        if self.Nef == 12:
            coeffs = [
                [3.78E-06,9.475024108,-6.71E-06,0.025502496,-5.68E-08,0.002142361,5.26E-06,7.48E-13,-4.13E-07,1.90E-08,-0.026811842,1.76E-08,-0.00403125,-9.75E-05,-7.06E-08,8.13073955,0.000113009,1.86E-12,-6.60E-05,-7.186574074,3.50E-13],
                [-9.60E-06,-21.51409613,2.42E-05,-0.061912353,2.07E-07,0.030173611,0.001216995,-1.40E-10,-0.000380288,-2.24E-06,0.137686707,-6.94E-08,-0.032135417,0.000468958,2.43E-06,0.35824605,-0.000958009,-6.89E-11,0.000166019,27.46921296,3.29E-13],
                [3.33E-06,0.677813505,-1.60E-05,-0.046184467,-7.50E-08,-0.001725347,-1.85E-05,-2.02E-12,-1.19E-06,3.47E-08,0.168129352,-6.74E-08,2.40E-05,-0.000370854,2.54E-07,-4.754444471,-0.000497023,-2.28E-11,-0.000111815,-0.58099537,-6.56E-11,],
                [-0.00230634,-15202.30125,0.005467824,0.095607094,1.65E-06,-0.116666667,0.215904117,-7.71E-08,-0.267987407,1.54E-06,-0.108918713,1.62E-08,0.279166667,-0.002399306,-4.49E-06,2970.129599,0.000423611,4.42E-11,0.001111111,18672.98611,9.07E-10,],
                [0.000141792,6.98288098,0.000100856,0.634134693,4.00E-06,0.193006944,8.28E-05,2.79E-10,1.48E-05,7.93E-07,-1.119140682,-4.08E-06,-0.213583333,-0.015357535,-1.66E-06,36.54209567,0.01065544,1.36E-10,0.00857912,2.04537037,7.11E-10,]
                ]

        if self.Nef == 14:
            coeffs = [
                [4.93E-06,12.14444444,-9.44E-06,0.017453704,-8.52E-08,0.003333333,-5.59E-21,1.54E-24,1.74E-20,-5.52E-23,-0.018157407,3.33E-08,-0.005,5.00E-05,-1.06E-21,8.660509259,7.41E-06,2.76E-25,-9.26E-05,-9.203703704,-4.12E-12,],
                [-9.73E-06,-22.67687709,2.75E-05,-0.010527825,2.27E-07,0.023135417,0.001127253,-1.16E-10,-0.000384457,-1.68E-06,0.011084368,-1.09E-07,-0.018871528,-0.000242465,1.49E-06,4.266662392,4.93E-05,-8.73E-14,0.000185856,27.85023148,1.35E-11,],
                [6.75E-07,0.931018519,-1.66E-05,-0.069638611,-6.36E-08,-0.002311111,-2.91E-20,5.67E-25,1.48E-20,1.32E-22,0.072969167,-5.47E-08,-0.002188889,-3.17E-06,-5.42E-23,-1.027806019,-1.78E-06,3.88E-25,-3.44E-06,-0.68,-5.22E-11,],
                [-0.002387192,-15205.67551,0.005463889,0.022750069,2.02E-06,-0.070486111,0.215886167,-7.70E-08,-0.268027502,1.13E-06,-0.031589059,2.78E-08,0.240625,-0.0016875,-3.60E-06,2970.837205,-0.000141204,-1.89E-11,0.00081713,18679.35185,1.65E-09,],
                [0.000172627,6.280192354,0.000188127,0.755528969,6.46E-06,0.338440972,1.65E-08,-1.50E-14,-2.10E-08,9.16E-12,-1.050862538,-6.11E-06,-0.32046875,-0.02017691,-6.30E-11,33.68053424,0.011342014,-2.27E-14,0.011636528,5.718055556,1.34E-09,]
                ]          
            
        if self.Nef == 16:
            coeffs = [
                [6.18E-06,15.06805556,-1.35E-05,0.019685185,-1.26E-07,0.0025,1.09E-19,9.04E-25,5.41E-21,-9.30E-22,-0.019824074,5.74E-08,-0.005555556,7.78E-05,-1.94E-21,9.242962963,-1.85E-06,-9.43E-26,-0.000118519,-11.35185185,-8.23E-12,],
                [-1.06E-05,-22.79269847,3.05E-05,-0.010484096,2.67E-07,0.025336806,0.001024431,-9.68E-11,-0.000380987,-1.44E-06,0.009776589,-1.25E-07,-0.019774306,-0.000281181,1.32E-06,4.357185487,7.20E-05,1.79E-13,0.000188981,27.84259259,1.33E-11,],
                [7.36E-07,0.932166667,-1.69E-05,-0.060634167,-6.45E-08,-0.002480556,-2.84E-20,2.04E-25,1.06E-20,1.43E-22,0.064106111,-5.49E-08,-0.002052778,-3.28E-06,1.42E-22,-0.943036574,-2.63E-06,3.41E-25,-3.13E-06,-0.68462963,-5.33E-11,],
                [-0.002376352,-15203.25577,0.005467593,0.017976383,2.00E-06,-0.06875,0.215886212,-7.70E-08,-0.26807285,9.48E-07,-0.085658082,2.55E-08,0.204513889,-0.001583333,-3.11E-06,2972.305599,0.000277778,1.45E-11,0.000791667,18679.44444,1.53E-09,],
                [0.000254866,9.327583362,0.000417519,0.962597788,1.24E-05,0.712548611,1.49E-09,8.32E-15,-5.90E-09,3.16E-11,-1.494248195,-1.18E-05,-0.680930556,-0.031864271,6.60E-11,46.37199204,0.01819,-4.17E-14,0.018914444,15.24027778,3.08E-09,]
                ]
        if self.Nef in [14,16]:
            self.GOR = np.dot(paras,coeffs[0])
            self.qs = np.dot(paras,coeffs[1])
            self.DELTAT = np.dot(paras,coeffs[2]) # the difference between the condensation temperature in the evaporator and the vapor temperature in such effect
            self.sA = np.dot(paras,coeffs[4])
            self.qF = np.dot(paras, coeffs[3])
        
        else:
            Xf, RR, TN, Ts = self.Xf, self.RR, self.TN, self.Ts
            GOR_paras = [Xf, RR, RR* Xf, TN, TN*Xf, TN*RR, Ts, Ts*Xf, Ts*RR, Ts*TN, 1 , Ts**2, TN**2, RR**2, Xf**2]
            sA_paras  = [Xf,    Xf**2,  RR,         RR*Xf,      RR*Xf**2,   RR**2,      RR**2*Xf,
                         TN,    TN*Xf,  TN*Xf**2,   TN*RR,      TN*RR*Xf,   TN*RR**2,   TN**2,
                         TN**2*Xf, TN**2*RR, Ts, Ts*Xf, Ts*Xf**2, Ts*RR, Ts*RR*Xf, 
                         Ts*RR**2, Ts*TN, Ts*TN*Xf, Ts*TN*RR, Ts*TN**2, Ts**2, Ts**2*Xf,
                         Ts**2*RR, Ts**2*TN, 1, Ts**3, TN**3, RR**3, Xf**3]
            
            GOR_coeffs = {3:[1.60E-07,0.826895712,-2.04E-07,0.003340838,-5.56E-09,0.000666667,-0.003295958,1.17E-10,-0.000549708,-2.46E-06,2.662545127,-1.98E-07,7.41E-07,-0.675925926,-4.12E-13],
                          6:[5.86E-07,2.940942982,-1.44E-06,0.007985234,-2.26E-08,0.001472222,-0.007157144,8.73E-09,-0.001540936,4.88E-06,4.741753363,-1.04E-06,-1.67E-05,-2.333333333,-7.41E-13],
                          9:[1.67E-06,5.9507846,-3.94E-06,0.012607651,-5.50E-08,0.002222222,-0.010203548,2.47E-08,-0.002549708,2.94E-05,6.350104873,-1.05E-05,-5.09E-05,-4.653703704,-2.88E-12],
                          12:[3.30E-06,9.621851852,-7.98E-06,0.016637037,-1.09E-07,0.002,-0.012637326,5.13E-08,-0.003277778,8.28E-05,7.592772368,-3.09E-05,-9.98E-05,-7.425925926,-6.09E-12],
                          15:[5.18E-06,13.78669547,-1.35E-05,0.020924649,-1.83E-07,0.000277778,-0.014688955,9.82E-08,-0.002836257,0.000158919,8.538343343,-6.45E-05,-0.000167731,-10.58982036,-1.63E-11]}
            
            sA_coeffs  = {3:[0.000596217,-3.66E-09,0,-2.44E-05,1.93E-09,0,5.60E-05,0,-2.95E-07,5.30E-11,0,7.14E-06,0,0.064807392,2.06E-07,0.00974051,0,-1.16E-05,-3.96E-11,0,-5.27E-06,0,-0.05718687,-2.61E-07,-0.011936049,-0.000702529,0.013464849,1.65E-07,0.003686623,0.000759933,0,-0.00019293,-0.000182949,0,3.20E-14],
                          6:[0.00040105,-6.57E-09,0,-1.56E-05,3.67E-10,0,2.62E-05,0,7.08E-07,8.73E-12,0,1.46E-06,0,0.032775092,5.04E-08,0.002499309,0,-3.30E-06,-6.53E-12,0,-1.02E-06,0,-0.028641745,-6.66E-08,-0.002735652,-0.000301667,0.005600544,4.10E-08,0.000713386,0.000329733,0,-7.31E-05,-0.00010089,0,4.94E-14],
                          9:[0.000596217,-3.66E-09,0,-2.44E-05,1.93E-09,0,5.60E-05,0,-2.95E-07,5.30E-11,0,7.14E-06,0,0.064807392,2.06E-07,0.00974051,0,-1.16E-05,-3.96E-11,0,-5.27E-06,0,-0.05718687,-2.61E-07,-0.011936049,-0.000702529,0.013464849,1.65E-07,0.003686623,0.000759933,0,-0.00019293,-0.000182949,0,3.20E-14],
                          12:[0.000894724,1.62E-08,0,-0.000287808,1.22E-08,0,0.00028908,0,-1.82E-05,2.99E-10,0,3.71E-05,0,0.130413747,8.00E-07,0.040822216,0,-3.51E-05,-2.21E-10,0,-2.85E-05,0,-0.110185354,-9.65E-07,-0.05537221,-0.001731678,0.03194821,6.33E-07,0.019196432,0.001859674,0,-0.000543621,-0.000374878,0,-9.94E-14],
                          15:[0.005685486,2.79E-07,0,-0.01767792,4.20E-07,0,0.014972954,0,-0.000685465,5.31E-09,0,0.001021958,0,0.598562516,9.56E-06,0.879295485,0,-0.000125358,-3.88E-09,0,-0.000845281,0,-0.237595008,-1.07E-05,-1.342398325,-0.012480131,0.109771476,7.64E-06,0.527896922,0.013668637,0,-0.004866016,-0.003499437,0,-2.36E-12]}
            
            self.GOR = np.dot(GOR_paras, GOR_coeffs[self.Nef])
            self.sA  = np.dot(sA_paras, sA_coeffs[self.Nef])
            
            self.qF = self.Capacity / self.RR / 24
            self.qs = self.Capacity * 1000 / self.GOR / 24 / 3600
            
            
        
        
        self.T_d = self.Tin + 10  # Brine temperature at last effect 
        
        # Calculate cooling water flow rate
        Q_loss = 0.054 # System thermal loss
        
            # mass balance
        q_d = self.Capacity / 24 # Hourly distillate production (m3/hr)
        self.q_feed = q_d / self.RR # Feed seawater flow rate (m3/hr)
        q_b = self.q_feed - q_d # Brine flow rate (m3/hr)

        self.s_b = self.Xf /1000/ (1- self.RR) #  brine salinity (g/L)
 
            # BPE calculation
        SW_BPE = BPE(self.T_d, self.s_b)
        
        self.T_b =  self.T_d + SW_BPE # brine temperature
        self.T_cool = self.T_d - 3 # cooling reject temperature (Assume DHTP = 3)
        
            # densities
        rho_b = SW_Density(self.T_b,'c',self.s_b*1000,'ppm',1,'bar')  # brine density
        rho_d = SW_Density(self.T_d,'c',0,'ppm',1,'bar')  # distillate density
        rho_sw= SW_Density(self.Tin,'c',self.Xf,'ppm',1,'bar')  # seawater density
        rho_f = SW_Density(self.T_cool,'c',self.Xf,'ppm',1,'bar')  # cooling reject density
        
            # enthalpies
        h_d = IAPWS97(T=273.15+ self.T_d,x=0).h 
        h_b = SW_Enthalpy(self.T_b, self.s_b)/ 1000
        h_sw = SW_Enthalpy(self.Tin, self.Xf/1000)/ 1000
        h_cool = SW_Enthalpy(self.T_cool, self.Xf/1000)/ 1000
        
            # energy consumption
        self.STEC = 1/self.GOR * (TD_func.enthalpySatVapTW(self.Ts+273.15)-TD_func.enthalpySatLiqTW(self.Ts+273.15))[0] *rho_d/3600
        self.P_req = self.STEC *self.Capacity /24 
        
            # mass flow rates
        self.m_d = q_d * rho_d / 3600 # distillate mass flow rate (kg/s)
        self.m_b = q_b * rho_b / 3600 # brine mass flow rate (kg/s)
        self.m_f = self.q_feed * rho_f / 3600 # feed mass flow rate (kg/s)
        self.m_sw = ((1-Q_loss)*self.P_req - self.m_b * h_b - self.m_d * h_d + h_cool * self.m_f) / (h_cool - h_sw) # intake + cooling water mass flow rate (kg/s)
        
        
            # volume flow rates
        self.q_sw = self.m_sw / rho_sw * 3600 # m3/h
        self.q_cooling = self.q_sw - self.q_feed 
        
        
        self.PR = 2326 / self.STEC * 1000 /3600       
        
        
        # Add ABS  
        pp1 = self.Tcond
        pp2 = self.Ts

        if self.pump_type == 1:
            abs_coeff = [
                [0.009258,-0.0082026,-0.0001356,1.9532,5.4857e-5,7.8857e-5],
                [0.1686,0.0024348,4.7353e-5,-0.17905,-0.0085011,-0.00012585,-1.4067e-6,0.0052416,0.00016374,1.7127e-6,-6.8253e-5,-1.1867e-6,2.5029,3.44e-7,4.7067e-7],
                [-0.328,1.20229,-0.008,10.8171,0.00457143,0.00457143],
                [-0.736,1.808,-0.0264,22.0257,0.012,0.0142857]]
            abs_params = [
                [pp1, pp2, pp1*pp2, 1, pp2**2, pp1**2],
                [pp1, pp1**2, pp1**3, pp2, pp1*pp2, pp2*pp1**2, pp2*pp1**3,pp2**2,pp2**2*pp1,pp2**2*pp1**2,pp2**3,pp2**3*pp1,1,pp2**4,pp1**4],
                [pp1, pp2, pp1*pp2, 1,pp2**2, pp1**2],
                [pp1, pp2, pp1*pp2, 1,pp2**2, pp1**2]
                ]
       
        elif self.pump_type == 2:
            abs_coeff = [
                [0.02266,-0.022654,-0.0003024,2.8248,0.00014057,0.00017086],
                [0.0083408,-0.0097175,-0.0001152,0.97403,5.8114e-5,7.8286e-5],
                [-0.038,1.1574,-0.0068,3.0757,0.0028571,0.0028571],
                [-0.446,1.98886,-0.0956,37.9357,0.0417143,0.0514286]]
            abs_params = [
                [pp1, pp2, pp1*pp2, 1,pp2**2, pp1**2],
                [pp1, pp2, pp1*pp2, 1,pp2**2, pp1**2],
                [pp1, pp2, pp1*pp2, 1,pp2**2, pp1**2],
                [pp1, pp2, pp1*pp2, 1,pp2**2, pp1**2]                ]
        
        elif self.pump_type == 3:
            abs_coeff = [
                [0.023072,-0.022487,-0.0003024,2.8621,0.00013829,0.000168],
                [0.0067028,-0.0058181,-3.128e-5,0.80108,4.5714e-6,2.7771e-5],
                [-0.216,1.376,-0.0032,-1.4743,8.7918e-17,0.0022857],
                [-0.468,1.15086,-0.1136,70.5714,0.0537143,0.0657143]]

            abs_params = [
                [pp1, pp2, pp1*pp2, 1,pp2**2, pp1**2],
                [pp1, pp2, pp1*pp2, 1,pp2**2, pp1**2],
                [pp1, pp2, pp1*pp2, 1,pp2**2, pp1**2],
                [pp1, pp2, pp1*pp2, 1,pp2**2, pp1**2]                ]
        
        self.COP = np.dot(abs_params[0],abs_coeff[0])
        self.sA_pump = np.dot(abs_params[1],abs_coeff[1])        
        self.T_sh = np.dot(abs_params[2],abs_coeff[2])        
        self.T_gen = np.dot(abs_params[3],abs_coeff[3])
        self.P_req /= self.COP     

        self.STEC = self.STEC / self.COP
        self.PR = self.PR * self.COP
        self.GOR = self.GOR * self.COP
        
        brine_s = self.Xf /1000/ (1 - self.RR)
        
        self.design_output = []
#        design_output.append({'Name':'Number of modules required','Value':self.num_modules,'Unit':''})
#        design_output.append({'Name':'Permeate flux of module','Value':self.Mprod,'Unit':'l/h'})
#        design_output.append({'Name':'Condenser outlet temperature','Value':self.TCO,'Unit':'oC'})
#        design_output.append({'Name':'Permeate flow rate','Value': self.F * self.num_modules,'Unit':'l/h'})    
        self.design_output.append({'Name':'Thermal power requirement','Value':self.P_req/1000 ,'Unit':'MW(th)'})
        self.design_output.append({'Name':'Specific thermal power consumption','Value':self.STEC,'Unit':'kWh(th)/m3'})
        self.design_output.append({'Name':'Brine concentration','Value':brine_s,'Unit':'g/L'})
        
        self.design_output.append({'Name':'Feedwater flow rate','Value':self.qF,'Unit':'m3/h'})     
        if self.q_cooling> 0:
            self.design_output.append({'Name':'Cooling water flow rate','Value':self.q_cooling ,'Unit':'m3/h'})         
        self.design_output.append({'Name':'The mass flow rate of the steam','Value':self.qs,'Unit':'kg/s'})
        self.design_output.append({'Name':'Specific heat transfer area of MED','Value':self.sA,'Unit':'m2/m3/day'})
        self.design_output.append({'Name':'Specific heat transfer area of the absorption heat pump','Value':self.sA_pump,'Unit':'m2/kW'})      
        self.design_output.append({'Name':'Overall performance ratio','Value':self.PR * self.COP,'Unit':''})   
        self.design_output.append({'Name':'Outlet temperature of the superheated steam from the heat pump','Value':self.T_sh,'Unit':'oC'}) 
        self.design_output.append({'Name':'Temperature of the saturated steam required to drive the heat pump generator','Value':self.T_gen,'Unit':'oC'})   
        self.design_output.append({'Name':'Gained output ratio','Value':self.GOR,'Unit':'kg permeate/kg permeate'})  
        # self.design_output.append({'Name':'Delta T','Value':self.DELTAT,'Unit':'oC'})
        # if self.DELTAT < 2:
        #     self.design_output.append({'Name':'Warning','Value':'Delta T is too small, cost might be high','Unit':''})
        
        
        
        
        # self.design_output.append({'Name':'Specific heat exchanger area','Value':self.system.sA,'Unit':'m2/(kg/s)'}) 
        
        return self.design_output
        
    def simulation(self, gen, storage):
        self.thermal_load = self.P_req # kW
        self.max_prod = self.Capacity /24 # m3/h
        self.storage_cap = storage * self.thermal_load # kWh
        
        to_desal = [0 for i in range(len(gen))]
        to_storage =  [0 for i in range(len(gen))]
        storage_load =  [0 for i in range(len(gen))]
        storage_cap_1 =  [0 for i in range(len(gen))]
        storage_cap_2 = [0 for i in range(len(gen))]
        storage_status =  [0 for i in range(len(gen))]
        solar_loss =  [0 for i in range(len(gen))]
        load =  [0 for i in range(len(gen))]
        prod =  [0 for i in range(len(gen))]
        fuel =  [0 for i in range(len(gen))]   
        energy_consumption =  [0 for i in range(len(gen))] 
        for i in range(len(gen)):
            to_desal[i] = min(self.thermal_load, gen[i])
            to_storage[i] = abs(gen[i] - to_desal[i])
            storage_load[i] = gen[i] - self.thermal_load
            if i != 0:
                storage_cap_1[i] = storage_status[i-1]
            storage_cap_2[i] = max(storage_load[i] + storage_cap_1[i], 0)
            storage_status[i] = min(storage_cap_2[i] , self.storage_cap)
            solar_loss[i] = abs(storage_status[i] - storage_cap_2[i])
            load[i] = to_desal[i] + max(0, storage_cap_1[i] - storage_cap_2[i])
            if load[i] / self.thermal_load < self.Fossil_f:
                fuel[i] = self.thermal_load - load[i]
            energy_consumption[i] = fuel[i]+load[i]     
            prod[i] = (fuel[i]+load[i] )/ self.thermal_load * self.max_prod
        Month = [0,31,59,90,120,151,181,212,243,273,304,334,365]
        Monthly_prod = [ sum( prod[Month[i]*24:(Month[i+1]*24)] ) for i in range(12) ]
               
        simu_output = []
        simu_output.append({'Name':'Water production','Value':prod,'Unit':'m3'})
        simu_output.append({'Name':'Storage status','Value':storage_status,'Unit':'kWh'})
        simu_output.append({'Name':'Storage Capacity','Value':self.storage_cap,'Unit':'kWh'})
        simu_output.append({'Name':'Fossil fuel usage','Value':fuel,'Unit':'kWh'})
        simu_output.append({'Name':'Total water production','Value':sum(prod),'Unit':'m3'})
        simu_output.append({'Name':'Monthly water production','Value': Monthly_prod,'Unit':'m3'})
        simu_output.append({'Name':'Total fossil fuel usage','Value':sum(fuel),'Unit':'kWh'})
        simu_output.append({'Name':'Percentage of fossil fuel consumption','Value':sum(fuel)/max(1,sum(energy_consumption))*100,'Unit':'%'})        
        simu_output.append({'Name':'Solar energy curtailment','Value':solar_loss,'Unit':'kWh'})
        simu_output.append({'Name':'Curtailed solar thermal energy','Value':(sum(gen) - sum(load)) / 1000000 ,'Unit':'GWh'})   
        simu_output.append({'Name':'Percentage of curtailed energy','Value':(sum(gen) - sum(load)) / sum(gen) * 100 ,'Unit':'%'})
               
        return simu_output
            
#%% MODEL EXECUTION            
# for t in range(15, 85, 5):
#     case = lt_med_general(Xf = 30, RR = 0.5, Tin = t, Capacity = 51000, Ts = 80, Nef = 12)
#     case.design()
#     print("Tin:", t, "STEC: ", case.design_output[1]['Value'], "GOR: ", case.design_output[4]['Value'])
#case.simulation(gen = [5000,6000,5000,3000,2500], storage =6)
            
        
        