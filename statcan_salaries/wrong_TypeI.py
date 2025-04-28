import pandas as pd
import numpy as np
import os
import time
from func_Read_CAN2020 import Read_CAN2020


# GDP impact - indirect (Type I multipliers)
# GDP impact is calculated for ICT sectors and not OECD sectors
# GDP impact is divided to: ICT - Manufacturing	ICT - Wholesaling	ICT - Software and computer services	ICT - Communications services	ICT - Software and computer services	ICT - Software and computer services

def get_OECD_data(file_path, file_nameM, sheet_nameM):
    # reading CAN2020
    data_rough1 = pd.read_excel(file_path+file_nameM, sheet_name=sheet_nameM)
    data_rough1.columns = ['OECD_Sector', 'title'] + list(data_rough1.columns[2:])

    OECD = data_rough1.iloc[0:96,:]

    # titles and descriptions: columns
    cols_descriptions = OECD.iloc[0:1,2:].copy()
    cols_description_dict = {OECD.columns[i]: OECD.iloc[0, i] for i in range(2, len(OECD.columns))}
    # titles and descriptions: rows
    rows_descriptions = OECD.iloc[:,0:2].copy()
    rows_descriptions_dict = {OECD.iloc[i,0]: OECD.iloc[i, 1] for i in range(len(OECD))}

    # Remove Descriptions from OECD
    OECD = OECD.drop(columns=OECD.columns[1])  # Drop column 1
    OECD = OECD.drop(index=0)  # Drop row 0
    # Make the first column (column 0) the index and name it 'OECD_titles'
    OECD.set_index(OECD.columns[0], inplace=True)
    OECD.index.name = 'OECD_titles'
    return OECD


def safe_divide(value, denom):
    # Division with handling zero values
    return value / denom if denom != 0 else "output is zero"

def compare_matrices_TypeI(M, file_path, file_nameM, usecols):
    MiraM = pd.read_excel( file_path + file_nameM, 
                             sheet_name='Type l (2020)', 
                             usecols=usecols, 
                             index_col=0,
                             skiprows=lambda x: x not in [4] + list(range(7, 52)) )
    MiraM.columns = MiraM.columns.str.replace(r"\.\d+$", "", regex=True)  # Remove .1, .2, etc.
    diff = M - MiraM  # Element-wise difference
    print( 'comparison of martices, difference:',diff.sum().sum() ) 

###############################################               main               #########################
start_time = time.time()
print("working directory of Read_TypeI.py is: ",os.getcwd())  # Print the current working directory

ICT_sectors = ['ICT - Manufacturing', 'ICT - Wholesaling', 'ICT - Software and computer services', 'ICT - Communications services',
               'ICT - Software and computer services',	
               'ICT - Software and computer services']
# These correspond to the numbers 17	26	33	34	35	38
OECD_sectors_for_indirect = ['C26',	'G',	'J58T60',	'J61',	'J62_63',	'M']
ICT_sectors_dict = {'ICT - Manufacturing': 'C26',
                    'ICT - Wholesaling': 'G',
                    'ICT - Software and computer services': ['J58T60', 'J62_63', 'M'],  
                    'ICT - Communications services': 'J61'}

# GDP indirect impact 
# of each OECD sector: ['C26',	'G',	'J58T60',	'J61',	'J62_63',	'M']
# GDP indirect impact of 'C26'
# revenue is aggregated by ICT subsectors but I don't get into that.
# I take the revenues from Financials worksheet:
# 1. Financials
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
file_path = "./" # windows style: r".\\"
file_nameM = 'CAN2020 - IO Analysis_v3.xlsx'
financials = pd.read_excel(file_path + file_nameM, sheet_name="Financials")

# Remove bottom table (empty rows)
financials = financials.loc[:financials[financials.eq("ICT Data (USD)").any(axis=1)].index[0] - 1]  

# Remove NaN columns and rows
financials = financials.dropna(how="all").dropna(axis=1, how="all") 

# Changing column names to be Revenues, Expenditure, etc.
last_valid_name = None
for i, col in enumerate(financials.columns):
    if col.startswith('Unnamed'):
        # Replace the 'Unnamed' column name with the last valid one
        financials.columns.values[i] = last_valid_name
    else:
        # Update the last valid column name
        last_valid_name = col

