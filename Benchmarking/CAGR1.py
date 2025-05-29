# benchmarking - the EIA from print2xls3.py is in a function and I choose sectors, years, calculate compound annual growth rate and plot
# input-output table from OECD
# https://www.oecd.org/en/data/datasets/input-output-tables.html


import sys
from pathlib import Path
import os
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from openpyxl import load_workbook, Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import PatternFill, Alignment, Font, Border, Side
import openpyxl
import inspect
from openpyxl.cell.cell import MergedCell
# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent / 'EIAfunctions'))
from func_data_upload_OECD_salaries import data_upload_OECD_salaries
from func_plot_L import plot_matrix_columns
from func_clc_L import clc_L
from func_safe_divide import safe_divide, safe_divide_vector








##################################################             old functions               ######################################################

def multipliers2prediction(s2s_mo, fdf_year2, column_name):
    predicted_output_year2_np  = np.round(s2s_mo.to_numpy() @ fdf_year2.values.reshape(-1, 1), 1)
    
    predicted_output_year2 = pd.DataFrame(predicted_output_year2_np, index=s2s_mo.index, columns=[column_name])
    
    return predicted_output_year2


def plot_real_vs_predicted(output_real, output_pred, 
                           income_real, income_pred, 
                           gdp_real, gdp_pred, 
                           year1, year2, title):
    fig, axes = plt.subplots(3, 1, figsize=(6,8), sharex=True)
    
    fig.suptitle(title, fontsize=16)

    # Panel 1: Output
    axes[0].plot(output_real.index, output_real, label='Real Output', color='purple', marker='o')
    axes[0].plot(output_pred.index, output_pred, label='Predicted Output', color='red', marker='o')
    axes[0].set_title(f'Output {year2} Based on {year1}')
    axes[0].set_xlabel('Sectors')
    axes[0].set_ylabel('Million USD')
    axes[0].legend()

    # Panel 2: Income
    axes[1].plot(income_real.index, income_real, label='Real Income', color='purple', marker='o')
    axes[1].plot(income_pred.index, income_pred, label='Predicted Income', color='red', marker='o')
    axes[1].set_title(f'Income {year2} Based on {year1}')
    axes[1].set_xlabel('Sectors')
    axes[1].set_ylabel('Million USD')
    axes[1].legend()

    # Panel 3: GDP
    axes[2].plot(gdp_real.index, gdp_real, label='Real GDP', color='purple', marker='o')
    axes[2].plot(gdp_pred.index, gdp_pred, label='Predicted GDP', color='red', marker='o')
    axes[2].set_title(f'GDP {year2} Based on {year1}')
    axes[2].set_xlabel('Sectors')
    axes[2].set_ylabel('Million USD')
    axes[2].legend()
    for ax in axes:
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()


 
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@                    main                  @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
start_time = time.time()
print("working directory of print2xls3.py is: ",os.getcwd())  # Print the current working directory



year = '2015'
year2 = '2015'
table_type = 'TTL' #or'DOM'   
OECD_path = "../Data/" # windows style: r".\\"
if table_type == 'DOM':
    output_filename = '/mnt/c/NavitComputer24/2024_NES/Economics/Textbook_EIA/OECD_salaries/EIA_matrices.xlsx'
elif table_type == 'TTL':
    output_filename = '/mnt/c/NavitComputer24/2024_NES/Economics/Textbook_EIA/OECD_salaries/EIA_TTL_matrices.xlsx'

report_title = f'ICT sectors, {year}'
sector_groups = {'ICT - Manufacturing': 'C26',
                    'ICT - Wholesaling': 'G',
                    'ICT - Software and computer services': ['J58T60', 'J62_63', 'M'],  
                    'ICT - Communications services': 'J61'}


# 1. Get IO=II, X, GDP, from OECD, compensation of employees, more GDP and II from OECDadditional as well as taxes, incomegross surplus etc.
##########################################################################################################################################   
currency_exchange_type = 'EXCH' #'EXCH' or 'PPP'
PPP_or_exch, OECD, simple_II_labels, OECDadditional, sector_description =  data_upload_OECD_salaries(year, currency_exchange_type, table_type)
print(f'PPP_or_exch {PPP_or_exch}')

additional_OECD_column_names = ['intermediate_consumption', 'mixed_income_gross', 'net_taxes_on_production',
                                'surplus_and_mixed_income_gross', 'output', 'salaries', 'employees_compensation', 'GDP' ]

