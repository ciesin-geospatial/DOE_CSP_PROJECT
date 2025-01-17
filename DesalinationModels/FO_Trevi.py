# -*- coding: utf-8 -*-
"""
Created on Wed Sep  4 11:28:52 2019
Converted from an Excel Model developed by Trevi Systems Inc. and shared by 
Michael Greene, Director of Manufacturing

It's a model used to size heat exhcangeers for the systems, design
heat exchangers and system flows

AAA- March 13, 2020
To apply a cost model for this system, we should modify this code to return output
parameters such as:
--design capacity of FO 
--permeate flux per FO module
--FO membrane area




@author: zzrfl
"""
import numpy as np
from scipy.interpolate import interp1d, griddata


class FO_Trevi(object):
    
    # Define input variables
    def __init__(self,
                 Salt_rej = 0.95   , # Salt rejection
                 Mprod    = 1      , # Product water flow rate (m3/day)
                 T_sw     = 13     , # Seawater temperature (oC)
                 NF_rcr   = 0.2    , # Nanofilter retentate recirculation rate 
                 RO_r     = 0.1    , # RO retentate reject rate
                 A        = 0.8    , # Percentage of pure draw in strong draw
                 p_margin = 0      , # Desired DP of strong draw over seawater osmotic pressure in psi
                 p_weak   = 545.35 , # Required polymer osmotic pressure in psi
                 DS_c_p   = [[3.23608, 30.32329, 84.258, 174.14918, 316.77652, 516.69451, 825.68047, 1344.052947, 1753.477316],[1.00258,10.055,19.9824,29.9461,40.0552,49.9181,60.0252,70.0398,72.9075]],
                 # Polymer concentration as function of osmotic pressure (look-up table)
                 r        = 0.3    , # Recovery rate
                 salinity = 0.034  , # Salinity (%)
                 hm       = 105    , # Heat of mixing per m3 of product water for swing (MJ)
                 DS_density = [[0,0.57492,1.01314,2.06163,4.00907,8.07857,10.29748,20.322,38.57126,56.59887,66.45577,71.81646,84.16594,100],[1000,1001,1001.4,1002.95,1005.6,1011.26,1013.99,1027.94,1053.67,1073.775,1080.52,1086.355,1083.684,1069.866]],
                 # Draw solution density as function of concentration
                 DS_heatcap    = [[0,30,45,60,85],[4.1855,3.332,2.852,2.569,2.205]], # Draw solution specific heat capacity
                 DS_conductivity = [[0,30,45,60,85], [0.588,0.426,0.347,0.294,0.208]], # Draw solution thermal conductivity
                 T_memb        = 14.6338, # Membrane temperature (deg C)
                 T_wd          = 16, # Weak draw temperature after Weak/Brine HX (oC)
                 T_prod        = 23, # Product water temperature (oC)
                 f_cin_1A      = 1.515, # Strong draw flow rate entering HX 1A
                 T_cout_1A     = 16.79, # Cold side outlet temperature in HX 1A
                 T_hin_1A      = 23,  # Hot side inlet temperature in HX 1A
                 T_hout_1A     = 23,  # Hot side outlet temperature in HX 1A
                 T_cout_1B     = 74.5,  # Cold side outlet temperature in HX 1B
                 T_hin_1B      = 89,  # Hot side inlet temperature in HX 1B
                 T_hin_1C      = 93,  # Hot side inlet temperature in HX 1C
                 T_hout_1C     = 83,  # Hot side outlet temperature in HX 1C
                 f_hin_1C      = 1.58, # Water flow rate entering HX 1C
                 T_cout_1C     = 90, # Cold side outlet temperature in HX 1C
                 T_hin_2A      = 23,  # Hot side inlet temperature in HX 2A
                 T_hout_2A     = 23,  # Hot side outlet temperature in HX 2A
                 T_cout_2A     = 16.79,  # Cold side outlet temperature in HX 2A
                 T_hin_2B      = 89,  # Hot side inlet temperature in HX 2B
                 T_cout_2B     = 74.5,  # Cold side outlet temperature in HX 2B
                 f_hin_2C      = 1.88, # Water flow rate entering HX 2C
                 T_hout_2C     = 83, # Hot side outlet temperature in HX 2C
                 T_cout_2C     = 90, # Cold side outlet temperature in HX 2C
                 T_hout_6      = 23, # Hot side outlet temperature in HX 6 (Brine outlet temperature)
                 f_sw_sup      = 0.6, # Supplemental water flow rate
                 T_hout_4      = 20, # Hot side outlet temperature in HX 4
                 T_cout_4      = 19, # Cold side outlet temperature in HX 4 (Seawater outlet temperature)
                 T_cout_5      = 13, # Cold side outlet temperature in HX 5 
                 # Seawater density look-up table
                 SW_d_temp  = [0,10,20,30,40,50,60,70,80,90,100,110,120],  # Temperature (deg C)
                 SW_d_salinity = [0,0.01,0.02,0.03,0.04,0.05,0.06,0.07,0.08,0.09,0.1,0.11,0.12],
                 SW_d_density = [[999.8,1007.9,1016,1024,1032,1040,1048,1056.1,1064.1,1072.1,1080.1,1088.1,1096.2],
                                 [999.7,1007.4,1015.2,1023,1030.9,1038.7,1046.6,1054.4,1062.2,1070.1,1077.9,1085.7,1093.6],
                                 [998.2,1005.7,1013.4,1021.1,1028.8,1036.5,1044.1,1051.8,1059.5,1067.2,1074.9,1082.6,1090.3],
                                 [995.7,1003.1,1010.7,1018.2,1025.8,1033.4,1040.9,1048.5,1056.1,1063.6,1071.2,1078.7,1086.3],
                                 [992.2,999.7,1007.1,1014.6,1022.1,1029.5,1037,1044.5,1052,1059.4,1066.9,1074.4,1081.6],
                                 [988,995.5,1002.9,1010.3,1017.7,1025.1,1032.5,1039.9,1047.3,1054.7,1062.1,1069.5,1076.9],
                                 [983.2,990.6,998,1005.3,1012.7,1020,1027.4,1034.7,1042.1,1049.5,1056.8,1064.2,1071.5],
                                 [977.8,985.1,992.5,999.8,1007.1,1014.5,1021.8,1029.1,1036.5,1043.8,1051.2,1058.5,1065.8],
                                 [971.8,979.1,986.5,993.8,1001.1,1008.5,1015.8,1023.1,1030.5,1037.8,1045.1,1052.5,1059.8],
                                 [965.3,972.6,980,987.3,994.7,1002,1009.4,1016.8,1024.1,1031.5,1038.8,1046.2,1053.5],
                                 [958.4,965.7,973.1,980.5,987.9,995.2,1002.6,1010,1017.4,1024.8,1032.2,1039.6,1047],
                                 [950.9,958.3,958.8,973.2,980.6,988.1,995.5,1003,1010.4,1017.8,1025.3,1032.7,1040.2],
                                 [943.1,950.6,958.1,965.6,973.1,980.6,988.1,995.6,1003.1,1010.6,1018.1,1025.6,1033.1]],
                 
                 # Seawater specific heat capacity look-up table
                 SW_cp_temp  = [0,10,20,30,40,50,60,70,80,90,100,110,120],
                 SW_cp_salinity = [0,0.01,0.02,0.03,0.04,0.05,0.06,0.07,0.08,0.09,0.1,0.11,0.12],
                 SW_cp_cp =     [[4.2068,4.1421,4.0799,4.0201,3.9627,3.9078,3.9078,3.8052,3.7576,3.7124,3.6697,3.6293,3.5915],
                                 [4.1967,4.1367,4.0788,4.0228,3.9689,3.9169,3.9169,3.8192,3.7733,3.7295,3.6877,3.6479,3.6101],
                                 [4.1891,4.1326,4.0782,4.0253,3.9741,3.9245,3.9245,3.8304,3.7859,3.743,3.7018,3.6623,3.6245],
                                 [4.1839,4.1305,4.0785,4.0278,3.9786,3.9308,3.9308,3.8394,3.7958,3.7536,3.7127,3.6733,3.6353],
                                 [4.181,4.1297,4.0796,4.0307,3.9829,3.9364,3.9364,3.6467,3.8037,3.7618,3.7211,3.6816,3.6432],
                                 [4.1806,4.1308,4.0819,4.0341,3.9873,3.9415,3.9415,3.8529,3.8101,3.7683,3.7275,3.6878,3.649],
                                 [4.1827,4.1337,4.0855,4.0383,3.992,3.9465,3.9465,3.8583,3.8155,3.7737,3.7327,3.6926,3.6534],
                                 [4.1871,4.1365,4.0906,4.0436,3.9973,3.9519,3.9519,3.8636,3.8206,3.7785,3.7372,3.6967,3.657],
                                 [4.194,4.1453,4.0973,4.0501,4.0037,3.9581,3.9581,3.8692,3.8259,3.7835,3.7417,3.7008,3.6607],
                                 [4.2034,4.1542,4.1059,4.0583,4.0115,3.9654,3.9654,3.8757,3.832,3.7891,3.7469,3.7056,3.665],
                                 [4.2152,4.1654,4.1164,4.0682,4.0209,3.9743,3.9743,3.8836,3.8394,3.796,3.7535,3.7117,3.6708],
                                 [4.2294,4.1788,4.1291,4.0802,4.0322,3.9851,3.9851,3.8933,3.8486,3.8049,3.7619,3.7199,3.6786],
                                 [4.2461,4.1947,4.1442,4.0946,4.0459,3.9982,3.9982,3.9054,3.8603,3.8162,3.773,3.7307,3.6894]],
                  
                 # Seawater thermal conductivity look-up table
                 SW_cond_temp  = [0,10,20,30,40,50,60,70,80,90,100,110,120],
                 SW_cond_salinity = [0,0.01,0.02,0.03,0.04,0.05,0.06,0.07,0.08,0.09,0.1,0.11,0.12],
                 SW_cond_cond = [[0.572,0.571,0.57,0.57,0.569,0.569,0.568,0.568,0.567,0.566,0.566,0.565,0.565],
                                 [0.588,0.588,0.587,0.587,0.586,0.585,0.585,0.584,0.584,0.583,0.583,0.582,0.582],
                                 [0.604,0.603,0.602,0.602,0.601,0.601,0.6,0.6,0.599,0.599,0.598,0.598,0.597],
                                 [0.617,0.617,0.616,0.616,0.615,0.615,0.614,0.614,0.613,0.613,0.612,0.612,0.611],
                                 [0.63,0.629,0.629,0.628,0.628,0.627,0.627,0.626,0.626,0.625,0.625,0.624,0.624],
                                 [0.641,0.64,0.64,0.639,0.639,0.638,0.638,0.637,0.637,0.636,0.636,0.635,0.635],
                                 [0.65,0.65,0.649,0.649,0.648,0.648,0.647,0.647,0.647,0.646,0.646,0.645,0.645],
                                 [0.658,0.658,0.658,0.657,0.657,0.656,0.656,0.655,0.655,0.655,0.654,0.654,0.653],
                                 [0.665,0.665,0.665,0.664,0.664,0.663,0.663,0.663,0.662,0.662,0.661,0.661,0.661],
                                 [0.671,0.671,0.67,0.67,0.67,0.669,0.669,0.669,0.668,0.668,0.667,0.667,0.667],
                                 [0.676,0.675,0.675,0.675,0.674,0.674,0.674,0.673,0.673,0.673,0.672,0.672,0.672],
                                 [0.679,0.679,0.679,0.678,0.678,0.678,0.677,0.677,0.677,0.676,0.676,0.676,0.675],
                                 [0.682,0.681,0.681,0.681,0.68,0.68,0.68,0.679,0.679,0.679,0.679,0.678,0.678]],
                      
                 # Seawater dynamic viscosity look-up table
                 SW_v_temp  = [0,10,20,30,40,50,60,70,80,90,100,110,120],
                 SW_v_salinity = [0,0.01,0.02,0.03,0.04,0.05,0.06,0.07,0.08,0.09,0.1,0.11,0.12],
                 SW_v_v = [[1.791,1.82,1.852,1.887,1.925,1.965,2.008,2.055,2.104,2.156,2.21,2.268,2.328],
                                 [1.306,1.33,1.355,1.382,1.412,1.443,1.476,1.511,1.548,1.586,1.627,1.669,1.714],
                                 [1.002,1.021,1.043,1.065,1.089,1.114,1.14,1.168,1.197,1.227,1.259,1.292,1.326],
                                 [0.797,0.814,0.632,0.851,0.871,0.891,0.913,0.936,0.96,0.984,1.01,1.037,1.064],
                                 [0.653,0.667,0.683,0.699,0.716,0.734,0.752,0.771,0.791,0.812,0.833,0.855,0.878],
                                 [0.547,0.56,0.573,0.587,0.602,0.617,0.633,0.649,0.666,0.684,0.702,0.721,0.74],
                                 [0.466,0.478,0.49,0.502,0.515,0.528,0.542,0.556,0.571,0.586,0.602,0.618,0.635],
                                 [0.404,0.414,0.425,0.436,0.447,0.459,0.471,0.484,0.497,0.51,0.524,0.538,0.553],
                                 [0.354,0.364,0.373,0.383,0.393,0.404,0.415,0.426,0.437,0.449,0.462,0.474,0.487],
                                 [0.315,0.323,0.331,0.34,0.349,0.359,0.369,0.379,0.389,0.4,0.411,0.422,0.434],
                                 [0.282,0.289,0.297,0.305,0.313,0.322,0.331,0.34,0.35,0.359,0.369,0.38,0.39],
                                 [0.255,0.262,0.269,0.276,0.283,0.291,0.299,0.308,0.316,0.325,0.334,0.344,0.354],
                                 [0.232,0.238,0.245,0.251,0.258,0.265,0.273,0.28,0.288,0.297,0.305,0.314,0.323]],

                  # Draw solution dynamic viscosity look-up table
                  DS_viscosity_temp  = [15,25,35,45,55,65,75,85,90.01],
                  DS_viscosity_c     = [0,0.5,0.6,0.8,1],
                  DS_viscosity_v     = [[1.14,80,130,200,280],
                                        [0.89,34.618,66.407,120.635,158.234],
                                        [0.719,22.451,41.051,66.43,85.239],
                                        [0.596,15.438,27.191,36.755,31.754],
                                        [0.504,11.515,19.309,14.362,20.105],
                                        [0.434,21.465,16.537,15.949,21.738],
                                        [0.378,20.084,19.956,12.149,16.25],
                                        [0.334,18.186,18.001,9.345,13.108],
                                        [0.314,10,10,10,10]],
                                        
                  # Water Density, Cp and dynamic viscosity look-up table
                  W_density = [[0,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100], [999.8,1000,999.8,999.2,998.3,997.1,995.7,994.1,992.3,990.2,988,986,983,980,978,975,972,968,965,962,958]],
                  W_cp = [[0,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100], [4.21,4.204,4.193,4.1855,4.183,4.181,4.179,4.178,4.179,4.181,4.182,4.183,4.185,4.188,4.191,4.194,4.198,4.203,4.208,4.213,4.219]],
                  W_viscosity = [[0,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100], [1.78,1.52,1.31,1.14,1,0.89,0.798,0.719,0.653,0.596,0.547,0.504,0.467,0.434,0.404,0.378,0.355,0.334,0.314,0.297,0.287]],
                  W_cond = [[1.85,6.85,11.85,16.85,21.85,26.85,31.85,36.85,41.85,46.85,51.85,56.85,64.85,66.85,71.85,76.85,81.85,86.85,91.85,96.85], [0.5606,0.5715,0.5818,0.5917,0.6009,0.6096,0.6176,0.6252,0.6322,0.6387,0.6445,0.6499,0.6546,0.6588,0.6624,0.6655,0.668,0.67,0.6714,0.6723]],

                ):
        # Assign instance variables
        self.Salt_rej = Salt_rej
        self.T_sw = T_sw
        self.Mprod  = Mprod
        self.NF_rcr = NF_rcr
        self.RO_r   = RO_r
        self.A      = A
        self.p_margin = p_margin
        self.p_weak = p_weak
        self.DS_p   = DS_c_p[0]  # Osmotic pressure of draw solution (psi)
        self.DS_c   = DS_c_p[1]  # Polymer concentration in draw solution (wt%)
        self.r      = r
        self.salinity = salinity
        self.hm     = hm
        self.DS_c2  = DS_density[0] # Draw solution concentration list (wt%)
        self.DS_d   = DS_density[1] # Draw solution density list (kg/m3)
        self.DS_c3  = DS_heatcap[0] 
        self.DS_cp  = DS_heatcap[1] 
        self.DS_c4  = DS_conductivity[0]
        self.DS_cond= DS_conductivity[1]
        self.SW_d_temp = SW_d_temp
        self.SW_d_salinity = SW_d_salinity
        self.SW_d_density = SW_d_density
        self.SW_cp_temp = SW_cp_temp
        self.SW_cp_salinity = SW_cp_salinity
        self.SW_cp_cp = SW_cp_cp
        self.SW_cond_temp = SW_cond_temp
        self.SW_cond_salinity = SW_cond_salinity
        self.SW_cond_cond = SW_cond_cond
        self.SW_v_temp = SW_v_temp
        self.SW_v_salinity = SW_v_salinity
        self.SW_v_v = SW_v_v
        self.DS_viscosity_temp = DS_viscosity_temp
        self.DS_viscosity_c = DS_viscosity_c
        self.DS_viscosity_v = DS_viscosity_v
        self.T_cout_2B = T_cout_2B
        self.T_memb = T_memb
        self.T_wd   = T_wd
        self.T_prod = T_prod
        self.f_cin_1A = f_cin_1A
        self.T_cout_1A = T_cout_1A
        self.T_hin_1A = T_hin_1A
        self.T_hout_1A = T_hout_1A
        self.T_cout_1B = T_cout_1B
        self.T_hin_1B = T_hin_1B
        self.T_hin_1C = T_hin_1C
        self.T_hout_1C = T_hout_1C
        self.f_hin_1C = f_hin_1C
        self.T_cout_1C = T_cout_1C
        self.T_hin_2A = T_hin_2A
        self.T_hout_2A = T_hout_2A
        self.T_cout_2A = T_cout_2A
        self.T_hin_2B = T_hin_2B
        self.f_hin_2C = f_hin_2C
        self.T_hout_2C = T_hout_2C
        self.T_cout_2C = T_cout_2C
        self.T_hout_6 = T_hout_6
        self.f_sw_sup = f_sw_sup
        self.T_hout_4 = T_hout_4
        self.T_cout_4 = T_cout_4
        self.T_cout_5 = T_cout_5
        self.W_density_t1 = W_density[0]
        self.W_density_d  = W_density[1]
        self.W_cp_t2 = W_cp[0]
        self.W_cp_cp = W_cp[1]
        self.W_viscosity_t3 = W_viscosity[0]
        self.W_viscosity_v = W_viscosity[1]
        self.W_cond_t4 = W_cond[0]
        self.W_cond_cond = W_cond[1]
        
        self.SW_d_points = []
        self.SW_d_values = []
        for temp in self.SW_d_temp:
            for s in self.SW_d_salinity:
                self.SW_d_points.append([temp,s])
        
        for i in range(len(self.SW_d_temp)):
            for j in range(len(self.SW_d_salinity)):
                self.SW_d_values.append(self.SW_d_density[i][j])
                
        self.SW_cp_points = []
        self.SW_cp_values = []
        for temp in self.SW_cp_temp:
            for s in self.SW_cp_salinity:
                self.SW_cp_points.append([temp,s])
        
        for i in range(len(self.SW_cp_temp)):
            for j in range(len(self.SW_cp_salinity)):
                self.SW_cp_values.append(self.SW_cp_cp[i][j])
                
                
        self.DS_viscosity_points = []
        self.DS_viscosity_values = []
        for temp in self.DS_viscosity_temp:
            for s in self.DS_viscosity_c:
                self.DS_viscosity_points.append([temp,s])
        
        for i in range(len(self.DS_viscosity_temp)):
            for j in range(len(self.DS_viscosity_c)):
                self.DS_viscosity_values.append(self.DS_viscosity_v[i][j])
                
        self.SW_cond_points=[]
        self.SW_cond_values=[]
        for temp in self.SW_cond_temp:
            for s in self.SW_cond_salinity:
                self.SW_cond_points.append([temp,s])
                
        for i in range(len(self.SW_cond_temp)):
            for j in range(len(self.SW_cond_salinity)):
                self.SW_cond_values.append(self.SW_cond_cond[i][j])
                
        self.SW_v_points=[]
        self.SW_v_values=[]  
        for temp in self.SW_v_temp:
            for s in self.SW_v_salinity:
                self.SW_v_points.append([temp,s])
        
        for i in range(len(self.SW_v_temp)):
            for j in range(len(self.SW_v_salinity)):
                self.SW_v_values.append(self.SW_v_v[i][j])
                
    # 1-dimension interpolation (linear method)
    def OneDInterp(self, v, z):
        # To add: Raise exception for disordered array or z that is out of range
        if v == 'Draw concentration':
            v1 = self.DS_p
            v2 = self.DS_c
        elif v == 'Draw density':
            v1 = self.DS_c2
            v2 = self.DS_d 
        elif v == 'Draw cp':
            v1 = self.DS_c3
            v2 = self.DS_cp
        elif v == 'Draw conductivity':
            v1 = self.DS_c4
            v2 = self.DS_cond
        elif v == 'Water density':
            v1 = self.W_density_t1
            v2 = self.W_density_d 
        elif v == 'Water cp':
            v1 = self.W_cp_t2
            v2 = self.W_cp_cp
        elif v == 'Water viscosity':
            v1 = self.W_viscosity_t3
            v2 = self.W_viscosity_v   
        elif v == 'Water conductivity':
            v1 = self.W_cond_t4
            v2 = self.W_cond_cond 
            
            
        f = interp1d(v1, v2)
        return f(z)[()]
    
    # 2-dimension interpolation (linear method)
    def TwoDInterp(self, v, z1, z2):
        if v == 'Seawater density':
            points = self.SW_d_points
            values = self.SW_d_values
        elif v == 'Seawater Cp':
            points = self.SW_cp_points
            values = self.SW_cp_values
        elif v == 'Seawater conductivity':
            points = self.SW_cond_points
            values = self.SW_cond_values
        elif v == 'Seawater viscosity':
            points = self.SW_v_points
            values = self.SW_v_values
        elif v == 'Draw viscosity':
            points = self.DS_viscosity_points
            values = self.DS_viscosity_values
        
        
        return griddata(points, values, (z1, z2), method='linear')[()]
        
    
    def flow_rate_calculations(self):
        
        self.RO_rf  = self.Mprod / (1/self.RO_r -1) # RO reject flow rate (m3/day)
        self.NF_pf  = self.Mprod + self.RO_rf       # Nanofilter permeate flow rate
        self.NF_rf  = self.NF_pf / (1/self.NF_rcr -1)  #Nanofilter rentate flow rate (m3/day)
        self.S      = self.Mprod + self.NF_rf + self.RO_rf  # Supernatant flow rate (m3/day)
        self.NF_rcc = self.S * 0.01 / self.NF_rf    # Nanofilter retentate polymer concentration       
        self.B      = self.OneDInterp('Draw concentration', self.p_weak) /100 # Percentage of pure draw in wak draw after membrane (%)
        self.SD_x   = self.B * self.NF_pf *(1-self.A) / (self.A - self.B) # Water in strong draw (m3/day)
        self.SD_y   = self.A * self.SD_x / (1-self.A)  # Pure draw in strong/weak draw (m3/day)
        self.SD     = self.SD_x + self.SD_y  #Strong draw (m3/day)
        self.WD_M_x = self.NF_pf + self.SD_x  # Water in weak draw after membrane (m3/day)
        self.WD_M   = self.WD_M_x + self.SD_y  # Weak draw after membrane (m3/day)
        self.WD_HX_x= self.WD_M_x + self.NF_rf * (1-self.NF_rcc)  # Water in weak draw through HXs (m3/day)
        self.WD_HX_y= self.SD_y + self.NF_rf * self.NF_rcc  # Pure draw in wak draw through HXs (m3/day)
        self.WD_HX  = self.WD_HX_x + self.WD_HX_y # Weak draw through HXs
        self.BHx    = self.WD_HX_y / self.WD_HX   # Percentage of pure draw in wak draw through HXs
        self.e      = self.NF_pf * (1- self.r)/self.r  # Water not recovered from seawater
        self.s      = (self.NF_pf + self.e) * self.salinity / (1-self.salinity) # Salt content in seawater
        self.sw     = self.NF_pf + self.e + self.s  # Seawater 
        self.e_s    = self.e + self.s  # Brine
        self.salinity_b = self.s / self.e_s # Salinity of brine (%)
 
       
    def membrane_heat_calculations(self):
        # To weak draw solution
        h_wd  = 0  # Heat transfered (MJ per m3/day)
        self.density_wd = self.OneDInterp('Draw density', self.B*100) # kg/m3
        f_wd = self.WD_M #m3/day
        self.cp_wd = self.OneDInterp('Draw cp', self.B*100)  # kJ/kg-deg C
        # To outgoing brine
        h_b   = self.hm - h_wd # Heat transfered (MJ per m3/day)
        f_b = self.e_s # m3/day
        self.density_b = self.TwoDInterp('Seawater density', self.T_memb, self.salinity_b)  # kg/m3
        self.cp_b = self.TwoDInterp('Seawater Cp', self.T_memb, self.salinity_b)  # kJ/kg-deg C
        
        # Delta T in weak draw and brine
        dT_wd  = h_wd * 1000 / self.density_wd / f_wd / self.cp_wd
        dT_b   = h_b  * 1000 / self.density_b  / f_b  / self.cp_b

        # Modify the heat to weak draw to have the same Delta T in weak draw and brine
        i = 1
        while (abs(dT_wd - dT_b) > 0.0001):
            if dT_wd < dT_b:
                h_wd += self.hm / 2**i
            else:
                h_wd -= self.hm/ 2**i
            h_b  = self.hm - h_wd
            dT_wd  = h_wd * 1000 / self.density_wd / f_wd / self.cp_wd
            dT_b   = h_b  * 1000 / self.density_b  / f_b  / self.cp_b
            i += 1
        
        self.h_wd = h_wd
        self.h_b = h_b
        self.P_wd = h_wd *1000/24/3600
        self.P_b  = h_b *1000/24/3600
        self.dT  = dT_b
 
        # Brine
        self.T_b_in = self.T_memb + self.dT   # Temperature of brine entering HX
        self.p_b    = 0.93*2 * self.salinity_b *10*100/58.5*0.08314472*14.50377*(273+ self.T_b_in)  # Brine osmotic pressure (psi)
 
        # Nanofilter
        self.NF_cp = self.OneDInterp('Draw cp', self.NF_rcc*100) # Specific heat of nanofilter retentate
        self.NF_d  = self.OneDInterp('Draw density', self.NF_rcc*100) # kg/m3
        self.Temp_wd = (self.density_wd * self.WD_M * self.cp_wd * self.T_wd + self.NF_d * self.NF_rf * self.NF_cp * self.T_prod) / (self.density_wd * self.WD_M * self.cp_wd + self.NF_d * self.NF_rf *self.NF_cp)

        # Transfer of heat of separation in heat exchanger at cloud point
        self.d_HX = self.OneDInterp('Draw density', self.BHx*100)
        self.f_HX = self.WD_HX  # Flow rate
        self.cp_HX = self.OneDInterp('Draw cp', self.BHx*100)
        self.dT_HX = self.hm * 1000 / self.d_HX / self.f_HX / self.cp_HX # Delta T
        self.p_prod = self.hm / 3.6 / 24 # Power per m3 product water (kW)
        self.p_wd  = self.p_prod / self.f_HX # Power per m3 weak draw (kW)
        

    def heat_exchanger_calculations(self, Name, Type_h, Type_c, rf_h, rf_c, dP_h, OP_h, dP_c, OP_c, T_hin, T_hout, T_cin, T_cout, c_hot, c_cold):
        # Hot side
        if Type_h == "Draw":
            d_h    = self.OneDInterp('Draw density', c_hot*100) 
            cp_h   = self.OneDInterp('Draw cp', c_hot*100)
            cond_h = self.OneDInterp('Draw conductivity', c_hot*100)
            v_hin  = self.TwoDInterp('Draw viscosity', T_hin, c_hot )
            v_hout = self.TwoDInterp('Draw viscosity', T_hout, c_hot )
            f_h    = self.Mprod * rf_h
        elif Type_h == "Water":
            d_h    = self.OneDInterp('Water density', (T_hin+T_hout)/2) 
            cp_h   = self.OneDInterp('Water cp', (T_hin+T_hout)/2)
            cond_h = self.OneDInterp('Water conductivity', (T_hin+T_hout)/2)
            v_hin  = self.OneDInterp('Water viscosity', T_hin )
            v_hout = self.OneDInterp('Water viscosity', T_hout )
            f_h    = self.Mprod * rf_h
        elif Type_h == "SW":
            d_h    = self.TwoDInterp('Seawater density', (T_hin+T_hout)/2, c_hot) 
            cp_h   = self.TwoDInterp('Seawater Cp', (T_hin+T_hout)/2, c_hot)
            cond_h = self.TwoDInterp('Seawater conductivity', (T_hin+T_hout)/2, c_hot)
            v_hin  = self.TwoDInterp('Seawater viscosity', T_hin, c_hot )
            v_hout = self.TwoDInterp('Seawater viscosity', T_hout, c_hot )
            f_h    = self.Mprod * rf_h
        
        # Cold side
        if Type_c == "Draw":
            d_c    = self.OneDInterp('Draw density', c_cold *100) 
            cp_c   = self.OneDInterp('Draw cp', c_cold*100)
            cond_c = self.OneDInterp('Draw conductivity', c_cold*100)
            v_cin  = self.TwoDInterp('Draw viscosity', T_cin, c_cold )
            v_cout = self.TwoDInterp('Draw viscosity', T_cout, c_cold )
            f_c    = self.Mprod * rf_c
        elif Type_c == "Water":
            d_c    = self.OneDInterp('Water density', (T_cin+T_cout)/2) 
            cp_c   = self.OneDInterp('Water cp', (T_cin+T_cout)/2)
            cond_c = self.OneDInterp('Water conductivity', (T_cin+T_cout)/2)
            v_cin  = self.OneDInterp('Water viscosity', T_hin )
            v_cout = self.OneDInterp('Water viscosity', T_hout)
            f_c    = self.Mprod * rf_c
        elif Type_c == "SW":
            d_c    = self.TwoDInterp('Seawater density', (T_cin+T_cout)/2, c_cold) 
            cp_c   = self.TwoDInterp('Seawater Cp', (T_cin+T_cout)/2, c_cold)
            cond_c = self.TwoDInterp('Seawater conductivity', (T_cin+T_cout)/2, c_cold)
            v_cin  = self.TwoDInterp('Seawater viscosity', T_cin, c_cold )
            v_cout = self.TwoDInterp('Seawater viscosity', T_cout, c_cold )
            f_c    = self.Mprod * rf_c
        
        # Approach temperature
        if abs((T_hin - T_cout) - (T_hout - T_cin)) < 0.1:
            T_app = T_hin - T_cout
        else:
            T_app = ((T_hout - T_cin)-(T_hin - T_cout)) / np.log(abs((T_hout - T_cin)/(T_hin - T_cout)))
        # Heat load
        heat_h = f_h / 3600 / 24 * d_h * cp_h * (T_hin - T_hout)  # kW
        heat_c = f_c / 3600 / 24 * d_c * cp_c * (T_cin - T_cout)  # kW        
        
        values = {'HX': Name, 'Approach Temp': T_app, 'Hot side flow rate (m3/day)': f_h, 'Cold side flow rate (m3/day)': f_c, 'Hot side heat load(kW)': heat_h, 'Cold side heat load(kW)': heat_c }
        return values
    
    def system_calculations(self):
        self.HX1A = self.heat_exchanger_calculations('HX_1A', 'Draw', 'Draw', self.SD, self.f_cin_1A, 3, 6, 3, 22, self.T_hin_1A, self.T_hout_1A, self.Temp_wd, self.T_cout_1A, self.A, self.BHx )
        self.HX1B = self.heat_exchanger_calculations('HX_1B', 'Draw', 'Draw', self.SD, self.f_cin_1A, 4, 10,4, 19, self.T_hin_1B, self.T_hout_1A, self.Temp_wd, self.T_cout_1B, self.A, self.BHx )
        self.HX1C = self.heat_exchanger_calculations('HX_1C', 'Water', 'Draw', self.f_hin_1C, self.f_cin_1A, 5, 30,5, 15, self.T_hin_1C, self.T_hout_1C, self.T_cout_1B, self.T_cout_1C, None, self.BHx )
        self.HX2A = self.heat_exchanger_calculations('HX_2A', 'Water', 'Draw', self.S, self.WD_HX-self.f_cin_1A, 1, 9, 3, 22, self.T_hin_2A, self.T_hout_2A, self.Temp_wd, self.T_cout_2A, None, self.BHx )
        self.HX2B = self.heat_exchanger_calculations('HX_2B', 'Water', 'Draw', self.S, self.WD_HX-self.f_cin_1A, 1, 10, 4, 19, self.T_hin_2B, self.T_hin_2A, self.T_cout_2A, self.T_cout_2B, None, self.BHx )
        self.HX2C = self.heat_exchanger_calculations('HX_2C', 'Water', 'Draw', self.f_hin_2C, self.WD_HX-self.f_cin_1A, 5, 30, 5, 19, self.T_hin_1C, self.T_hout_2C, self.T_cout_2B, self.T_cout_2C, None, self.BHx )
        self.HX6  = self.heat_exchanger_calculations('HX_6' , 'SW'   , 'Draw', self.e_s, self.WD_M, 1, 3, 1, 4, self.T_memb + self.dT, self.T_hout_6, self.T_memb + self.dT, self.T_wd, self.salinity_b, self.B  )
        self.HX4  = self.heat_exchanger_calculations('HX_4' , 'Draw' , 'SW', self.SD, self.f_sw_sup, 4, 3, 1, 3, self.T_hin_1A, self.T_hout_4, self.T_sw, self.T_cout_4, self.A, self.salinity)
        self.HX5  = self.heat_exchanger_calculations('HX_5' , 'Water' , 'SW', self.SD, self.sw, 1, 8, 1, 4, self.T_hout_2A, self.T_prod, self.T_sw, self.T_cout_5, None, self.salinity)
                                                           
#%%
case = FO_Trevi(Mprod = 1,salinity=0.035)
case.flow_rate_calculations()  
case.membrane_heat_calculations()      
case.system_calculations()
