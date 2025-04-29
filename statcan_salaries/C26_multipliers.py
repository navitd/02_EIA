import sys
from pathlib import Path
import os
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent / 'EIAfunctions'))
from func_data_upload2 import data_upload
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

def clc_output_multipliers(year,T97_flag=False):
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
    other_final_demand = OECD.loc[simple_II_labels, final_demand_columns[1:]] #exluding HFCE - household expenditure
    total       = OECD.loc[simple_II_labels, 'TOTAL'] #equals to output, this is x
    #GDP         = OECD.loc['VALU', simple_II_labels]
    output      = OECD.loc['OUTPUT', simple_II_labels]
    #I don't need to worry bout household_expenditure of GDP or output - they are both 0
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

    # Modul 2: calculate L and multipliers
    T = safe_divide(II, output)
    Ldf, L_minus_I = clc_L(T)

    IIc = II.copy()
    IIc["HFCE"] = household_expenditure # added a column for closed model
    IIc.loc['employees_compensation'] = statcan_sectors_data['employees_compensation'] #If I wanted a column I would have written IIC['employees_compensation']
    # temporary fix, perhaps I should put household_expenditure of employees_compensation to 0
    if T97_flag:
        IIc.loc['employees_compensation', 'HFCE'] = T97_values.loc[T97_values['Transaction'] == 'Compensation of employees', 'OBS_VALUE_USD'].values[0]
    else:
        IIc.loc['employees_compensation', 'HFCE'] = 0 #T97_values.loc[T97_values['Transaction'] == 'Compensation of employees', 'OBS_VALUE_USD'].values[0]
    #T is manifestly not HFCE because the numbers are different
    outputc = output.copy()
    outputc['HFCE'] = OECD.loc['OUTPUT', 'HFCE']
    Tc = safe_divide(IIc, outputc)
    Lcdf, Lc_minus_I = clc_L(Tc)

    return statcan_sectors_data, OECD, simple_II_labels, final_demand_columns, II, IIc, output, outputc, T, Tc, Ldf, L_minus_I, Lcdf, Lc_minus_I



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


###############################################               main               #########################
start_time = time.time()
print("working directory of C26_output_multipliers.py is: ",os.getcwd())  # Print the current working directory
# the work on the multipliers is not finished yet, that's why it is still here and not in a separate file.
# OECD_statcan_comp.py has a slightly different version of the same function (outputing PPP as well)

#fix: create a function that calculates all the multipleirs. the above clc_multipliers is only for L and Lc. 
#at the beginning they were the multipleirs.


print(f'C26 is Manufacture of computer, electronic and optical products')
year = '2015'
PPP, _, _, _, sector_description, _ =  data_upload(year)
sector = 'C26'
sector_description = sector_description[sector]


statcan_sectors_data, OECD, simple_II_labels, final_demand_columns, II, IIc, output, outputc, T, Tc, Ldf, L_minus_I, Lcdf, Lc_minus_I = clc_output_multipliers(year)


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

# multipliers: direct, indirect, induced separately
###################################################
n = T.shape[0]
# direct
direct_o = pd.DataFrame(np.ones((n, n)), index=s2s_mo.index, columns=s2s_mo.columns)
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

#add a bar plot of the 6 ict sectors

# predict output, income and GDP
#################################
year2 = '2020'

statcan_sectors_data_year2, OECD_year2, simple_II_labels, final_demand_columns, _, _, output_year2, outputc_year2, _, _, _, _, _, _ = clc_output_multipliers(year2)
income_year2 = statcan_sectors_data_year2['employees_compensation']
GDP_year2 = OECD_year2.loc['VALU', simple_II_labels]

fdf_year2 = OECD_year2.loc[simple_II_labels, final_demand_columns].sum(axis=1)
fcdf_year2 = OECD_year2.loc[simple_II_labels,final_demand_columns].sum(axis=1) #added HFCE to fcdf_year2
fcdf_year2.loc['employees_compensation'] = 0

predicted_output_year2 = multipliers2prediction(s2s_mo, fdf_year2, 'Predicted_Output')
predicted_outputc_year2 = multipliers2prediction(s2s_moc, fcdf_year2, 'Predicted_Output')
predicted_income_year2 = multipliers2prediction(s2s_mh, fdf_year2, 'Predicted_Income')  
predicted_incomec_year2 = multipliers2prediction(s2s_mhc, fcdf_year2, 'Predicted_Income') 
predicted_GDP_year2 = multipliers2prediction(s2s_mg, fdf_year2, 'Predicted_GDP') 
predicted_GDPc_year2 = multipliers2prediction(s2s_mgc, fcdf_year2, 'Predicted_GDP') 


# calculate type I and typeII multipliers




##############################              plotting          #############################
#prediction plotting

plot_real_vs_predicted(output_year2, predicted_output_year2,
                       income_year2, predicted_income_year2,
                       GDP_year2, predicted_GDP_year2,  
                       year, year2,'Simple Model')


plot_real_vs_predicted(output_year2, predicted_outputc_year2.iloc[:-1],
                       income_year2, predicted_incomec_year2.iloc[:-1],
                       GDP_year2, predicted_GDPc_year2.iloc[:-1],  
                       year, year2,'Closed Model')


#multipliers plotting
plot_market_multipliers([mo, mh, mg], ['New Dollar\'s Output per New Dollar\'s Final Demand',
                                       'New Dollar\'s Income per New Dollar\'s Final Demand',
                                       'New Dollar\'s GDP per New Dollar\'s Final Demand'], figure_title=f"{year}, Simple Model: Direct + Indirect")
plot_market_multipliers([moc, mhc, mgc], ['New Dollar\'s Output per New Dollar\'s Final Demand',
                                          'New Dollar\'s Income per New Dollar\'s Final Demand',
                                          'New Dollar\'s GDP per New Dollar\'s Final Demand'], figure_title=f"{year}, Closed Model: Direct + Indirect + Induced")


plot_market_multipliers([s2s_mo.loc[:,sector], s2s_mh.loc[:,sector], s2s_mg.loc[:,sector]], ['New Dollar\'s Output per New Dollar\'s Final Demand',
                                       'New Dollar\'s Income per New Dollar\'s Final Demand',
                                       'New Dollar\'s GDP per New Dollar\'s Final Demand'], 
                                       figure_title=f"{year}, Simple Model: Direct + Indirect, {sector_description}")
plot_market_multipliers([s2s_moc.loc[:,sector], s2s_mhc.loc[:,sector], s2s_mgc.loc[:,sector]], ['New Dollar\'s Output per New Dollar\'s Final Demand',
                                       'New Dollar\'s Income per New Dollar\'s Final Demand',
                                       'New Dollar\'s GDP per New Dollar\'s Final Demand'], 
                                       figure_title=f"{year}, Closed Model: Direct + Indirect + Induced, {sector_description}")


'''
# bar graphs of direct, indirect and induced
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





# the following is an old plotting. only ICT and only T
'''
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
)'
'''