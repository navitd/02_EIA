# standartization of data collection
# what I have:
# 1995-2010: OECD II + E extrap
# 2011-2020: OECD II + OECD E
# 2021-2040: Lc extrap, E extrap
# extrap = extrapolated, mainly by gdp data from world bank. there's ARIMA in gdp and linear extrapolation in japan gdp

#In this file I will upload everything, make something that  uploads everything, then saves what needs to be saved to excel

# https://www.oecd.org/en/data/datasets/input-output-tables.html

# Lc_to_excel- I only save to excel Lc data,without extrap
import sys
from pathlib import Path
import os
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import matplotlib.gridspec as gridspec
import matplotlib.colors as mcolors
import matplotlib.cm as cm
import seaborn as sns
from openpyxl import load_workbook, Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import PatternFill, Alignment, Font, Border, Side
from openpyxl.cell.cell import MergedCell
# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent / 'EIAfunctions'))
from func_data_upload_OECD_without_E import data_upload_OECD_without_E
from func_plot_L import plot_matrix_columns
from func_clc_L import clc_L
from func_safe_divide import safe_divide, safe_divide_vector
from func_multipliers_by_f import multipliers_by_f
from func_plot_real_vs_predicted import plot_real_vs_predicted


##########################################         functions from Benchmarking/Employment.py       ##########################################
#the plotting functions from Employment are not needed here, they are to be moved to 08 file

def collect_v(v, country, year, cols_list, dfv):
    dftemp = pd.DataFrame()
    dftemp = v.reset_index()
    dftemp.columns = cols_list 
    dftemp['country'] = country
    dftemp['year'] = year
    dftemp = dftemp[["country", "year"] + cols_list]
    dfv = pd.concat([dfv, dftemp], ignore_index=True)
    return dfv
def collect_m(m, country, year, m_value_name, dfm):
            dftemp = pd.DataFrame()
            dftemp = m.reset_index().melt(id_vars=m.index.name or 'index', 
                                            var_name='buying_sector', 
                                            value_name=m_value_name)

            # Rename 'index' to 'selling_sector' if needed
            dftemp.rename(columns={m.index.name or 'index': 'selling_sector'}, inplace=True)
            # Add metadata
            dftemp['country'] = country
            dftemp['year'] = year
            # Reorder columns
            dftemp = dftemp[['country', 'year',  'selling_sector', 'buying_sector', m_value_name]]
            # Append to the master DataFrame
            dfm = pd.concat([dfm, dftemp], ignore_index=True)
            return dfm
####################################################         functions that plot       ######################################################
##################################################        functions that calculate        ######################################################

def multipliers2prediction(s2s_mo, fdf_year2, column_name):
    predicted_output_year2_np  = np.round(s2s_mo.to_numpy() @ fdf_year2.values.reshape(-1, 1), 1)
    
    predicted_output_year2 = pd.DataFrame(predicted_output_year2_np, index=s2s_mo.index, columns=[column_name])
    
    return predicted_output_year2



def scale_df_by_series(direct_o: pd.DataFrame, fcdf: pd.Series) -> pd.DataFrame:
    
    return direct_o[fcdf.index].mul(fcdf, axis=1)


def pivot_matrix_to_3_columns(m: pd.DataFrame, value: str) -> pd.DataFrame:
    return m.reset_index().melt(id_vars=m.index.name or 'index',
                                var_name='buying sector',
                                value_name=value).rename(columns={m.index.name or 'index': 'selling sector'})




def get_impacts(dfimpact, mdirect, mindirect, minduced, ms2s, value_vec, value_vec_name, value_col, country,year):
    impact_cols = [value_col+' impact direct', value_col+' impact indirect', value_col+' impact induced', value_col+' impact total']
    dftemp2 = None
    for data, value in zip( [mdirect, mindirect, minduced, ms2s], impact_cols ):
        m = scale_df_by_series(data, fcdf[:-1])       #this is the multiplication
        dftemp1 = pivot_matrix_to_3_columns(m, value) #this is the matrix in 3 columns
        if dftemp2 is None:
            dftemp2 = dftemp1  # First iteration: just assign
        else:
            dftemp2 = pd.merge(
                dftemp2,
                dftemp1,
                on=["selling sector", "buying sector"],
                how="outer"
            )
    # dftemp2 contains 4 GDP impacts 
    dftemp2['country'] = country
    dftemp2['year'] = year
    dftemp2[value_vec_name] = value_vec.sum()
    cols = ['country', 'year', 'buying sector', 'selling sector'] + impact_cols + [value_vec_name]
    dftemp2 = dftemp2[cols]
    dfimpact = pd.concat([dfimpact, dftemp2], ignore_index=True)
    return dfimpact




#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@                    main                  @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

# upload gdp
dfgdp_worldbank = pd.read_csv("Bench_predictions/gdp_ARIMAgdp_currentUSD04.csv")
dfgdp_worldbank.rename(columns={"Unnamed: 0": "year"}, inplace=True)
dfgdp_worldbank.iloc[:, 1:] = dfgdp_worldbank.iloc[:, 1:] * 10**(-6)
dfgdp_worldbank = dfgdp_worldbank.set_index('year')

# upload E
dfE = pd.read_csv("Bench_predictions/Esectors_from_Etot05.csv")
dfE.rename(columns={"E": "Employment"}, inplace=True)

# upload f other
dff = pd.read_csv("Bench_predictions/dfother_extrap06.csv")

########################################                           parameters                       ##################################################
start_time = time.time()
print("working directory of GDPsupplychain.py is: ",os.getcwd())  # Print the current working directory

