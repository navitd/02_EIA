# B06 data collection for prediction and extrapolation (not for graphs)

# B version
##########################
# 
# B06 collect data 1995-2020: fHFCE, fother, Tc, output, GDPj_by_xj and everything else I may need later
# save to one file
# the problem: need separate functions for Tc and vectors
# another problem: need different name so that not confused with data colelction for graphs
# harmonise: years are numbers not strings
# decided series or dataframes ( prefer dataframes ) for all vectors
# 
#collect also tot for everything. tot meaning summation over sectors to get vtot
#no need to do this with T

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
from func_data_upload_OECD_without_E import data_upload_OECD_without_E #data_upload_OECD_salaries func_data_upload_OECD_salaries
from func_safe_divide import safe_divide, safe_divide_vector
from func_clc_L import clc_L






################################       collecting data from input-output tables      #########################################
def collect_v(v, country, year, cols_list, dfv): # used to be collecting_year_country_data_vector
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


def clc_v_tot(df, value_col, col_tot):
    # add total employment per (country, year)
    df[col_tot] = df.groupby(["country", "year"])[value_col].transform("sum")
    # ratio of sector employment to total
    df[value_col+" sector ratio"] = df[value_col] / df[col_tot]
    dftotal = df[["country", "year", col_tot]].drop_duplicates()
    return df, dftotal


def slice_v_from_bigdf(bigdf, country, year):
    # assuming bigdf was prepared by collect_v: columns are country, year, sector, value_column
    v = bigdf[(bigdf.country==country) & (bigdf.year==int(year))].copy()
    #remove country and year from E and add 0 at the end [employees_compensation, HFCE]=0
    v.drop(columns=['country','year'], inplace=True)
    v.set_index('sector', inplace=True)
    return v




#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@                    main                  @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# upload gdp
dfgdp_worldbank = pd.read_csv("Bench_predictions_B/A04_gdp_ARIMAgdp_currentUSD04.csv")
dfgdp_worldbank.rename(columns={"Unnamed: 0": "year"}, inplace=True)
dfgdp_worldbank.iloc[:, 1:] = dfgdp_worldbank.iloc[:, 1:] * 10**(-6)
dfgdp_worldbank = dfgdp_worldbank.set_index('year')

# upload E
dfE = pd.read_csv("Bench_predictions_B/A05_Esectors_from_Etot05.csv")
dfE.rename(columns={"E": "Employment"}, inplace=True)












table_type = 'TTL' #or'DOM'   
OECD_path = "../Data/" # windows style: r".\\"
if table_type == 'DOM':
    output_filename = '/mnt/c/NavitComputer24/2024_NES/Economics/Textbook_EIA/OECD_salaries/EIA_matrices.xlsx'
elif table_type == 'TTL':
    output_filename = '/mnt/c/NavitComputer24/2024_NES/Economics/Textbook_EIA/OECD_salaries/EIA_TTL_matrices.xlsx'

