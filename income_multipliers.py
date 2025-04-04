import pandas as pd
import numpy as np
import os
import time
from func_Read_CAN2020 import Read_CAN2020



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



#the following is not used because it is wrong
def compute_income_multipliers(T: np.ndarray, wages: np.ndarray, output, final_demand: np.ndarray):
    """
    Computes direct, indirect, induced, Type I, and Type II income multipliers.
    
    Parameters:
    io_matrix (np.ndarray): Square IO matrix (n x n)
    wages (np.ndarray): Wage vector (n x 1)
    final_demand (np.ndarray): Final demand vector (n x 1)
    
    Returns:
    dict: A dictionary with computed multipliers.
    """
    n = T.shape[0]
    
    # Compute the Leontief inverse
    identity_matrix = np.eye(n)
    leontief_inverse = np.linalg.inv(identity_matrix - T)
    
    # Direct income multiplier       ?
    direct_income = wages / np.array(output)
    
    # Indirect income multiplier
    indirect_income = wages @ leontief_inverse
    
    # Induced income multiplier
    income_vector = wages @ leontief_inverse
    induced_income = np.sum(income_vector) / np.sum(final_demand)
    
    # Type I and Type II multipliers
    type_I_multiplier = np.sum(direct_income + indirect_income) / np.sum(direct_income)
    type_II_multiplier = np.sum(direct_income + indirect_income + induced_income) / np.sum(direct_income)
    
    return {
        "Direct Income Multiplier": np.sum(direct_income),
        "Indirect Income Multiplier": np.sum(indirect_income),
        "Induced Income Multiplier": induced_income,
        "Type I Multiplier": type_I_multiplier,
        "Type II Multiplier": type_II_multiplier,
    }


###############################################               main               #########################
start_time = time.time()
print("working directory of income_multipliers.py is: ",os.getcwd())  # Print the current working directory


# Module 1: Get IO=II, X, GDP, from OECD, wages, compensation for employees and employment from CANSTAT
# later move this to a function that receives country and year and uploads the results

OECD_path = "../Data/NATIODOMIMP/" # windows style: r".\\"
OECD_name = 'CAN2019dom.csv'
OECD_rough = pd.read_csv(OECD_path + OECD_name)

# Remove imports from matrix
OECD_rough = OECD_rough.set_index(OECD_rough.columns[0])  # Set first column as index
OECD_rough.index = OECD_rough.index.astype(str)  # Ensure index is strings
OECD = OECD_rough[~OECD_rough.index.str.startswith("IMP_")]
simple_II_labels = OECD_rough.columns.tolist()[OECD_rough.columns.get_loc("A01_02") : OECD_rough.columns.get_loc("T") + 1]
OECD.index = OECD.index.str.removeprefix("DOM_")
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

# uploading form CANSTAT from 
# https://data-explorer.oecd.org/vis?tm=value%20added%20and%20its%20components%20by%20activity&pg=0&snb=10&df[ds]=dsDisseminateFinalDMZ&df[id]=DSD_NAMAIN10%40DF_TABLE6&df[ag]=OECD.SDD.NAD&df[vs]=2.0&dq=A.AUS...B1G.....V..&lom=LASTNPERIODS&lo=5&to[TIME_PERIOD]=false
# I downloaded it to C:\NavitComputer24\2024_NES\Economics\Data\STATCAN
# I want to make another file that compares STATCAN to OECD and checks consistency between them.
# the statcan file: OECD_VA_Breakdown.csv or OECD_VA_Breakdown2.csv
# OECD is in USD and STATCAN is in CAD?






T = IO.apply(lambda col: col.map(lambda val: safe_divide(val, output[col.name])))
T = II.div(output, axis=0) #correct this output may be zero
n = T.shape[0] #number of rows
identity_matrix = np.eye(n)
I_minus_T = identity_matrix - T 
if np.linalg.det(I_minus_T) != 0:
    L = np.linalg.inv(I_minus_T)
    Ldf = pd.DataFrame(L, columns=T.columns, index=T.index)
else:
    print("Matrix I - T is not invertible.")






multipliers = compute_income_multipliers(np.array(II), wages, final_demand)
# final demand should be broken to household_expenditure and all the rest

for key, value in multipliers.items():
    print(f"{key}: {value:.4f}")



#ICT sectors information
ICT_sectors = ['ICT - Manufacturing', 'ICT - Wholesaling', 'ICT - Software and computer services', 'ICT - Communications services',
               'ICT - Software and computer services',	
               'ICT - Software and computer services']
# These correspond to the numbers 17	26	33	34	35	38
OECD_sectors_for_indirect = ['C26',	'G',	'J58T60',	'J61',	'J62_63',	'M']
ICT_sectors_dict = {'ICT - Manufacturing': 'C26',
                    'ICT - Wholesaling': 'G',
                    'ICT - Software and computer services': ['J58T60', 'J62_63', 'M'],  
                    'ICT - Communications services': 'J61'}