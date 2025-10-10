import sys
from pathlib import Path
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import matplotlib.gridspec as gridspec
import matplotlib.colors as mcolors
import matplotlib.cm as cm
from matplotlib.ticker import MaxNLocator
from matplotlib.lines import Line2D

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent / 'EIAfunctions'))
from func_data_upload_OECD_salaries import data_upload_OECD_salaries
from func_safe_divide import safe_divide, safe_divide_vector
from func_clc_L import clc_L

'''
Etot = pd.read_csv("Bench_predictions/Etotal_multivariate_E_extrap03.csv", index_col=0)
print("\n Etot from multivariate_E_extrap03:\n")
print(Etot.tail())  
'''




##################################       collecting data from input-output tables      #########################################
def clc_v_tot(df, value_col, col_tot):
    # add total employment per (country, year)
    df[col_tot] = df.groupby(["country", "year"])[value_col].transform("sum")
    # ratio of sector employment to total
    df[value_col+"_sector_ratio"] = df[value_col] / df[col_tot]
    dftotal = df[["country", "year", col_tot]].drop_duplicates()
    return df, dftotal

def collecting_year_country_data_vector(country, year, dfv, v, vector_name):
            dftemp = pd.DataFrame()
            dftemp = v.reset_index()
            dftemp.columns = ['sector', vector_name]
            dftemp['country'] = country
            dftemp['year'] = year
            dftemp = dftemp[['country', 'year', 'sector', vector_name]]
            dfv = pd.concat([dfv, dftemp], ignore_index=True)
            return dfv


def collecting_year_country_data_matrix(country, year, dfm, m, matrix_name):
            dftemp = pd.DataFrame()
            dftemp = m.reset_index().melt(id_vars=m.index.name or 'index', 
                                        var_name='buying_sector', 
                                        value_name=matrix_name)

            # Rename 'index' to 'selling_sector'
            dftemp.rename(columns={m.index.name or 'index': 'selling_sector'}, inplace=True)
            # Add metadata
            dftemp['country'] = country
            dftemp['year'] = year
            # Reorder columns
            dftemp = dftemp[['country', 'year',  'selling_sector', 'buying_sector', matrix_name]]
            # Append to the master DataFrame
            dfm = pd.concat([dfm, dftemp], ignore_index=True)
            return dfm

########################################         plotting             ###############################################
def plot_dffc(years, countries):

    for country in countries:
        for year in years:
            subset = dffc[(dffc['country'] == country) & (dffc['year'] == str(year))]
            if subset.empty:
                print(f"No data found for {country} in {year}.")
                continue
            plt.figure(figsize=(8, 4))
            plt.plot(subset.index, subset['final demand'], marker='o')
            plt.title(f"Final Demand – {country}, {year}")
            plt.xlabel("Index")
            plt.ylabel("Final Demand")
            plt.grid(True)
            plt.tight_layout()
            plt.show()


#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@                    main                  @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

# 1. get dfE from input-output tables
# later remove dfoutput etc.
table_type = 'TTL' #or'DOM'   
OECD_path = "../Data/" # windows style: r".\\"
if table_type == 'DOM':
    output_filename = '/mnt/c/NavitComputer24/2024_NES/Economics/Textbook_EIA/OECD_salaries/EIA_matrices.xlsx'
elif table_type == 'TTL':
    output_filename = '/mnt/c/NavitComputer24/2024_NES/Economics/Textbook_EIA/OECD_salaries/EIA_TTL_matrices.xlsx'

first_year = '2011'
last_year = '2020'
year_range = [str(year) for year in range(int(first_year), int(last_year) + 1)]
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



# 1. Get IO=II, X, GDP, from OECD, compensation of employees, more GDP and II from OECDadditional as well as taxes, incomegross surplus etc.
##########################################################################################################################################   
final_demand_columns = ['HFCE',	'NPISH', 'GGFC',	'GFCF',	'INVNT', 'CONS_NONRES', 'EXPO'] # 'IMPO', 'DPABR', 



dffc = pd.DataFrame()
dfother_final_demand = pd.DataFrame()
for country in countries:
    for year in year_range:
        PPP_or_exch, OECD, simple_II_labels, OECDadditional, sector_description =  data_upload_OECD_salaries(year, currency_exchange_type, table_type, country)
        
        # the following is calculated twice: in data_upload_OECD_salaries and here. I want to leave it here, but I also need it there - do I??
        II = OECD.loc[simple_II_labels, simple_II_labels]
        household_expenditure = OECD.loc[simple_II_labels, 'HFCE']
        other_final_demand = OECD.loc[simple_II_labels, final_demand_columns[1:]] #exluding HFCE - household expenditure
        
        
       
        #################################
        # final demand
        #################################
        fdf = OECD.loc[simple_II_labels, final_demand_columns].sum(axis=1)
        fcdf = OECD.loc[simple_II_labels,final_demand_columns].sum(axis=1)
        fcdf.loc['employees_compensation'] = 0        
        
        dftemp = pd.DataFrame()
        dftemp = fcdf.reset_index()
        dftemp.columns = ['sector', 'final demand']
        dftemp['country'] = country
        dftemp['year'] = year
        dftemp = dftemp[['country', 'year', 'sector', 'final demand']]
        dffc = pd.concat([dffc, dftemp], ignore_index=True)

        for name in final_demand_columns[1:]:
            dftemp = pd.DataFrame()
            dftemp = OECD.loc[simple_II_labels, name].reset_index()
            dftemp.columns = ['sector', name]
            dftemp['country'] = country
            dftemp['year'] = year
            dftemp = dftemp[['country', 'year', 'sector', name]]
            dfother_final_demand = pd.concat([dfother_final_demand, dftemp], ignore_index=True)


# checking the big dataframes
# Filter for the specific country and year

years = range(2019, 2020)
plot_dffc(years,  countries)


gdp_filename = "Bench_predictions/gdp_ARIMAgdp_currentUSD04.csv"
gdp_data = pd.read_csv(gdp_filename)
gdp_data.rename(columns={'Unnamed: 0': 'year'}, inplace=True) #renaming the column
gdp_data['year'] = gdp_data['year'].astype(int)
gdp_data.set_index('year', inplace=True) 