table_type = 'TTL' #or'DOM'   
OECD_path = "../Data/" # windows style: r".\\"
if table_type == 'DOM':
    output_filename = '/mnt/c/NavitComputer24/2024_NES/Economics/Textbook_EIA/OECD_salaries/EIA_matrices.xlsx'
elif table_type == 'TTL':
    output_filename = '/mnt/c/NavitComputer24/2024_NES/Economics/Textbook_EIA/OECD_salaries/EIA_TTL_matrices.xlsx'

first_year = '1995'
last_year = '2020'
year_range = [str(year) for year in range(int(first_year), int(last_year) + 1)]
year_range2 = [str(year) for year in range(int(2021), int(2040) + 1)]
report_title = f'ICT sectors, {last_year}'
ICT_factors = {'ICT - Manufacturing': 'C26',
                'ICT - Wholesaling': 'G',
                'ICT - Software and computer services': ['J58T60', 'J62_63', 'M'],  
                'ICT - Communications services': 'J61'}
ICTsectors = ['C26', 'G', 'J58T60', 'J62_63', 'M', 'J61']

country_names = ['Canada', 'The United States', 'Great Britain', 'France', 'Germany', 'Italiy', 'Japan']
countries = ['CAN', 'USA', 'GBR', 'FRA', 'DEU', 'ITA', 'JPN'] # 'CHN' is not available in OECD, but it is in OECDadditional
country_map = dict(zip(countries, country_names))

currency_exchange_type = 'EXCH' #'EXCH' or 'PPP'

fixed_sectors = ['A01_02', 'A03', 'B05_06', 'B07_08', 'B09', 'C10T12', 'C13T15', 'C16', 'C17_18', 'C19', 'C20', 'C21', 'C22', 'C23', 'C24', 
                 'C25', 'C26', 'C27', 'C28', 'C29', 'C30', 'C31T33', 'D', 'E', 'F', 'G', 'H49', 'H50', 'H51', 'H52', 'H53', 'I', 'J58T60', 'J61',
                  'J62_63', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T']

# 1. upload OECD intput-output tables 1995-2020
###############################################   
#copied from Benchmarking/Employment.py

final_demand_columns = ['HFCE',	'NPISH',	'GGFC',	'GFCF',	'INVNT',	'CONS_NONRES', 'EXPO'] # 'IMPO', 'DPABR', 

dfoutput = pd.DataFrame() # this will hold output by country, year, sector, output
dfGDP = pd.DataFrame() # this will hold the GDP by country, year, sector, GDP
dfGDPimpact = pd.DataFrame() # this will hold country, year, buying sector, selling sector, GDPimpact
dfEimpact = pd.DataFrame()
dfTc = pd.DataFrame()
dfLc = pd.DataFrame()
for country in countries:
    for year in year_range:
        print(country, year)
        #if year in year_range2:
        #    Lc = 




        # I have decided on the format: I'll put GDPimpact in a dfGDPimpact. I need for that the whole impact code
        PPP_or_exch, OECD, simple_II_labels =  data_upload_OECD_without_E(year, currency_exchange_type, table_type, country)

        # the following is calculated twice: in data_upload_OECD_salaries and here. I want to leave it here, but I also need it there - do I??
        II = OECD.loc[simple_II_labels, simple_II_labels]
        household_expenditure = OECD.loc[simple_II_labels, 'HFCE']
        GDP         = OECD.loc['VALU', simple_II_labels]
        output      = OECD.loc['OUTPUT', simple_II_labels]

        dfoutput = collect_v(output, country, year, ['sector', 'output'], dfoutput)
        dfGDP    = collect_v(GDP,    country, year, ['sector', 'GDP'],    dfGDP)
        f = OECD.loc[simple_II_labels,final_demand_columns[1:]].sum(axis=1)
        f = f.rename_axis("sector")
        dff     = collect_v(f,       country, year, ['sector', 'other final demand total'], dff)
        

        E = dfE[(dfE.country==country) & (dfE.year==int(year))].copy()
        #remove country and year from E and add 0 at the end [employees_compensation, HFCE]=0
        E.drop(columns=['country','year'], inplace=True)
        E.set_index('sector', inplace=True)
        E.loc["HFCE"] = 0

        # 2. calculate L and Lc
        ##########################
        T = safe_divide(II, output)
        Ldf, L_minus_I = clc_L(T)

        IIc = II.copy()
        IIc["HFCE"] = household_expenditure # added a column for closed model
        # Convert Series to a one-row DataFrame with sectors as columns
        ET = E.T  # .T transposes to make index=0, columns=sectors
        ET.index = ["employees_compensation"]  # name the row
        IIc = pd.concat([IIc, ET], axis=0)
        IIc.loc['employees_compensation', 'HFCE'] = 0 

        outputc = output.copy()
        outputc['HFCE'] = E.sum().values[0]
        Tc = safe_divide(IIc, outputc)
        Lcdf, Lc_minus_I = clc_L(Tc)
        
        dfTc = collect_m(Tc, country, year, 'Tc', dfTc)
        dfLc = collect_m(Lcdf, country, year, 'Lc', dfLc)

        
        


end_time = time.time()
print(f"Elapsed time: {(end_time - start_time)/60:.1f} minutes")


dfTc.to_csv("Bench_predictions/dfTc_Lc_to_excel07.csv", index=False)
dfLc.to_csv("Bench_predictions/dfLc_Lc_to_excel07.csv", index=False)



