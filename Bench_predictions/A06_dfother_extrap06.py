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




################################       collecting data from input-output tables      #########################################

def clc_v_tot(df, value_col, col_tot):
    df[col_tot] = df.groupby(["country", "year"])[value_col].transform("sum")
    dftotal = df[["country", "year", col_tot]].drop_duplicates()
    return dftotal

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
def plot_dffc(dffc, years, countries):

    for country in ['CAN']: #countries:
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

def plot_dfother_final_demand(df, col_name, years, countries):

    for country in ['CAN']: #countries:
        for year in years:
            subset = df[(df['country'] == country) & (df['year'] == str(year))][col_name]
            if subset.empty:
                print(f"No data found for {country} in {year}.")
                continue
            plt.figure(figsize=(8, 4))
            plt.plot(subset.index, subset, marker='o')
            plt.title(f"Final Demand – {country}, {year}")
            plt.xlabel("Index")
            plt.ylabel("Final Demand")
            plt.grid(True)
            plt.tight_layout()
            plt.show()


def plot_v_by_year_1panel(df, countries, ylabel, title):
    plt.figure(figsize=(10,6))

    for country in df.columns:
        plt.plot(df.index, df[country], marker='o', label=country)

    plt.xlabel("Year")
    plt.ylabel(ylabel + " [Millions USD]")
    plt.title(title)
    plt.legend()
    plt.grid(True)
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

first_year = '1995'
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

        # building df1year (also 1 country)
        vector_name=final_demand_columns[1]
        ftemp = pd.DataFrame()
        dftemp = OECD.loc[simple_II_labels,vector_name].reset_index()
        dftemp.columns = ['sector', vector_name]
        dftemp['country'] = country
        dftemp['year'] = year
        dftemp = dftemp[['country', 'year', 'sector', vector_name]]

        df1year = dftemp.copy()
        for vector_name in final_demand_columns[2:]:
            dftemp = pd.DataFrame()
            dftemp = OECD.loc[simple_II_labels, vector_name].reset_index()
            dftemp.columns = ['sector', vector_name]
            dftemp['country'] = country
            dftemp['year'] = year
            dftemp = dftemp[['country', 'year', 'sector', vector_name]]
            
            # Merge dftemp as a new column into dfother_final_demand
            df1year = df1year.merge(
                dftemp,
                on=['country', 'year', 'sector'],
                how='left'
            )

        dfother_final_demand = pd.concat([dfother_final_demand, df1year], ignore_index=True)
dfother_final_demand['year'] = dfother_final_demand['year'].astype(int)
# checking the big dataframes
# Filter for the specific country and year
#years = range(2019, 2020)
#plot_dffc(dffc, years,  countries)
#sector_name=final_demand_columns[6]
#plot_dfother_final_demand(dfother_final_demand,sector_name, years,  countries)

# switching to one column instead of 6
dfother_final_demand['other final demand'] = dfother_final_demand[final_demand_columns[1:]].sum(axis=1)
dfother_final_demand.drop(columns=final_demand_columns[1:], inplace=True)
# summing over sectors to get one number per country per year
dfftotal = clc_v_tot(dfother_final_demand, 'other final demand', 'other final demand total')
#get gdp data
gdp_filename = "Bench_predictions/gdp_ARIMAgdp_currentUSD04.csv"
gdp_data = pd.read_csv(gdp_filename)
gdp_data.rename(columns={'Unnamed: 0': 'year'}, inplace=True) #renaming the column
gdp_data['year'] = gdp_data['year'].astype(int)
gdp_data.set_index('year', inplace=True) 
#pivotingg gdp_data to long format (to match dfftotal format)
gdp_long = (
    gdp_data
    .reset_index()  # make 'year' a column instead of index
    .melt(id_vars='year', var_name='country', value_name='gdp total')
    .sort_values(['country', 'year'])
    .reset_index(drop=True)
)
# inserting gdp data to dfftotal
dfftotal = dfftotal.merge(
    gdp_long[['country', 'year', 'gdp total']],
    on=['country', 'year'],
    how='left'
)

dfftotal['ratio_f_to_gdp'] = safe_divide_vector(dfftotal['other final demand total'], dfftotal['gdp total'])
# or
#dfftotal['ratio_f_gdp'] = dfftotal['other final demand total'] / dfftotal['gdp total']
# if I'm sure there are no zeros in gdp total

n_years_to_average=10
stats_all = ( #average from 1995 to 2020
    dfftotal
    .groupby("country")["ratio_f_to_gdp"]
    .agg(["mean", "std"])
    .reset_index()
)
stats = ( # overage over n last years
    dfftotal
    .sort_values(["country", "year"])
    .groupby("country")
    .tail(n_years_to_average)  # take last n rows per country
    .groupby("country")["ratio_f_to_gdp"]
    .agg(["mean", "std"])
    .reset_index()
)

dfother_extrap = pd.DataFrame(index=gdp_data.index, columns=gdp_data.columns)
for country in gdp_data.columns:
    mean_value = stats.loc[stats['country'] == country, 'mean'].values[0]
    dfother_extrap[country] = gdp_data[country] * mean_value
#Eextrap is the extrapolation E
plot_v_by_year_1panel(dfother_extrap, countries, 'other final demand [Million USD]', "Extrapolated other final demand by Country")


dfother_extrap_long = (
    dfother_extrap
    .reset_index()
    .melt(id_vars='year', var_name='country', value_name='other final demand total')
)
dfother_extrap_long = dfother_extrap_long[["country", "year", "other final demand total"]]





# last step: replaced extrap with data where data is availabel
dfother_extrap_and_data = dfother_extrap_long.copy()

# Merge the actual data ('dfftotal') on country and year
dfother_extrap_and_data = dfother_extrap_and_data.merge(
    dfftotal[["country", "year", "other final demand total"]],
    on=["country", "year"],
    how="left",
    suffixes=("", " data")
)

# Replace extrapolated values with actual ones where available
dfother_extrap_and_data["other final demand total"] = (
    dfother_extrap_and_data["other final demand total data"]
    .combine_first(dfother_extrap_and_data["other final demand total"])
)
# combine first means: If "other final demand total data" has a non-missing value, it replaces the corresponding value in "other final demand total".

# Drop the temporary column
dfother_extrap_and_data = dfother_extrap_and_data.drop(columns=["other final demand total data"])
dfother_extrap_and_data = dfother_extrap_and_data[['year','country','other final demand total']]


# pivot for plotting
dfother2 = dfother_extrap_and_data.pivot(
    index="year",
    columns="country",
    values="other final demand total"
)
dfother2 = dfother2[dfother_extrap.columns]
plot_v_by_year_1panel(dfother2, countries, 'other final demand [Million USD]', "Extrapolated other final demand by Country")


# print to excel - correct dataframe to print
dfother_extrap_and_data.to_csv("Bench_predictions/dfother_extrap06.csv", index=False)
print("\n \n")

print('\n')
      