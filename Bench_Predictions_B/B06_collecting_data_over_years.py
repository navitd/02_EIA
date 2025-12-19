# B06 data collection for prediction and extrapolation (not for graphs)

# B version
##########################
# 
# B06 collect data 1995-2020: fHFCE, fother, Tc, output, GDPj_by_xj and everything else I may need later
# 
# the problem: need separate functions for Tc and vectors
# another problem: need different names so that not confused with data colelction for graphs
# harmonise: years are numbers not strings
# decided series or dataframes ( prefer dataframes it comes out series) for all vectors
# 
#collect also tot for everything. tot meaning summation over sectors to get vtot
#no need to do this with T

#
# run again to save to files - 1995-2020
# fixed_sectors should be changed when switching to DOM
#for future:
# Lcdf * df8 and Ldf*df9 give output

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


#summing v_tot without compensation of employees or HFCE
def clc_v_tot(df, value_col, col_tot, simple_II_labels):
    # total only over selected labels
    df_tot = (
        df[df["sector"].isin(simple_II_labels)]
        .groupby(["country", "year"])[value_col]
        .sum()
        .reset_index()
        .rename(columns={value_col: col_tot})
    )
    # merge total back
    df = df.merge(df_tot, on=["country", "year"], how="left")
    #  ratio
    df[value_col + " sector ratio"] = df[value_col] / df[col_tot]
    return df, df_tot


# for extrapolation - calculating ratio with worldbank gdp
def ratio_with_worldbank_gdp(dfv_total, gdp_long, worldbank_gdp_col_name, col_name):
        
    # inserting gdp data to all collected vectors:
    dfv_total = dfv_total.merge(
        gdp_long[['country', 'year', worldbank_gdp_col_name ]],
        on=['country', 'year'],
        how='left'
    )
    ratio_col_name = 'ratio of '+col_name+' to gdp'
    dfv_total[ratio_col_name] = safe_divide_vector(dfv_total[col_name+' total'], dfv_total[worldbank_gdp_col_name])   
    return dfv_total, ratio_col_name



def slice_v_from_bigdf(bigdf, country, year):
    # assuming bigdf was prepared by collect_v: columns are country, year, sector, value_column
    v = bigdf[(bigdf.country==country) & (bigdf.year==int(year))].copy()
    #remove country and year from E and add 0 at the end [employees_compensation, HFCE]=0
    v.drop(columns=['country','year'], inplace=True)
    v.set_index('sector', inplace=True)
    return v


#################### compare outputs
#multipliers2prediction(Ldf, f7, "predicted output") and Ldf@f are equivalent
#below change variables names to generic names
def multipliers2prediction(s2s_mo, fdf_year2, column_name):
    predicted_output_year2_np  = np.round(s2s_mo.to_numpy() @ fdf_year2.values.reshape(-1, 1), 1)
    
    predicted_output_year2 = pd.DataFrame(predicted_output_year2_np, index=s2s_mo.index, columns=[column_name])
    
    return predicted_output_year2



############# extrap and data tot2extrap most important step for this file