first_year = '2020'
last_year = '2020'
year_range = [str(year) for year in range(int(first_year), int(last_year) + 1)]
n_for_f=0
years_for_f_base = [year for year in range(int(2020)-n_for_f, int(2020)+1)]
# add this to A09 etc.

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
dfoutput = pd.DataFrame() # this will hold output by country, year, sector, output
dfGDP = pd.DataFrame() # this will hold the GDP by country, year, sector, GDP
dfGDPimpact = pd.DataFrame() # this will hold country, year, buying sector, selling sector, GDPimpact
dfEimpact = pd.DataFrame()
dfTc = pd.DataFrame()
#dfLc = pd.DataFrame()
dfGDPj_by_xj= pd.DataFrame()
#dffc = pd.DataFrame()
dfHFCE = pd.DataFrame()
dfother = pd.DataFrame()
df7 = pd.DataFrame()
for country in countries:
    for year in year_range:
        
        E = slice_v_from_bigdf(dfE, country, year)
        E.loc["HFCE"] = 0

        # I have decided on the format: I'll put GDPimpact in a dfGDPimpact. I need for that the whole impact code
        PPP_or_exch, OECD, simple_II_labels =  data_upload_OECD_without_E(year, currency_exchange_type, table_type, country)

        # the following is calculated twice: in data_upload_OECD_salaries and here. I want to leave it here, but I also need it there - do I??
        II = OECD.loc[simple_II_labels, simple_II_labels]
        fHFCE = OECD.loc[simple_II_labels, 'HFCE']
        fHFCE   = fHFCE.rename_axis("sector")
        fother   = OECD.loc[simple_II_labels,final_demand_columns[1:]].sum(axis=1)
        fother   = fother.rename_axis("sector")
        f7      = OECD.loc[simple_II_labels,final_demand_columns].sum(axis=1)
        f7   = f7.rename_axis("sector")
        GDP         = OECD.loc['VALU', simple_II_labels]
        GDP   = GDP.rename_axis("sector")
        output      = OECD.loc['OUTPUT', simple_II_labels]
        output = output.rename_axis("sector")
        # all above vectors are series, not dataframes 
        # first data collection
        dfHFCE   = collect_v(fHFCE,  country, int(year), ['sector', 'HFCE'], dfHFCE)
        dfother = collect_v(fother,  country, int(year), ['sector', 'other final demand'], dfother)
        dfGDP    = collect_v(GDP,    country, int(year), ['sector', 'GDP'],    dfGDP)
        dfoutput = collect_v(output, country, int(year), ['sector', 'output'], dfoutput)
        df7      = collect_v(f7, country, int(year), ['sector', '7 final demand'], df7)

        #checking data collection
        print(year, country)
        print('fHFCE         fother')
        print(pd.concat([fHFCE, fother,f7], axis=1))

        if isinstance(fHFCE, pd.Series):
            print("This is a Series")
        elif isinstance(fHFCE, pd.DataFrame):
            print("This is a DataFrame")
        else:
            print("This is something else")


        # 2. calculate L and Lc
        ##########################
        T = safe_divide(II, output)
        Ldf, L_minus_I = clc_L(T)

        IIc = II.copy()
        IIc["HFCE"] = fHFCE # added a column for closed model
        # Convert Series to a one-row DataFrame with sectors as columns
        ET = E.T  # .T transposes to make index=0, columns=sectors
        ET.index = ["employees_compensation"]  # name the row
        IIc = pd.concat([IIc, ET], axis=0)
        IIc.loc['employees_compensation', 'HFCE'] = 0 

        outputc = output.copy()
        outputc['HFCE'] = E.sum().values[0]
        Tc = safe_divide(IIc, outputc)
        Lcdf, Lc_minus_I = clc_L(Tc)


        # collect Tc



        # collect GDPj_by_xj
        GDPc = OECD.loc['VALU', simple_II_labels + ['HFCE']] #delete this maybe
        GDPj_by_xj = safe_divide_vector(GDPc, outputc)
        dfGDPj_by_xj = collect_v(GDPj_by_xj,country, year, ["sector","GDPj_by_xj"], dfGDPj_by_xj)
        


        #################################
        # final demand
        #A06.A collecting HFCE, fother 1995-2020 collecting sector information but fother is 1 vector
        #################################
        fdf = OECD.loc[simple_II_labels, final_demand_columns].sum(axis=1)
        fcdf = OECD.loc[simple_II_labels,final_demand_columns].sum(axis=1)
        fcdf.loc['employees_compensation'] = 0             
        #note: dffc collects fcdf - final_demand_columns - all 7 columns
        dffc = collect_v(fcdf, country, year, ['sector', 'final demand'], dffc)
        # the above is for graphs, not for extrapolation!

   
############################################################

dfother_final_demand['year'] = dfother_final_demand['year'].astype(int)

