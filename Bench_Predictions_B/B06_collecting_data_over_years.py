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




#for extrapolation - calculating market total
def clc_v_tot(df, value_col, col_tot):
    # add total employment per (country, year)
    df[col_tot] = df.groupby(["country", "year"])[value_col].transform("sum")
    # ratio of sector employment to total
    df[value_col+" sector ratio"] = df[value_col] / df[col_tot]
    dftotal = df[["country", "year", col_tot]].drop_duplicates()
    return df, dftotal

# for extrapolation - calculating ratio with worldbank gdp
def ratio_with_worldbank_gdp(dfv_total, gdp_long, worldbank_gdp_col_name, col_name):
        
    # inserting gdp data to all collected vectors:
    dfv_total = dfv_total.merge(
        gdp_long[['country', 'year', worldbank_gdp_col_name ]],
        on=['country', 'year'],
        how='left'
    )
    dfv_total['ratio_'+col_name+'_to_gdp'] = safe_divide_vector(dfv_total[col_name+' total'], dfv_total[worldbank_gdp_col_name])   
    return dfv_total



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
worldbank_gdp_col_name = "gdp total world bank"
dfgdp_worldbank.rename(columns={"Unnamed: 0": "year","gdp total": worldbank_gdp_col_name}, inplace=True)
dfgdp_worldbank.iloc[:, 1:] = dfgdp_worldbank.iloc[:, 1:] * 10**(-6)
dfgdp_worldbank['year'] = dfgdp_worldbank['year'].astype(int)
dfgdp_worldbank = dfgdp_worldbank.set_index('year')


# upload E
dfE = pd.read_csv("Bench_predictions_B/A05_Esectors_from_Etot05.csv")
dfE.rename(columns={"E": "Employment"}, inplace=True)

######################################################################################################################################################




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
#dfGDPimpact = pd.DataFrame() # this will hold country, year, buying sector, selling sector, GDPimpact
#dfEimpact = pd.DataFrame()
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

        fHFCE    = OECD.loc[simple_II_labels, 'HFCE']
        fHFCE    = fHFCE.rename_axis("sector")
        fother   = OECD.loc[simple_II_labels,final_demand_columns[1:]].sum(axis=1)
        fother   = fother.rename_axis("sector")
        f7       = OECD.loc[simple_II_labels,final_demand_columns].sum(axis=1)
        f7       = f7.rename_axis("sector")
        GDP      = OECD.loc['VALU', simple_II_labels]
        GDP      = GDP.rename_axis("sector")
        output   = OECD.loc['OUTPUT', simple_II_labels]
        output = output.rename_axis("sector")
        # all above vectors are series, not dataframes 
        
        '''
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
        '''

        # 2. calculate L and Lc
        ##########################
        II = OECD.loc[simple_II_labels, simple_II_labels]
        T = safe_divide(II, output)
        #Ldf, L_minus_I = clc_L(T)

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
        #Lcdf, Lc_minus_I = clc_L(Tc)
   
        dfTc    = collect_m(Tc, country, year, 'Tc', dfTc)
        fHFCEc  = fHFCE.copy();   fHFCEc.loc['employees_compensation'] = 0  #should tis be sum(E)?
        fotherc = fother.copy(); fotherc.loc['employees_compensation'] = 0  
        f7c     = f7.copy();         f7c.loc['employees_compensation'] = 0  
        GDPc    = OECD.loc['VALU', simple_II_labels + ['HFCE']]
        GDPj_by_xjc = safe_divide_vector(GDPc, outputc)
        # collect closed model
        HFCE_col_name = 'HFCE'
        other_col_name = "other final demand"
        f7_col_name = "7 final demand"
        GDP_col_name = 'GDP'
        output_col_name = 'output'
        GDPj_by_xj_col_name = "GDPj_by_xj"
        dfHFCE   = collect_v(fHFCEc,  country, int(year), ['sector', HFCE_col_name], dfHFCE)
        dfother  = collect_v(fotherc,  country, int(year), ['sector', other_col_name], dfother)
        df7      = collect_v(f7c, country, int(year), ['sector', f7_col_name], df7)
        dfGDP    = collect_v(GDPc,    country, int(year), ['sector', GDP_col_name],    dfGDP)
        dfoutput = collect_v(outputc, country, int(year), ['sector', output_col_name], dfoutput)
        dfGDPj_by_xj = collect_v(GDPj_by_xjc,country, int(year), ["sector",GDPj_by_xj_col_name], dfGDPj_by_xj)
        
        #I had a thought to collect all vectors from II and not OECD but it gets complicated. output and GDP must be collected from OECD. so I leave it as is
   