def tot2future_by_gdp_extrapolation(dfv_total, col_name, ratio_col_name, n_for_tot2future, dfgdp_worldbank):
    #averaging over the ratio to form the base for the extrapolation
    stats = ( # overage over n_for_tot2future last years
        dfv_total
        .sort_values(["country", "year"])
        .groupby("country")
        .tail(n_for_tot2future+1)  # take last n_for_tot2future+1 rows per country
        .groupby("country")[ratio_col_name]
        .agg(["mean", "std"])
        .reset_index()
    )
    # dfv_extrap is the tot for future years
    dfv_extrap = pd.DataFrame(index=dfgdp_worldbank.index, columns=dfgdp_worldbank.columns)
    for country in dfgdp_worldbank.columns:
        mean_value = stats.loc[stats['country'] == country, 'mean'].values[0]
        dfv_extrap[country] = dfgdp_worldbank[country] * mean_value

    dfv_extrap_long = (
        dfv_extrap
        .reset_index()
        .melt(id_vars='year', var_name='country', value_name=col_name+' total')
    )
    dfv_extrap_long = dfv_extrap_long[["country", "year", col_name+' total']]

    # compare in the above to 2020 and 2021 data
   
    # last step: replace extrap with data where data is availabel
    dfv_extrap_and_data = dfv_extrap_long.copy()

    # Merge the actual data ('dfftotal') on country and year
    dfv_extrap_and_data = dfv_extrap_and_data.merge(
        dfv_total[["country", "year", col_name+" total"]],
        on=["country", "year"],
        how="left",
        suffixes=("", " data")
    )

    # Replace extrapolated values with actual ones where available
    dfv_extrap_and_data[col_name+" total"] = (
        dfv_extrap_and_data[col_name+" total data"]
        .combine_first(dfv_extrap_and_data[col_name+" total"])
    )
    # combine first means: If "other final demand total data" has a non-missing value, it replaces the corresponding value in "other final demand total".

    # Drop the temporary column
    dfv_extrap_and_data = dfv_extrap_and_data.drop(columns=[col_name+" total data"])
    dfv_extrap_and_data = dfv_extrap_and_data[['year','country',col_name+' total']]

    # pivot for plotting
    dfv_wide = dfv_extrap_and_data.pivot(
        index="year",
        columns="country",
        values=col_name+" total"
    )
    dfv_wide = dfv_wide[dfv_extrap.columns]
    return dfv_extrap_and_data, dfv_wide

################################################                  plotting                ###########################################################

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
#to run for saving files:
#1. TTL 
#3. 1995-2020
#2. change if 0 to if 1 in 2 places

########################################################################################################################################################
table_type = 'TTL' #or'DOM'   
OECD_path = "../Data/" # windows style: r".\\"
if table_type == 'DOM':
    output_filename = '/mnt/c/NavitComputer24/2024_NES/Economics/Textbook_EIA/OECD_salaries/EIA_matrices.xlsx'
    final_demand_columns = ['HFCE',	'NPISH', 'GGFC',	'GFCF',	'INVNT', 'CONS_NONRES', 'EXPO']
elif table_type == 'TTL':
    output_filename = '/mnt/c/NavitComputer24/2024_NES/Economics/Textbook_EIA/OECD_salaries/EIA_TTL_matrices.xlsx'
    final_demand_columns = ['HFCE', 'NPISH', 'GGFC', 'GFCF', 'INVNT', 'DPABR', 'CONS_NONRES', 'EXPO', 'IMPO']

first_year = '1995'
last_year = '2020'
year_range = [str(year) for year in range(int(first_year), int(last_year) + 1)]
n_for_tot2future=0 # all tots: output, f, GDP, GDPj_by_xj
years_for_f_base = [year for year in range(int(2020)-n_for_tot2future, int(2020)+1)]
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