# switching to one column instead of 6
dfother_final_demand['other final demand'] = dfother_final_demand[final_demand_columns[1:]].sum(axis=1)
dfother_final_demand.drop(columns=final_demand_columns[1:], inplace=True)

#A06.B dfother_final_demand has tot
# writing to A06_dfother_final_demand
#####################################
# to get the ratio of dfother_sector / dfother_tot for data years
dfother_final_demand, dfother_total = clc_v_tot(dfother_final_demand, 'other final demand', 'other final demand total')

#print to csv
dfother_final_demand.to_csv("Bench_predictions/A06_dfother_final_demand.csv", index=False)
#dfother_final_demand.columns ['country', 'year', 'sector', 'other final demand','other final demand total', 'other final demand sector ratio']
# up to here: dfother_final_demand calculates tot and sector ratio



# to get the ratio dfother_total / gdp_total for each extrap year
# to get one number of dff per year - for extrapolation
# averaging over sectors to get one number per country per year
#dfftotal = clc_v_tot(dfother_final_demand, 'other final demand', 'other final demand total')
#get gdp data
#A06.D extrapolating of fother_tot with gdp_tot
##############################################
gdp_filename = "Bench_predictions/A04_gdp_ARIMAgdp_currentUSD04.csv"
gdp_data = pd.read_csv(gdp_filename)
gdp_data.rename(columns={'Unnamed: 0': 'year'}, inplace=True) #renaming the column
gdp_data['year'] = gdp_data['year'].astype(int)
gdp_data.set_index('year', inplace=True) 
#pivoting gdp_data to long format (to match dfftotal format)
gdp_long = (
    gdp_data
    .reset_index()  # make 'year' a column instead of index
    .melt(id_vars='year', var_name='country', value_name='gdp total')
    .sort_values(['country', 'year'])
    .reset_index(drop=True)
)
# inserting gdp data to dfftotal
dfother_total = dfother_total.merge(
    gdp_long[['country', 'year', 'gdp total']],
    on=['country', 'year'],
    how='left'
)

dfother_total['ratio_f_to_gdp'] = safe_divide_vector(dfother_total['other final demand total'], dfother_total['gdp total'])
# or
#dfftotal['ratio_f_gdp'] = dfftotal['other final demand total'] / dfftotal['gdp total']
# if I'm sure there are no zeros in gdp total
# dfother_final_demand.columns ['country', 'year', 'sector', 'other final demand', 'other final demand total', 'other final demand sector ratio']
# dfother_total.columns ['country', 'year', 'other final demand total', 'gdp total', 'ratio_f_to_gdp']


#A06.C  fother_sector / fother_tot
##################################
stats_all = ( #average from 1995 to 2020
    dfother_total
    .groupby("country")["ratio_f_to_gdp"]
    .agg(["mean", "std"])
    .reset_index()
)
stats = ( # overage over n_for_f last years
    dfother_total
    .sort_values(["country", "year"])
    .groupby("country")
    .tail(n_for_f+1)  # take last n_for_f+1 rows per country
    .groupby("country")["ratio_f_to_gdp"]
    .agg(["mean", "std"])
    .reset_index()
)
# dfother_extrap is the tot for future years
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
    dfother_total[["country", "year", "other final demand total"]],
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
dfother_extrap_and_data.to_csv("Bench_predictions/A06_dfother_extrap.csv", index=False)


print('\n')
      


'''
      
        # building df1year (also 1 country) first iteration
        I did this because I wantted to collect all 6 other final demand vectors
        but now I don't want that
        vector_name=final_demand_columns[1]
        ftemp = pd.DataFrame()
        dftemp = OECD.loc[simple_II_labels,vector_name].reset_index()
        dftemp.columns = ['sector', vector_name]
        dftemp['country'] = country
        dftemp['year'] = year
        dftemp = dftemp[['country', 'year', 'sector', vector_name]]
        #the line below means that HFCE is in "other final demand"
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
      
      
'''