import sys
from pathlib import Path
import os
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent / 'EIAfunctions'))
from func_data_upload_OECD_salaries import data_upload_OECD_salaries
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

def safe_divide_vector(vector, output):
    # Check if there are NaNs in either II or output
    if vector.isna().any():
        raise ValueError("numerator contains NaN values.")
    if output.isna().any():
        raise ValueError("Output contains NaN values.")
    
    # Replace zeros in outputc with NaN to avoid division by zero
    output_safe = output.replace(0, np.nan)
    # Divide vector by output, handling NaN values (from division by zero)
    coefficient = vector.divide(output_safe, axis=0)
    # Replace any NaN values (from division by zero) with zero
    coefficient = coefficient.fillna(0)
    return coefficient

def plot_OECD_OECD_comparison(GDP, GDP_additional, II, II_additional, output, output_additional, title):
    fig, axes = plt.subplots(3,1, figsize=(18, 6))  # 1 row, 3 columns
    fig.suptitle(title, fontsize=16)
    # Plot GDP and GDP_additional
    axes[0].plot(GDP, marker='o', label=GDP.name if GDP.name else 'GDP')
    axes[0].plot(GDP_additional, marker='o', label=GDP_additional.name if GDP_additional.name else 'GDP Additional')
    axes[0].set_title('GDP vs GDP Additional')
    axes[0].set_ylabel('Value')
    axes[0].legend()
    axes[0].grid(True)
    axes[0].tick_params(axis='x', rotation=45)

    # Plot II and II_additional
    axes[1].plot(II, marker='o', label=II.name if II.name else 'II')
    axes[1].plot(II_additional, marker='o', label=II_additional.name if II_additional.name else 'II Additional')
    axes[1].set_title('II vs II Additional')
    axes[1].legend()
    axes[1].grid(True)
    axes[1].tick_params(axis='x', rotation=45)

    # Plot output and output_additional
    axes[2].plot(output, marker='o', label=output.name if output.name else 'Output')
    axes[2].plot(output_additional, marker='o', label=output_additional.name if output_additional.name else 'Output Additional')
    axes[2].set_title('Output vs Output Additional')
    axes[2].legend()
    axes[2].grid(True)
    axes[2].tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plt.show()


#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@               main             @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
start_time = time.time()
print("working directory of C26_output_multipliers.py is: ",os.getcwd())  # Print the current working directory

year = '2015'

# 1. Get IO=II, X, GDP, from OECD, compensation of employees, more GDP and II from OECDadditional as well as taxes, incomegross surplus etc.
##########################################################################################################################################   
PPP, OECD, simple_II_labels, OECDadditional, sector_description =  data_upload_OECD_salaries(year)

II = OECD.loc[simple_II_labels, simple_II_labels]
household_expenditure = OECD.loc[simple_II_labels, 'HFCE']
final_demand_columns = ['HFCE',	'NPISH',	'GGFC',	'GFCF',	'INVNT',	'DPABR',	'CONS_NONRES',	'EXPO',	'IMPO']
other_final_demand = OECD.loc[simple_II_labels, final_demand_columns[1:]] #exluding HFCE - household expenditure
total       = OECD.loc[simple_II_labels, 'TOTAL'] #equals to output, this is x
GDP         = OECD.loc['VALU', simple_II_labels]
output      = OECD.loc['OUTPUT', simple_II_labels]



additional_OECD_column_names = ['intermediate_consumption', 'mixed_income_gross', 'net_taxes_on_production',
                    'surplus_and_mixed_income_gross', 'output', 'salaries', 'employees_compensation', 'GDP' ]
# compare: GDP, output, intermediate_consumption
GDP_additional = OECDadditional.loc[ simple_II_labels, 'GDP']
output_additional = OECDadditional.loc[ simple_II_labels, 'output']
II_additional = OECDadditional.loc[ simple_II_labels, 'intermediate_consumption']
E_additional = OECDadditional.loc[ simple_II_labels, 'employees_compensation']  



plot_OECD_OECD_comparison(GDP, GDP_additional, II.sum(axis=0), II_additional, output, output_additional,f'OECD vs OECD Additional, {year}')

def plot_single_series(E_additional, title):
    plt.figure(figsize=(8, 6))
    
    plt.plot(E_additional, marker='o', label=E_additional.name if E_additional.name else 'Series')
    plt.ylabel('Value')
    plt.title(title)
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

plot_single_series(E_additional, f'Employees Compensation, {year}')