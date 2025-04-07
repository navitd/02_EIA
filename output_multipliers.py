import pandas as pd
import numpy as np
import os
import time
from func_data_upload import data_upload
from func_plot_L import plot_matrix_columns
from func_clc_L import clc_L

def data_exploration_flags(II,household_expenditure,other_final_demand,output,output_of_final_demand,OECD_rough):
    print( pd.DataFrame({
        'II plus f total': II.sum(axis=1) + household_expenditure + other_final_demand.sum(axis=1) ,
        'Output': output
    }) )
    print('expected to be zero:')
    print(pd.DataFrame({
        'output_of_final_demand': output_of_final_demand
    }))

    print(f'sum of output:{output.sum()}, bottom right corner of the matrix:{OECD_rough.loc['OUTPUT', 'TOTAL']}, difference expected to be zero:{output.sum()-OECD_rough.loc['OUTPUT', 'TOTAL']}')

def safe_divide(value, denom):
    # Division with handling zero values
    return value / denom if denom != 0 else "total output is zero"



###############################################               main               #########################
start_time = time.time()
print("working directory of income_multipliers.py is: ",os.getcwd())  # Print the current working directory


# Module 1: Get IO=II, X, GDP, from OECD, wages, compensation for employees and employment from CANSTAT
# later move this to a function that receives country and year and uploads the results
year = '2019'
PPP, OECD, simple_II_labels, mapping_dict, statcan =  data_upload(year)

II = OECD.loc[simple_II_labels, simple_II_labels]
household_expenditure = OECD.loc[simple_II_labels, 'HFCE']
final_demand_columns = ['HFCE',	'NPISH',	'GGFC',	'GFCF',	'INVNT',	'DPABR',	'CONS_NONRES',	'EXPO',	'IMPO']
other_final_demand = OECD.loc[simple_II_labels, final_demand_columns[1:]] #exluding HFCE - household expenditure
total       = OECD.loc[simple_II_labels, 'TOTAL'] #equals to output, this is x
GDP         = OECD.loc['VALU', simple_II_labels]
output      = OECD.loc['OUTPUT', simple_II_labels]
#I don't need to worry bout household_expenditure of GDP or output - they are both 0
# but output of GDP is given and should be marked independently

#single values in OECD:
GDP_of_household_expenditure = OECD.loc['VALU', 'HFCE']
GDP_of_total_column = OECD.loc['VALU', 'TOTAL'] # total is the output, should be equal to f_row_sums.sum(axis=0)
GDP_of_final_demand = OECD.loc['VALU', final_demand_columns]        #this could be added to the rows from the right or to the columns form the bottom
output_of_final_demand = OECD.loc['OUTPUT', final_demand_columns]   #probably will not be needed

# from looking at the numbers:
# total = output
# II_row_sums + f_row_sums = total = output
# household_expenditure is the column added to II to get the closed model
# when uploading data for the first time run:
# data_exploration_flags(II,household_expenditure,other_final_demand,output,output_of_final_demand,OECD_rough)

#final demand and value added are not the same at all




# Modul 2: calculate L and multipliers
T = II.apply(lambda col: col.map(lambda val: safe_divide(val, output[col.name])))
Ldf, L_minus_I = clc_L(T)



IIc = II.copy()
IIc["HFCE"] = household_expenditure # added a column for closed model
# I need to add a row for closed model - compensation of employees from statcan. I need to get it and convert to USD
IIc
outputc = output.copy()
outputc['HFCE'] = OECD.loc['OUTPUT', 'HFCE']
Tc = IIc.apply(lambda col: col.map(lambda val: safe_divide(val, outputc[col.name])))
Lcdf, Lc_minus_I = clc_L(Tc)



# Modul 3: plotting
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



plot_matrix_columns(
    matrix=L_minus_I,
    sectors=OECD_sectors_ICT,
    sector_code_to_name=code_to_name,
    title=f'output indirect impact, year {year}'
)