# the following is calculated twice: in data_upload_OECD_salaries and here. I want to leave it here, but I also need it there - do I??
II = OECD.loc[simple_II_labels, simple_II_labels]
household_expenditure = OECD.loc[simple_II_labels, 'HFCE']
final_demand_columns = ['HFCE',	'NPISH',	'GGFC',	'GFCF',	'INVNT',	'CONS_NONRES', 'EXPO'] # 'IMPO', 'DPABR', 
other_final_demand = OECD.loc[simple_II_labels, final_demand_columns[1:]] #exluding HFCE - household expenditure
GDP         = OECD.loc['VALU', simple_II_labels]
output      = OECD.loc['OUTPUT', simple_II_labels]
#I don't need to worry about household_expenditure of GDP or output - they are both 0
# but output of GDP is given and should be marked independently

#single values in OECD:
#GDP_of_household_expenditure = OECD.loc['VALU', 'HFCE']
#GDP_of_total_column = OECD.loc['VALU', 'TOTAL'] # total is the output, should be equal to f_row_sums.sum(axis=0)
#GDP_of_final_demand = OECD.loc['VALU', final_demand_columns]        #this could be added to the rows from the right or to the columns form the bottom
#output_of_final_demand = OECD.loc['OUTPUT', final_demand_columns]   #probably will not be needed

# from looking at the numbers:
# total = output
# II_row_sums + f_row_sums = total = output
# household_expenditure is the column added to II to get the closed model
# when uploading data for the first time run:
# data_exploration_flags(II,household_expenditure,other_final_demand,output,output_of_final_demand,OECD_rough)

#final demand and value added are not the same at all

# 2. calculate L and Lc
###########################################################################################################################################
T = safe_divide(II, output)
Ldf, L_minus_I = clc_L(T)

IIc = II.copy()
IIc["HFCE"] = household_expenditure # added a column for closed model
IIc.loc['employees_compensation'] = OECDadditional['employees_compensation'] #If I wanted a column I would have written IIC['employees_compensation']
IIc.loc['employees_compensation', 'HFCE'] = 0 #T97_values.loc[T97_values['Transaction'] == 'Compensation of employees', 'OBS_VALUE_USD'].values[0]

outputc = output.copy()
outputc['HFCE'] = OECDadditional['employees_compensation'].sum()
Tc = safe_divide(IIc, outputc)
Lcdf, Lc_minus_I = clc_L(Tc)


# 3. calculate multipliers
###########################################################################################################################################

mo = Ldf.sum(axis=0) #dollar's worth of outcome per 1 dollar's worth of new final demand
moc_trancated = Lcdf.iloc[:-1].sum(axis=0) #dollar's worth of outcome per 1 dollar's worth of new final demand

# income multipliers mh
Ej_by_xj = Tc.iloc[-1,:-1] #hosehold income received per dollar's worth of sector output  
income_F_multipliers = Ldf.mul(Ej_by_xj, axis=0) #household income recieved per dollar's worth of secotr final demand
# Ej/xj*Ljk - Ljk is how much output was sold from j to k. and j is the sector that paid the salaries, so Ej/xj is used.
sum_income_F_multipliers = income_F_multipliers.sum(axis=0) 
# m(h)_k = sum_j(Ej/xj*Ljk) - sum over j of the detailed income_F_multipliers - sum over the rows
# an additional dolar of final demand in sector k generates m(h)_k dollars of new household income when all direct and
# indirect effects are converted into dollar estimates of income.
# income_F_multipliers is the details for each sector - how much income is generated by an additional dollar of final demand in sector k for each of the other sectors
# the above is only direct+indirect effects
# direct + indirect + induced effect - same calculation but with Lcdf

#income multipliers second time
Ej_by_xj = Tc.iloc[-1,:]
#it has a different size than above
# to add: J61 = J - J58T60 - J62_63
# my disagreement with Tanveer is from compensation of employees J61, B07_08, C31T33, J62_63

# GDP multipliers
GDPc = OECD.loc['VALU', simple_II_labels + ['HFCE']]
GDPj_by_xj = safe_divide_vector(GDPc, outputc)

# summary of multipliers without typeI and typeII - 
# 12 multipliers output, income, GDP, X sector2sector, sector2market X simple model, closed model
# all of the closed model multipliers are trancated (the row and column of salaries and final demand are not included)
s2s_mo = Ldf                       # direct + indirect effect
s2s_moc = Lcdf                     # direct + indirect + iduced effect
s2s_mh = Ldf.mul(Ej_by_xj.iloc[ :-1 ], axis=0) 
s2s_mhc = Lcdf.mul(Ej_by_xj.rename(index={'HFCE': 'employees_compensation'}), axis=0)
s2s_mg =  Ldf.mul(GDPj_by_xj.iloc[ :-1 ], axis=0)    
s2s_mgc = Lcdf.mul(GDPj_by_xj.rename(index={'HFCE': 'employees_compensation'}), axis=0)

