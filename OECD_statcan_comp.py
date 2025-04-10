import pandas as pd
import numpy as np
import os
import time
import matplotlib.pyplot as plt
from func_data_upload2 import data_upload
from func_plot_L import plot_matrix_columns
from func_clc_L import clc_L



def safe_divide(II, output):
    # Check if there are NaNs in either II or output
    if II.isna().any().any():
        raise ValueError("Matrix II contains NaN values.")
    if output.isna().any():
        raise ValueError("Output contains NaN values.")
    
    # Replace zeros in outputc with NaN to avoid division by zero
    output_safe = output.replace(0, np.nan)
    
    # Divide II by output, handling NaN values (from division by zero)
    T = II.divide(output_safe, axis=1)
    
    # Replace any NaN values (from division by zero) with zero
    T = T.fillna(0)
    
    return T

def clc_output_multipliers(year):
    # Module 1: Get IO=II, X, GDP, from OECD, wages, compensation for employees and employment from CANSTAT
    # later move this to a function that receives country and year and uploads the results

    PPP, OECD, simple_II_labels, statcan_sectors_data, sector_description, T97_values =  data_upload(year)
    # statcan_sector_description is the explanation in words of the codes. 
    # If I want to look something up in statcan_rough I can use read_statcan
    # in the files I downloaded from OECD there's no description of the sectors in words.
    # I should change statcan_sector_description into a dictionary

    II = OECD.loc[simple_II_labels, simple_II_labels]
    household_expenditure = OECD.loc[simple_II_labels, 'HFCE']
    final_demand_columns = ['HFCE',	'NPISH',	'GGFC',	'GFCF',	'INVNT',	'DPABR',	'CONS_NONRES',	'EXPO',	'IMPO']
    #other_final_demand = OECD.loc[simple_II_labels, final_demand_columns[1:]] #exluding HFCE - household expenditure
    #total       = OECD.loc[simple_II_labels, 'TOTAL'] #equals to output, this is x
    #GDP         = OECD.loc['VALU', simple_II_labels]
    output      = OECD.loc['OUTPUT', simple_II_labels]
    #I don't need to worry bout household_expenditure of GDP or output - they are both 0
    # but output of GDP is given and should be marked independently

    #final demand and value added are not the same at all

    # Modul 2: calculate L and multipliers
    T = safe_divide(II, output)
    Ldf, L_minus_I = clc_L(T)

    IIc = II.copy()
    IIc["HFCE"] = household_expenditure # added a column for closed model
    IIc.loc['employees_compensation'] = statcan_sectors_data['employees_compensation'] #If I wanted a column I would have written IIC['employees_compensation']
    # temporary fix, perhaps I should put household_expenditure of employees_compensation to 0
    IIc.loc['employees_compensation', 'HFCE'] = T97_values.loc[T97_values['Transaction'] == 'Compensation of employees', 'OBS_VALUE_USD'].values[0]
    #T is manifestly not HFCE because the numbers are different
    outputc = output.copy()
    outputc['HFCE'] = OECD.loc['OUTPUT', 'HFCE']
    Tc = safe_divide(IIc, outputc)
    Lcdf, Lc_minus_I = clc_L(Tc)

    return statcan_sectors_data, OECD, simple_II_labels, final_demand_columns, II, IIc, output, outputc, T, Tc, Ldf, L_minus_I, Lcdf, Lc_minus_I

def plot_six_panels(data_dict, sectors, title_prefix, y_label):
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()

    for i, sector in enumerate(sectors):
        ax = axes[i]
        for j, year in enumerate(yearvec):
            df = data_dict[year]
            if sector in df.columns:
                ax.plot(df.index, df[sector], label=year, marker='o')
        ax.set_title(f'{title_prefix} - Sector {sector}')
        ax.set_xlabel('Index')
        ax.set_ylabel(y_label)
        ax.legend()
        ax.grid(True)

    plt.tight_layout()
    plt.show()

###############################################               main               #################################
start_time = time.time()
print("working directory of OECD_statcan_comp.py is: ",os.getcwd())  # Print the current working directory