############################################################
# B06.B calculate market total 
############################################################

# to get the ratio of dfother_sector / dfother_tot for data years
dfHFCE, dfHFCE_total = clc_v_tot(dfHFCE, HFCE_col_name, HFCE_col_name+' total')
dfother, dfother_total = clc_v_tot(dfother, other_col_name, other_col_name+' total')
df7, df7_total = clc_v_tot(df7, f7_col_name, f7_col_name+' total')
dfGDP, dfGDP_total = clc_v_tot(dfGDP, GDP_col_name, GDP_col_name+' total')
dfoutput, dfoutput_total = clc_v_tot(dfoutput, output_col_name, output_col_name+' total')
dfGDPj_by_xj, dfGDPj_by_xj_total = clc_v_tot(dfGDPj_by_xj, GDPj_by_xj_col_name, GDPj_by_xj_col_name+' total')

#clc_v_tot is accurate

#print to csv
dfHFCE.to_csv("Bench_predictions_B/B06_dfHFCE.csv", index=False)
dfother.to_csv("Bench_predictions_B/B06_dfother.csv", index=False)
df7.to_csv("Bench_predictions_B/B06_df7.csv", index=False)
dfGDP.to_csv("Bench_predictions_B/B06_dfGDP.csv", index=False)
dfoutput.to_csv("Bench_predictions_B/B06_dfoutput.csv", index=False)
dfGDPj_by_xj.to_csv("Bench_predictions_B/B06_dfGDPj_by_xj.csv", index=False)



# to get the ratio dfother_total / gdp_total for each extrap year
##################################################
#B06.C extrapolating of fother_tot with gdp_tot
##################################################
#pivoting gdp_data to long format (to match dfftotal format)
gdp_long = (
    dfgdp_worldbank
    .reset_index()  # make 'year' a column instead of index
    .melt(id_vars='year', var_name='country', value_name=worldbank_gdp_col_name)
    .sort_values(['country', 'year'])
    .reset_index(drop=True)
)
# this is a side stpe, to see that roughly OECD gdp is 90% of world bank gdp
OECD_worldbank_ratio = (dfGDP_total.merge(gdp_long,
                      on=["country", "year"],)
    .assign(ratio=lambda x: x["GDP total"] / x[worldbank_gdp_col_name])
)
#

dfHFCE_total = ratio_with_worldbank_gdp(dfHFCE_total, gdp_long, worldbank_gdp_col_name, HFCE_col_name)
dfother_total = ratio_with_worldbank_gdp(dfother_total, gdp_long, worldbank_gdp_col_name, other_col_name)
df7_total = ratio_with_worldbank_gdp(df7_total, gdp_long, worldbank_gdp_col_name, f7_col_name)
dfGDP_total = ratio_with_worldbank_gdp(dfGDP_total, gdp_long, worldbank_gdp_col_name, GDP_col_name)
dfoutput_total = ratio_with_worldbank_gdp(dfoutput_total, gdp_long, worldbank_gdp_col_name, output_col_name)
dfGDPj_by_xj_total = ratio_with_worldbank_gdp(dfGDPj_by_xj_total, gdp_long, worldbank_gdp_col_name, GDPj_by_xj_col_name)


#so far it is just the ratio. I still need the extrapolation!!


####################################
#B06.D  fother_sector / fother_tot
####################################
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