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

def plot_market_multipliers(series_list, panel_titles, figure_title):
    
    fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(6, 8), sharex=True)
    
    for ax, series, panel_title in zip(axes, series_list, panel_titles):
        ax.plot(series.index, series.values, marker='o', linestyle='-')
        ax.set_title(panel_title)
        ax.grid(True)
        ax.tick_params(axis='x', labelsize=8)
        ax.tick_params(axis='x', labelrotation=45)

    fig.tight_layout()
    fig.suptitle(figure_title, fontsize=14, y=0.98)
    plt.subplots_adjust(top=0.9)  # lower top to make room for suptitle
    plt.show()


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

def plot_multipliers(OECD_sectors_ICT, direct_o, indirect_o, induced_o,
                     direct_h, indirect_h, induced_h,
                     direct_g, indirect_g, induced_g, title="Multipliers Plot"):
    
    fig, axes = plt.subplots(3, 1, figsize=(6, 8), sharex=True)
    fig.suptitle(title, fontsize=16)

    # Define bar width and positions
    bar_width = 0.25
    index = np.arange(len(OECD_sectors_ICT))

    # Panel 1: Output Multipliers
    axes[0].bar(index, direct_o, bar_width, label='Direct', color='green')
    axes[0].bar(index, indirect_o, bar_width, bottom=direct_o, label='Indirect', color='red')
    axes[0].bar(index, induced_o, bar_width, bottom=direct_o + indirect_o, label='Induced', color='blue')
    axes[0].set_title('Output Multipliers ICT sector')
    axes[0].set_ylabel('Multiplier Value')
    axes[0].set_xticks(index)
    axes[0].set_xticklabels(OECD_sectors_ICT, rotation=45)
    axes[0].legend()

    # Panel 2: Income Multipliers
    axes[1].bar(index, direct_h, bar_width, label='Direct', color='green')
    axes[1].bar(index, indirect_h, bar_width, bottom=direct_h, label='Indirect', color='red')
    axes[1].bar(index, induced_h, bar_width, bottom=direct_h + indirect_h, label='Induced', color='blue')
    axes[1].set_title('Income Multipliers ICT sector')
    axes[1].set_ylabel('Multiplier Value')
    axes[1].set_xticks(index)
    axes[1].set_xticklabels(OECD_sectors_ICT, rotation=45)
    axes[1].legend()

    # Panel 3: GDP Multipliers
    axes[2].bar(index, direct_g, bar_width, label='Direct', color='green')
    axes[2].bar(index, indirect_g, bar_width, bottom=direct_g, label='Indirect', color='red')
    axes[2].bar(index, induced_g, bar_width, bottom=direct_g + indirect_g, label='Induced', color='blue')
    axes[2].set_title('GDP Multipliers ICT sector')
    axes[2].set_xlabel('Sectors')
    axes[2].set_ylabel('Multiplier Value')
    axes[2].set_xticks(index)
    axes[2].set_xticklabels(OECD_sectors_ICT, rotation=45)
    axes[2].legend()

    # Adjust the layout for better visualization
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show()


#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@               main             @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
start_time = time.time()
print("working directory of C26_output_multipliers.py is: ",os.getcwd())  # Print the current working directory

year = '2015'

# 1. Get IO=II, X, GDP, from OECD, compensation of employees, more GDP and II from OECDadditional as well as taxes, incomegross surplus etc.
##########################################################################################################################################   
PPP, OECD, simple_II_labels, OECDadditional, sector_description =  data_upload_OECD_salaries(year)

additional_OECD_column_names = ['intermediate_consumption', 'mixed_income_gross', 'net_taxes_on_production',
                    'surplus_and_mixed_income_gross', 'output', 'salaries', 'employees_compensation', 'GDP' ]


II = OECD.loc[simple_II_labels, simple_II_labels]
household_expenditure = OECD.loc[simple_II_labels, 'HFCE']
final_demand_columns = ['HFCE',	'NPISH',	'GGFC',	'GFCF',	'INVNT',	'DPABR',	'CONS_NONRES',	'EXPO',	'IMPO']
other_final_demand = OECD.loc[simple_II_labels, final_demand_columns[1:]] #exluding HFCE - household expenditure
total       = OECD.loc[simple_II_labels, 'TOTAL'] #equals to output, this is x
GDP         = OECD.loc['VALU', simple_II_labels]
output      = OECD.loc['OUTPUT', simple_II_labels]


# 2. calculate L and Lc
###########################################################################################################################################
T = safe_divide(II, output)
Ldf, L_minus_I = clc_L(T)

IIc = II.copy()
IIc["HFCE"] = household_expenditure # added a column for closed model
IIc.loc['employees_compensation'] = OECDadditional['employees_compensation'] #If I wanted a column I would have written IIC['employees_compensation']

IIc.loc['employees_compensation', 'HFCE'] = 0 #T97_values.loc[T97_values['Transaction'] == 'Compensation of employees', 'OBS_VALUE_USD'].values[0]

outputc = output.copy()
outputc['HFCE'] = OECD.loc['OUTPUT', 'HFCE']
Tc = safe_divide(IIc, outputc)
Lcdf, Lc_minus_I = clc_L(Tc)

