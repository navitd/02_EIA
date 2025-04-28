import sys
from pathlib import Path
import os
import time
import pandas as pd
import numpy as np
# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent / 'EIAfunctions'))
from func_data_upload import data_upload



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

GDPstatcan = statcan[(statcan["TIME_PERIOD"] == int(year)) & (statcan["Transaction"] == 'Value added, gross')].drop(columns=["Economic activity","TIME_PERIOD","Transaction"])
    #GDPstatcan.set_index("detailed_sectors")["OBS_VALUE"] #detailed_sectors is now the index

    # now GSPstatcan is with detailed OECD codes and we need to translate it to known OECD codes
    # from A01 and A02 to A01_02
GDPstatcan['OECD_codes'] = GDPstatcan['detailed_sectors'].map(mapping_dict)
GDPstatcan = GDPstatcan.sort_values(by="OECD_codes")

# sum A01 and A02 to A01_02
# Group by OECD_codes and sum the OBS_VALUE column
GDPstatcan_grouped = GDPstatcan.groupby('OECD_codes', as_index=False)['OBS_VALUE'].sum()
# GDPstatcan_grouped I checked and it is correct

#chose from it only codes that appear in OECD:
#merge values to GDP

GDP2 = GDP.reset_index(name='GDP_OECD').copy()
GDP2.rename(columns={'index': 'OECD_codes1'}, inplace=True)
GDP2 = pd.merge(GDP2, GDPstatcan_grouped, left_on='OECD_codes1', right_on='OECD_codes', how='inner')

GDP2['ratio'] = GDP2['GDP_OECD'] / GDP2['OBS_VALUE']
GDP2.rename(columns={'OBS_VALUE':"GDP_statcan_CAD"},inplace=True)
GDP2.drop(columns=['OECD_codes'], inplace=True)

# CAD to USD
# Load the Excel file and read the specific sheet, selecting only the necessary columns
file_path = '/mnt/c/NavitComputer24/2024_NES/Economics/Data/PPP_data.xlsx'  
PPPtable = pd.read_excel(file_path, sheet_name='PPP_data', usecols=['TIME_PERIOD', 'OBS_VALUE'])
PPP = PPPtable[PPPtable["TIME_PERIOD"]==int(year)]["OBS_VALUE"].values[0] #this is the value for 2020


GDP2["GDP_statcan_USD"] = (GDP2["GDP_statcan_CAD"] / PPP).round(1) 



T = II.apply(lambda col: col.map(lambda val: safe_divide(val, output[col.name])))

n = T.shape[0] #number of rows
identity_matrix = np.eye(n)
I_minus_T = identity_matrix - T 
if np.linalg.det(I_minus_T) != 0:
    L = np.linalg.inv(I_minus_T)
    Ldf = pd.DataFrame(L, columns=T.columns, index=T.index)
else:
    print("Matrix I - T is not invertible.")


#simple output multipliers = vectors of L
later I need to do income multipleirs - income/output. 
now I will copy the aboe (output mutlipleirs is actualy L) to an ouput_multipleirs.py and plot accordingly
and make predictions

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