# Create MultiIndex for columns
financials.columns = pd.MultiIndex.from_arrays([financials.columns, financials.iloc[0]])
financials = financials.drop(index=0)

# C26 Revenues - ID3 equivalent - under intermediate input green tag, line 3
# Group by 'OECD sector'  and sum over 'Revenue, 2020' column

Expenditures_intermediate_input = financials.groupby(('ICT Data (CAD)', 'OECD code')).sum()[('Expenditure (including salaries)', 2020)].reset_index()
# 2. intermediate input calculation ID7:ID51
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Output_by_Revenue = technical coefficient T * Revenue - the output required to get this revenue.
# 2.1. T :
OECD = get_OECD_data(file_path, file_nameM, 'CAN2020')
IO = OECD.loc['DOM_A01_02':'DOM_T', 'A01_02':'T']
output = OECD.loc['OUTPUT','A01_02':'T']
valu = OECD.loc['VALU', 'A01_02':'T']

T = IO.apply(lambda col: col.map(lambda val: safe_divide(val, output[col.name])))
#comparison with Mira:
T2 = pd.read_excel( file_path + file_nameM, 
                             sheet_name='Type l (2020)', 
                             usecols="AW:CP", 
                             index_col=0,
                             skiprows=lambda x: x not in [4] + list(range(7, 52)) )
T2.columns = T2.columns.str.replace(r"\.\d+$", "", regex=True)  # Remove .1, .2, etc.
diffT = T - T2  # Element-wise difference
print( 'comparison of T, difference:',diffT.sum().sum() ) # agrees, gives 0.0

#Output_by_Revenue =  technical coefficient T * Revenue
# Ensure the index of Total_Revenue_intermediate_input is the OECD code for easy lookup
Expenditures_intermediate_input.set_index(('ICT Data (CAD)', 'OECD code'), inplace=True)
Expenditures_intermediate_input.rename_axis("OECD code", inplace=True)
# Reduce the column MultiIndex to the first level
Expenditures_intermediate_input.columns = Expenditures_intermediate_input.columns.get_level_values(0)

# Multiply matching columns in T by the corresponding revenue value
Intermediate_Input = pd.DataFrame()
for code in Expenditures_intermediate_input.index.values:
    Intermediate_Input[code] = T[code] * Expenditures_intermediate_input.loc[code].values

II = Intermediate_Input
# 3. Gstar = Leontieff * Intermediate_Input matrix multiplication
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  L = 1/I-T
# Identity matrix of the same size as T
I = np.eye(T.shape[0])
I_minus_T = I - T                     # dataframe
# Check if determinant is non-zero (=I-T is invertible) and compute the inverse
if np.linalg.det(I_minus_T) != 0:
    L = np.linalg.inv(I_minus_T)
    Ldf = pd.DataFrame(L, columns=T.columns, index=T.index)
else:
    print("Matrix I - T is not invertible.")
# L from nparray to pandas:
IIoldindex = II.index
II.index = II.index.str.removeprefix("DOM_")
Gstar = Ldf.dot(II)
IIindex = IIoldindex
usecols = 'IL:IQ'
compare_matrices_TypeI(Gstar, file_path, file_nameM, usecols)

# 4. GDP indirect impact = GDPratio * G* = GDP_ratio * L * II = GDP_ratio * L * T * Revenue
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# first I need GDP_ratio from Read_CAN2020.py:

_, _, _, _, GDPratio, _, _, _ = Read_CAN2020(file_path, file_nameM, 'CAN2020', 'A01_02','T')

#GDP_ind = GDPratio * Gstar
Gstaroldindex = Gstar.index
Gstar.index = Gstar.index.str.removeprefix("DOM_")
GDPind = Gstar.mul(GDPratio, axis=0)
#GDPind includes the indirect impact for all four ICT sectors
#C26 is manufacturing, G is wholsaling, J58T60, J62_63, M are computer services and J61 is communication


compare_matrices_TypeI(GDPind, file_path, file_nameM, 'IV:JA')



end_time = time.time()
print(f"Read_TypeI Execution time: {(end_time - start_time)/60:.1f} minutes")



 
print(financials)