dfoutput = pd.DataFrame() # this will hold output by country, year, sector, output
dfGDP = pd.DataFrame() # this will hold the GDP by country, year, sector, GDP
#dfGDPimpact = pd.DataFrame() # this will hold country, year, buying sector, selling sector, GDPimpact
#dfEimpact = pd.DataFrame()
dfTc = pd.DataFrame()
dfGDPj_by_xj= pd.DataFrame()
dfHFCE = pd.DataFrame()
df8 = pd.DataFrame()
df9 = pd.DataFrame()
for country in countries:
    for year in year_range:
        
        E = slice_v_from_bigdf(dfE, country, year)
        E.loc["HFCE"] = 0

        # I have decided on the format: I'll put GDPimpact in a dfGDPimpact. I need for that the whole impact code
        PPP_or_exch, OECD, simple_II_labels =  data_upload_OECD_without_E(year, currency_exchange_type, table_type, country)

        fHFCE    = OECD.loc[simple_II_labels, 'HFCE']
        fHFCE    = fHFCE.rename_axis("sector")
        f8       = OECD.loc[simple_II_labels,final_demand_columns[1:]].sum(axis=1)
        f8       = f8.rename_axis("sector")
        f9       = OECD.loc[simple_II_labels,final_demand_columns].sum(axis=1)
        f9       = f9.rename_axis("sector")
        GDP      = OECD.loc['VALU', simple_II_labels]
        GDP      = GDP.rename_axis("sector")
        output   = OECD.loc['OUTPUT', simple_II_labels]
        output = output.rename_axis("sector")
        # all above vectors are series, not dataframes 
        
        #checking data collection
        '''
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
        Ldf, L_minus_I = clc_L(T)
        #check EIA:
        #xcheck = multipliers2prediction(Ldf, f9, "predicted output")
        #xcheck2 = Ldf@f9 #This multiplication works here because all row names are the same
        #diff = (xcheck.sub(output, axis=0)).abs()
        #print(diff)
        #print(pd.concat([output,xcheck, xcheck2],axis=1))

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
        #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        if 0: #I removed it from the above, so probably should delete
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
            
        

              
        dfTc = collecting_year_country_data_matrix(country, year, dfTc, Tc, 'Tc')

        
        # 3. calculate multipliers
        #############################
        mo = Ldf.sum(axis=0)                       #dollar's worth of outcome per 1 dollar's worth of new final demand
        moc_trancated = Lcdf.iloc[:-1].sum(axis=0) #dollar's worth of outcome per 1 dollar's worth of new final demand

        # income multipliers mh
        Ej_by_xj = Tc.iloc[-1,:-1] #hosehold income received per dollar's worth of sector output  
        income_F_multipliers = Ldf.mul(Ej_by_xj, axis=0) #household income recieved per dollar's worth of secotr final demand
        # Ej/xj*Ljk - Ljk is how much output was sold from j to k. and j is the sector that paid the salaries, so Ej/xj is used.
        sum_income_F_multipliers = income_F_multipliers.sum(axis=0) 
        

        #income multipliers second time
        Ej_by_xj = Tc.iloc[-1,:]
        
        # GDP multipliers
        GDPc = OECD.loc['VALU', simple_II_labels + ['HFCE']]
        GDPj_by_xj = safe_divide_vector(GDPc, outputc)

        # summary of multipliers without typeI and typeII - 
        # 6 multipliers output, income, GDP, X sector2sector X simple model, closed model
        # all of the closed model multipliers are trancated (the row and column of salaries and final demand are not included)
        s2s_mo = Ldf                       # direct + indirect effect
        s2s_moc = Lcdf                     # direct + indirect + iduced effect
        s2s_mh = Ldf.mul(Ej_by_xj.iloc[ :-1 ], axis=0) 
        s2s_mhc = Lcdf.mul(Ej_by_xj.rename(index={'HFCE': 'employees_compensation'}), axis=0)
        s2s_mg =  Ldf.mul(GDPj_by_xj.iloc[ :-1 ], axis=0)    
        s2s_mgc = Lcdf.mul(GDPj_by_xj.rename(index={'HFCE': 'employees_compensation'}), axis=0)
        


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

        #################################
        # impacts instead of multipliers
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

        dfGDPimpact = get_impacts(dfGDPimpact, direct_g, indirect_g, induced_g, s2s_mgc.iloc[:-1,:-1], GDP, 'national GDP','GDP',country, year )
        dfEimpact   = get_impacts(dfEimpact, direct_h, indirect_h, induced_h, s2s_mhc.iloc[:-1,:-1], E, 'national Employment','Employment',country, year )
        






        #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        dfTc    = collect_m(Tc, country, int(year), 'Tc', dfTc)
        fHFCEc  = fHFCE.copy(); fHFCEc.loc['employees_compensation'] = 0  #should this be sum(E)?
        f8c     = f8.copy();    f8c.loc['employees_compensation'] = 0  
        f9c     = f9.copy();    f9c.loc['employees_compensation'] = 0  
        GDPc    = OECD.loc['VALU', simple_II_labels + ['HFCE']]
        GDPj_by_xjc = safe_divide_vector(GDPc, outputc)
        # collect closed model
        HFCE_col_name = 'HFCE'
        f8_col_name = "8 final demand"
        f9_col_name = "9 final demand"
        GDP_col_name = 'GDP'
        output_col_name = 'output'
        GDPj_by_xj_col_name = "GDPj_by_xj"
        dfHFCE   = collect_v(fHFCEc,  country, int(year), ['sector', HFCE_col_name], dfHFCE)
        df8      = collect_v(f8c,     country, int(year), ['sector', f8_col_name], df8)
        df9      = collect_v(f9c,     country, int(year), ['sector', f9_col_name], df9)
        dfGDP    = collect_v(GDPc,    country, int(year), ['sector', GDP_col_name],    dfGDP)
        dfoutput = collect_v(outputc, country, int(year), ['sector', output_col_name], dfoutput)
        dfGDPj_by_xj = collect_v(GDPj_by_xjc,country, int(year), ["sector",GDPj_by_xj_col_name], dfGDPj_by_xj)
        

        #check:
        #xcheck = multipliers2prediction(Lcdf, f8c, "predicted output")
        #diff = (xcheck.sub(outputc, axis=0)).abs()
        #print('difference between Lcdf#f8c and outputc\n',diff)
        #print('                  outputc     Lcdf@ftestc\n',pd.concat([outputc, xcheck],axis=1))
        #print()

        # Lcdf * df8 and Ldf*df9 give output
        #I had a thought to collect all vectors from II and not OECD but it gets complicated. output and GDP must be collected from OECD. so I leave it as is
       

############################################################
# B06.B calculate market total 
############################################################

# to get the ratio of dfother_sector / dfother_tot for data years, and also dfv_total
dfHFCE, dfHFCE_total = clc_v_tot(dfHFCE, HFCE_col_name, HFCE_col_name+' total',simple_II_labels)
df8, df8_total = clc_v_tot(df8, f8_col_name, f8_col_name+' total',simple_II_labels)
df9, df9_total = clc_v_tot(df9, f9_col_name, f9_col_name+' total',simple_II_labels)
dfGDP, dfGDP_total = clc_v_tot(dfGDP, GDP_col_name, GDP_col_name+' total',simple_II_labels)
dfoutput, dfoutput_total = clc_v_tot(dfoutput, output_col_name, output_col_name+' total',simple_II_labels)
dfGDPj_by_xj, dfGDPj_by_xj_total = clc_v_tot(dfGDPj_by_xj, GDPj_by_xj_col_name, GDPj_by_xj_col_name+' total',simple_II_labels)

#clc_v_tot is accurate

#print to csv
# there is another printing below for the full run of the program
if 1:
    dfTc.to_csv("Bench_predictions_B/B06_dfTc.csv", index=False)
    dfHFCE.to_csv("Bench_predictions_B/B06_dfHFCE.csv", index=False)
    df8.to_csv("Bench_predictions_B/B06_df8.csv", index=False)
    df9.to_csv("Bench_predictions_B/B06_df9.csv", index=False)
    dfGDP.to_csv("Bench_predictions_B/B06_dfGDP.csv", index=False)
    dfoutput.to_csv("Bench_predictions_B/B06_dfoutput.csv", index=False)
    dfGDPj_by_xj.to_csv("Bench_predictions_B/B06_dfGDPj_by_xj.csv", index=False)



# to get the ratio dfother_total / gdp_total for each extrap year
##################################################
#B06.C extrapolating of fother_tot with gdp_tot
##################################################
#pivoting dfgdp_worldbank to long format (to match dfftotal format)
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

dfHFCE_total, ratio_col_name_HFCE = ratio_with_worldbank_gdp(dfHFCE_total, gdp_long, worldbank_gdp_col_name, HFCE_col_name)
df8_total, ratio_col_name_f8 = ratio_with_worldbank_gdp(df8_total, gdp_long, worldbank_gdp_col_name, f8_col_name)
df9_total, ratio_col_name_f9 = ratio_with_worldbank_gdp(df9_total, gdp_long, worldbank_gdp_col_name, f9_col_name)
dfGDP_total, ratio_col_name_GDP = ratio_with_worldbank_gdp(dfGDP_total, gdp_long, worldbank_gdp_col_name, GDP_col_name)
dfoutput_total, ratio_col_name_output = ratio_with_worldbank_gdp(dfoutput_total, gdp_long, worldbank_gdp_col_name, output_col_name)
dfGDPj_by_xj_total, ratio_col_name_GDPj_by_xj = ratio_with_worldbank_gdp(dfGDPj_by_xj_total, gdp_long, worldbank_gdp_col_name, GDPj_by_xj_col_name)

#so far it is just the ratio. I still need the extrapolation!!

####################################
#B06.D  
####################################
# just checking if the extrapolation is reasonable - mean value of fother/gdp don't change much whether it's a mean of 2010-2020 or only 2020
stats_all = ( #average from 1995 to 2020
    dfHFCE_total
    .groupby("country")[ratio_col_name_HFCE]
    .agg(["mean", "std"])
    .reset_index()
)
#

dfHFCE_extrap_and_data, dfHFCE_extrap_and_data_wide = tot2future_by_gdp_extrapolation(dfHFCE_total,HFCE_col_name, ratio_col_name_HFCE,n_for_tot2future,dfgdp_worldbank)
df8_extrap_and_data, df8_extrap_and_data_wide = tot2future_by_gdp_extrapolation(df8_total,f8_col_name, ratio_col_name_f8,n_for_tot2future,dfgdp_worldbank)
df9_extrap_and_data, df9_extrap_and_data_wide = tot2future_by_gdp_extrapolation(df9_total,f9_col_name, ratio_col_name_f9,n_for_tot2future,dfgdp_worldbank)
dfGDP_extrap_and_data, dfGDP_extrap_and_data_wide = tot2future_by_gdp_extrapolation(dfGDP_total,GDP_col_name, ratio_col_name_GDP,n_for_tot2future,dfgdp_worldbank)
dfoutput_extrap_and_data, dfoutput_extrap_and_data_wide = tot2future_by_gdp_extrapolation(dfoutput_total,output_col_name, ratio_col_name_output,n_for_tot2future,dfgdp_worldbank)
dfGDPj_by_xj_extrap_and_data, dfGDPj_by_xj_extrap_and_data_wide = tot2future_by_gdp_extrapolation(dfGDPj_by_xj_total,GDPj_by_xj_col_name, ratio_col_name_GDPj_by_xj,n_for_tot2future,dfgdp_worldbank)


#plot extrapolation
#plot_v_by_year_1panel(df7_extrap_and_data_wide, countries, 'final demand [Million USD]', "Extrapolated other final demand by Country")
#plot_v_by_year_1panel(dfoutput_extrap_and_data_wide, countries, 'output [Million USD]', "Extrapolated output by Country")
#plot_v_by_year_1panel(dfGDP_extrap_and_data_wide, countries, 'GDP [Million USD]', "Extrapolated GDP by Country")

# print to excel - correct dataframe to print
if 1:
    dfHFCE_extrap_and_data.to_csv("Bench_predictions_B/B06_dfHFCE_tot.csv", index=False)
    df8_extrap_and_data.to_csv("Bench_predictions_B/B06_df8_tot.csv", index=False)
    df9_extrap_and_data.to_csv("Bench_predictions_B/B06_df9_tot.csv", index=False)
    dfGDP_extrap_and_data.to_csv("Bench_predictions_B/B06_dfGDP_tot.csv", index=False)
    dfoutput_extrap_and_data.to_csv("Bench_predictions_B/B06_dfoutput_tot.csv", index=False)
    dfGDPj_by_xj_extrap_and_data.to_csv("Bench_predictions_B/B06_dfGDPj_by_xj_tot.csv", index=False)


if 0:
    #checks
    #1. GDPj_by_xj *output = GDP??
    #the above is not true. it's true only for _xj_, not the summing of output

    #2. dfHFCE+dfother = df7??
    #df7check= dfHFCE_extrap_and_data_wide + dfother_extrap_and_data_wide

    #diff = np.abs(df7check - df7_extrap_and_data_wide)
    #diff_ratio = diff/df7_extrap_and_data_wide
    #diff_mean = diff_ratio.mean()

    #mask_years = lambda df: (df.index >= 2010) & (df.index <= 2021) 
    #print('df7check - result of adding HFCE+other')
    #print(df7check[mask_years(df7check)])
    #print(dfHFCE_extrap_and_data_wide[mask_years(dfHFCE_extrap_and_data_wide)])
    #print(dfother_extrap_and_data_wide[mask_years(dfother_extrap_and_data_wide)])

    #print('         HFCE       ', ' other    ', '7 by addition ', '7 from df')
    #print(pd.concat([dfHFCE_extrap_and_data_wide[mask_years(dfHFCE_extrap_and_data_wide)]['CAN'],
    #                 dfother_extrap_and_data_wide[mask_years(dfother_extrap_and_data_wide)]['CAN'],
    #                 df7check[mask_years(df7check)]['CAN'], 
    #                 df7_extrap_and_data_wide[mask_years(df7_extrap_and_data_wide)]['CAN']], axis=1))


    #mask_years = lambda df: (df.index >= 2020) & (df.index <= 2030) 

    #print('         HFCE       ', ' other    ', '7 by addition ', '7 from df')
    #print(pd.concat([dfHFCE_extrap_and_data_wide[mask_years(dfHFCE_extrap_and_data_wide)]['CAN'],
    #                 dfother_extrap_and_data_wide[mask_years(dfother_extrap_and_data_wide)]['CAN'],
    #                 df7check[mask_years(df7check)]['CAN'], 
    #                 df7_extrap_and_data_wide[mask_years(df7_extrap_and_data_wide)]['CAN']], axis=1))


    #
    #check output
    '''
    mask_years = lambda df: (df.index >= 2020) & (df.index <= 2030) 

    print('         HFCE       ', ' other    ', '7 by addition ', '7 from df')
    print(pd.concat([dfHFCE_extrap_and_data_wide[mask_years(dfHFCE_extrap_and_data_wide)]['CAN'],
                    dfother_extrap_and_data_wide[mask_years(dfother_extrap_and_data_wide)]['CAN'],
                    df7check[mask_years(df7check)]['CAN'], 
                    df7_extrap_and_data_wide[mask_years(df7_extrap_and_data_wide)]['CAN']], axis=1))

    '''
    #compare output tot:
    #year = 2020
    #country = 'CAN'
    #output_tot1 = dfoutput_extrap_and_data[(dfoutput_extrap_and_data.year==year) & (dfoutput_extrap_and_data.country==country)]['output total']
    #output_tot2 = dfoutput[(dfoutput.year==year) & (dfoutput.country==country)]["output total"]
    #print('dfoutput_extrap_and_data, dfoutput (sectors)')
    #print( pd.concat([output_tot1.iloc[[0]], output_tot2.iloc[[0]]], axis=0) )


    year = 2018
    country = 'USA'
    Tctemp = (
        dfTc[(dfTc.country == country) & (dfTc.year == year)]
        .pivot(index="selling_sector", columns="buying_sector", values="Tc")
    )
    x = dfoutput[(dfoutput.country == country) & (dfoutput.year == year)].set_index('sector')['output']
    f8temp = df8[(df8.country == country) & (df8.year == year)].set_index('sector')[f8_col_name]
    f8temp.rename(index={"employees_compensation":"HFCE"},inplace=True) 
    f9temp = df9[(df9.country == country) & (df9.year == year)].set_index('sector')[f9_col_name]
    f9temp.rename(index={"employees_compensation":"HFCE"},inplace=True) 
    Tctemp = Tctemp[[c for c in Tctemp.columns if c != 'HFCE'] + ['HFCE']] #put 'HFCE' at the end
    Lctemp,_ = clc_L(Tctemp)
    xcheck = multipliers2prediction(Lctemp, f8temp,'output') #it is important to use this instead of @ because when the row names don't agree the multiplication is inaccurate  
    #Lc shoudl be multilied by f8
    Ltemp,_ = clc_L(Tctemp.iloc[:-1,:-1])
    xcheck2 = Ltemp@f9temp.iloc[:-1]
    print('        xcheck   ',' xcheck2', '   x dfoutput')
    print(pd.concat([xcheck.iloc[:-1].round(), xcheck2.round(), x.iloc[:-1].round() ], axis=1))

    #the following is for when country = JPN and I could compare directly with the run above ()
    #print(' Lcdf from above,    Lctemp from collection\n')
    #print(pd.concat([pd.DataFrame(Lcdf.to_numpy().flatten(), columns=['L']), pd.DataFrame(Lctemp.to_numpy().flatten(), columns=['Ltemp'])], axis=1))
    #print('\n')
    #print('            f8temp    and f9temp from above \n',pd.concat([f8temp,f9temp], axis=1))

    #print(pd.concat([pd.DataFrame(Tc.to_numpy().flatten(), columns=['Tc']), pd.DataFrame(Tctemp.to_numpy().flatten(), columns=['Tctemp'])], axis=1))

    
print('\n')
      