yearvec = ['2015', '2016', '2017', '2018', '2019', '2020']
OECD_sectors_ICT = ['C26', 'G', 'J58T60', 'J61', 'J62_63', 'M']
#these three I plot to see differences over years
Tc_dict = {}
Lc_dict = {}
OECD_IIc_dict = {}
#this I plot to see comparison with OECD
OECD_outputc_dict = {}
# Collect Tc for each year
for year in yearvec:
    statcan_sectors_data, OECD, simple_II_labels, _, _, IIc, _, outputc, _, Tc, _, _, Lcdf, _ = clc_output_multipliers(year)
#matrices
    Tc_dict[year] = Tc
    Lc_dict[year] = Lcdf 
    OECD_IIc_dict[year] = IIc
#vectors
    OECD_GDP = OECD.loc['VALU', simple_II_labels]
    OECD_II = OECD.loc[simple_II_labels, simple_II_labels].sum(axis=1)
    OECD_outputc_dict[year] = outputc
#statcan data
    statcan_E = statcan_sectors_data['employees_compensation']
    statcan_GDP = statcan_sectors_data['GDP']
    statcan_II = statcan_sectors_data['intermediate_consumption'] #this is a vector and not a matrix
    statcan_output = statcan_sectors_data['output']
    


#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                 plotting            $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


#plot_six_panels(Tc_dict, OECD_sectors_ICT, title_prefix='Tc', y_label='Tc Value')
#plot_six_panels(Lc_dict, OECD_sectors_ICT, title_prefix='Lc', y_label='Lcdf Value')
#plot_six_panels(OECD_IIc_dict, OECD_sectors_ICT, title_prefix='IIc', y_label='IIc Value')




#ICT sectors information
ICT_sectors = ['ICT - Manufacturing', 'ICT - Wholesaling', 'ICT - Software and computer services', 'ICT - Communications services',
               'ICT - Software and computer services',	'ICT - Software and computer services']
# These correspond to the numbers 17	26	33	34	35	38
OECD_sectors_ICT = ['C26',	'G',	'J58T60',	'J61',	'J62_63',	'M']
ICT_sectors_dict = {'ICT - Manufacturing': 'C26',
                    'ICT - Wholesaling': 'G',
                    'ICT - Software and computer services': ['J58T60', 'J62_63', 'M'],  
                    'ICT - Communications services': 'J61'}
# Build sector code to name mapping
code_to_name = {}
for name, codes in ICT_sectors_dict.items():
    if isinstance(codes, list):
        for code in codes:
            code_to_name[code] = name
    else:
        code_to_name[codes] = name



##Simple output multipliers: L
#plot_matrix_columns(
#    matrix=Ldf,
#    sectors=OECD_sectors_ICT,
#    sector_code_to_name=code_to_name,
#    title=f'Leontief Matrix Column Profiles - output direct+indirect impact, year {year}'
#)

























#plot Lc over the years


#plot ratio of GDP_OECD/GDP_statcan, output_OECD/output_statcan, II_OECD/II_statcan
#see if there is repetition of pattern over years and over type of data



'''

output_year2 = OECD_year2.loc['OUTPUT', simple_II_labels]
outputc_year2 = output_year2.copy()
outputc_year2.loc['HFCE'] = OECD_year2.loc['OUTPUT', 'HFCE']
fdf_year2 = OECD_year2.loc[simple_II_labels, final_demand_columns].sum(axis=1)
fcdf_year2 = OECD_year2.loc[simple_II_labels,final_demand_columns[1:]].sum(axis=1)
fcdf_year2.loc['employees_compensation'] = 0


predicted_output_year2_np  = np.round(Ldf_year1.to_numpy() @ fdf_year2.values.reshape(-1, 1), 1)
predicted_outputc_year2_np = np.round(Lcdf_year1.to_numpy() @ fcdf_year2.values.reshape(-1,1), 1)

predicted_output_year2 = pd.DataFrame(predicted_output_year2_np, index=Ldf_year1.index, columns=['Predicted_Output'])
predicted_outputc_year2 = pd.DataFrame(predicted_outputc_year2_np, index=Lcdf_year1.index, columns=['Predicted_Output'])
'''