mo = s2s_mo.sum(axis=0)
moc = s2s_moc.sum(axis=0)
mh = s2s_mh.sum(axis=0)
mhc = s2s_mhc.sum(axis=0)
mg = s2s_mg.sum(axis=0)
mgc = s2s_mgc.sum(axis=0)


# impact analysis
###################################################
# multipliers: direct, indirect, induced separately
###################################################
n = T.shape[0]
# direct
direct_o = pd.DataFrame(np.eye(n), index=s2s_mo.index, columns=s2s_mo.columns)
direct_h = pd.DataFrame(np.zeros((n, n)), index=Ej_by_xj.iloc[:-1].index, columns=Ej_by_xj.iloc[:-1].index)
np.fill_diagonal(direct_h.values, Ej_by_xj.values)
direct_g = pd.DataFrame(np.zeros((n, n)), index=GDPj_by_xj.iloc[:-1].index, columns=GDPj_by_xj.iloc[:-1].index)
np.fill_diagonal(direct_g.values, GDPj_by_xj.values)
#indirect
indirect_o = s2s_mo - direct_o
#Ej_by_xj*L_minus_I = s2s_mh-Ej_by_xj
indirect_h  = s2s_mh - direct_h
#GDPj_by_xj*L_minus_I = s2s_mg-GDPj_by_xj
indirect_g  = s2s_mg - direct_g
#induced
induced_o = s2s_moc.iloc[:-1,:-1] - s2s_mo
induced_h = s2s_mhc.iloc[:-1,:-1] - s2s_mh
induced_g = s2s_mgc.iloc[:-1,:-1] - s2s_mg




# predict output, income and GDP
#################################
#year2 = '2015'

_, OECD_year2, _, OECDadditional_year2, _ =  data_upload_OECD_salaries(year, currency_exchange_type, table_type)
income_year2 = OECDadditional_year2['employees_compensation']
GDP_year2 = OECD_year2.loc['VALU', simple_II_labels]

fdf_year2 = OECD_year2.loc[simple_II_labels, final_demand_columns].sum(axis=1)
#there is what causes closed model to be in accuarete:
#fcdf_year2 = OECD_year2.loc[simple_II_labels,final_demand_columns[1:]].sum(axis=1)
#I should take HFCE inside fcdf_year2. 
fcdf_year2 = OECD_year2.loc[simple_II_labels,final_demand_columns].sum(axis=1)
fcdf_year2.loc['employees_compensation'] = 0

predicted_output_year2 = multipliers2prediction(s2s_mo, fdf_year2, 'Predicted_Output')
predicted_outputc_year2 = multipliers2prediction(s2s_moc, fcdf_year2, 'Predicted_Output')
predicted_income_year2 = multipliers2prediction(s2s_mh, fdf_year2, 'Predicted_Income')  
predicted_incomec_year2 = multipliers2prediction(s2s_mhc, fcdf_year2, 'Predicted_Income') 
predicted_GDP_year2 = multipliers2prediction(s2s_mg, fdf_year2, 'Predicted_GDP') 
predicted_GDPc_year2 = multipliers2prediction(s2s_mgc, fcdf_year2, 'Predicted_GDP') 
output_year2      = OECD_year2.loc['OUTPUT', simple_II_labels]


def multipliers_by_f(M, fcdf_year2, title):
    fcdf_year2 = fcdf_year2.values.reshape(-1, 1) if isinstance(fcdf_year2, pd.Series) else fcdf_year2
    result = M.values @ fcdf_year2
    result_df = pd.DataFrame(result, index=M.index, columns=[title])
    return result_df

temp = multipliers_by_f(s2s_moc.iloc[:-1,:-1], fcdf_year2[:-1], 'Total output impact')











##############################              plotting          #############################

                       
   





# bar graphs of direct, indirect and induced
'''
ICT_sectors = ['ICT - Manufacturing', 'ICT - Wholesaling', 'ICT - Software and computer services', 'ICT - Communications services',
               'ICT - Software and computer services',	'ICT - Software and computer services']
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

# assume I want to see the ICT sectors as selling sectors. how much they will sell
plot_multipliers(OECD_sectors_ICT, direct_o.loc[OECD_sectors_ICT,:].sum(axis=1), indirect_o.loc[OECD_sectors_ICT,:].sum(axis=1), 
                 induced_o.loc[OECD_sectors_ICT,:].sum(axis=1),
                 direct_h.loc[OECD_sectors_ICT,:].sum(axis=1), indirect_h.loc[OECD_sectors_ICT,:].sum(axis=1),
                 induced_h.loc[OECD_sectors_ICT,:].sum(axis=1),
                 direct_g.loc[OECD_sectors_ICT,:].sum(axis=1), indirect_g.loc[OECD_sectors_ICT,:].sum(axis=1),
                 induced_g.loc[OECD_sectors_ICT,:].sum(axis=1), 
                  title="Multipliers")
'''




