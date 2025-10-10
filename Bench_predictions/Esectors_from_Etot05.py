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



#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@                    main                  @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


# final demand is needed to get L, and L is needed to get the full E for Japan 2020
# japan 2020 has missing sectors and this code fixes it.

#dfE at the beginning is only for 2011-2020 - this is the data E we have.

#  get dfE from input-output tables
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
# final demand is needed to get L, and L is needed to get the full E for Japan 2020
# japan 2020 has missing sectors and this code fixes it.

dfE = pd.DataFrame() # this will hold country, year, buying sector, selling sector, Eimpact
for country in countries:
    for year in year_range:
        
        # I have decided on the format: I'll put GDPimpact in a dfGDPimpact. I need for that the whole impact code
        PPP_or_exch, OECD, simple_II_labels, OECDadditional, sector_description =  data_upload_OECD_salaries(year, currency_exchange_type, table_type, country)
        
        # the following is calculated twice: in data_upload_OECD_salaries and here. I want to leave it here, but I also need it there - do I??
        II = OECD.loc[simple_II_labels, simple_II_labels]
        household_expenditure = OECD.loc[simple_II_labels, 'HFCE']
        other_final_demand = OECD.loc[simple_II_labels, final_demand_columns[1:]] #exluding HFCE - household expenditure
        E           = OECDadditional['employees_compensation'] 
        output      = OECD.loc['OUTPUT', simple_II_labels]

        dfE = collecting_year_country_data_vector(country, year, dfE, E, 'Employment')

    
        # predictions before impacts
        # prediction for 2020 Japan, and Great Britain 2020:
        years_for_average = ['2017', '2018', '2019']
        if ((year == '2020') & (country == 'JPN')):
            avg_employment = dfE[ (dfE.year.isin(years_for_average)) & (dfE.country=='JPN')].groupby('sector')['Employment'].mean()    
            dfE.loc[((dfE['year'] == year) & (dfE.country=='JPN')), 'Employment'] = dfE.loc[((dfE['year'] == year) & (dfE.country=='JPN')), 'sector'].map(avg_employment)
           #plot_E_line_graph(dfE[dfE.country=='JPN'], 'Employment', 'Employment by Sector in Japan by Year')

        if ((year == '2020') & (country == 'GBR')):
            avg_employment = dfE[ (dfE.year.isin(years_for_average)) & (dfE.country=='GBR')].groupby('sector')['Employment'].mean()    
            dfE.loc[((dfE['year'] == year) & (dfE.country=='GBR')), 'Employment'] = dfE.loc[((dfE['year'] == year) & (dfE.country=='GBR')), 'sector'].map(avg_employment)
            #plot_E_line_graph(dfE[dfE.country=='GBR'], 'Employment', 'Employment by Sector in Great Britain by Year')

        ################################################
        # get E sectors for Japan 2020 for all sectors #
        ################################################
        T = safe_divide(II, output)
        Ldf, L_minus_I = clc_L(T)

        IIc = II.copy()
        IIc["HFCE"] = household_expenditure # added a column for closed model
        IIc.loc['employees_compensation'] = OECDadditional['employees_compensation'] #If I wanted a column I would have written IIC['employees_compensation']
        
        if ((year == '2020') & (country == 'JPN')):
            temp = dfE.loc[((dfE['year'] == year) & (dfE.country=='JPN')), 'Employment']
            IIc.loc['employees_compensation'] = \
            dfE.loc[(dfE['year'] == year) & (dfE['country'] == 'JPN'), ['sector', 'Employment']]\
            .set_index('sector').reindex(IIc.columns)['Employment']
            
        if ((year == '2020') & (country == 'GBR')):
            temp = dfE.loc[((dfE['year'] == year) & (dfE.country=='GBR')), 'Employment']
            IIc.loc['employees_compensation'] = \
            dfE.loc[(dfE['year'] == year) & (dfE['country'] == 'GBR'), ['sector', 'Employment']]\
            .set_index('sector').reindex(IIc.columns)['Employment']
            
# to delete:
# get Etotal extrapolation by gdp
dfE10years, _ = clc_v_tot(dfE, 'Employment', 'Etotal')

# from the above I need dfE - this has Esectors
# I alrady have Employment_sector_ratio, this is Esector/Etotal
# so I just need to get an average number for Employment_sector_ratio and multiply by Etot for each country, year
# there needs to be dfEsectors_from_Etot- this is for sectors and extrapolated years

# this is Etot 1995-2040
Etot = pd.read_csv("Bench_predictions/Etotal_multivariate_E_extrap03.csv", index_col=0)

Esector_extrap = pd.DataFrame(columns = ['country', 'year', 'sector', 'Eextrap'])
for country in countries:
     ratios = dfE10years[dfE10years.country==country].groupby('sector')['Employment_sector_ratio'].mean()
     for year in Etot.index:
        vals = ratios * Etot.loc[int(year), country] 
        # Create a temporary DataFrame for this (country, year)
        E1year = pd.DataFrame({
            'country': country,
            'year': year,
            'sector': ratios.index,
            'Eextrap': vals.values
        })
        # Append to the main DataFrame
        Esector_extrap = pd.concat([Esector_extrap, E1year], ignore_index=True) 


# print to csv Esector_extrap.to_csv("Bench_predictions/Esectors_from_Etot05.csv", index=False)


print(Etot.tail())  

# plot by Country
for country in countries:
    subset = Esector_extrap[Esector_extrap['country'] == country]

    # Find the index where year == 2035
    start_idx = subset[subset['year'] == 2035].index.min()

    # Slice from that index onward
    subset_after_2035 = subset.loc[start_idx:]

    plt.figure(figsize=(8, 5))
    plt.plot(subset_after_2035.index, subset_after_2035['Eextrap'], label=country, color='red')

    plt.xlabel('Index')
    plt.ylabel('Eextrap')
    plt.title(f'Eextrap for {country} (from 2035)')
    plt.legend()
    plt.tight_layout()
    plt.show()







