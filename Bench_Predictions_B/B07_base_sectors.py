# standartization of data collection
# what I have:
# 1995-2010: OECD II + E extrap
# 2011-2020: OECD II + OECD E
# 2021-2040: Lc extrap, E extrap
# extrap = extrapolated, mainly by gdp data from world bank. there's ARIMA in gdp and linear extrapolation in japan gdp
# https://www.oecd.org/en/data/datasets/input-output-tables.html

#previousely, A07 were only collecting the vectors
# A08 and A09 are the base-extrap parts

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


##########################################         functions       ##########################################
def make_base_v(df,col_name,countries, years_for_base):
    dfbase = pd.DataFrame()  # start with empty DataFrame
    for country in countries:
        f_1country = df[
            (df['country'] == country) & 
            (df['year'].isin(years_for_base))
        ]
        f_country_mean = (
            f_1country
            .groupby(["country", "sector"])[col_name]
            .mean()
            .reset_index()
        )
        #reordering position of HFCE if exists:
        f_country_mean = f_country_mean.set_index("sector")
        if "HFCE" in f_country_mean.index:
            # Move 'HFCE' to the end
            hfce_row = f_country_mean.loc[["HFCE"]]
            f_country_mean = f_country_mean.drop("HFCE")
            f_country_mean = pd.concat([f_country_mean, hfce_row])
        # Move sector back to a column
        f_country_mean = f_country_mean.reset_index()

        # Reorder columns
        first_cols = ["country", "sector"]
        f_country_mean = f_country_mean[[c for c in first_cols if c in f_country_mean.columns] +
                                        [c for c in f_country_mean.columns if c not in first_cols]]
        dfbase = pd.concat([dfbase, f_country_mean], ignore_index=True)

    return dfbase


def get_mask(df, country, year):
            return (df["country"] == country) & (df["year"] == year)



#from base to sectors using tot
def base_to_sectors(df_base, df_tot, var_name, cols_list, countries, year_range_future):
    df_extrap = pd.DataFrame()
    for country in countries:
        for year in year_range_future:
            dftemp = pd.DataFrame()  # create a new temp DataFrame each iteration

            # select base for country
            base_1country = df_base[df_base.country == country].copy()
            base_1country.drop(columns=["country"], inplace=True)
            base_1country = base_1country.set_index("sector")

            # ftot_value is the total value comes from extrapolation
            ftot_value = df_tot[(df_tot.country == country) & (df_tot.year == int(year))][var_name+" total"].values[0]
            #building a dataframe to concatenate with existing data
            dftemp[var_name] = base_1country * ftot_value      
            dftemp[var_name+" total"] = ftot_value
            dftemp[var_name+" sector ratio"] = base_1country
            dftemp["country"] = country
            dftemp["year"] = year
            # reset index to turn sector index into a column
            dftemp.reset_index(inplace=True)
            #reorder columns
            dftemp = dftemp[cols_list]
            # concatenate, continuing the index automatically
            df_extrap = pd.concat([df_extrap, dftemp], axis=0, ignore_index=True)
    return df_extrap



'''
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
'''



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
# dfE already has data until 2040 - base extrapolation already done.

# for base extrapolation
dfTc = pd.read_csv("Bench_predictions_B/B06_dfTc.csv")
dfHFCE = pd.read_csv("Bench_predictions_B/B06_dfHFCE.csv")
df8    = pd.read_csv("Bench_predictions_B/B06_df8.csv")
df9    = pd.read_csv("Bench_predictions_B/B06_df9.csv")
dfGDP  = pd.read_csv("Bench_predictions_B/B06_dfGDP.csv")
dfoutput = pd.read_csv("Bench_predictions_B/B06_dfoutput.csv")
dfGDPj_by_xj = pd.read_csv("Bench_predictions_B/B06_dfGDPj_by_xj.csv")

dfHFCE_tot       = pd.read_csv("Bench_predictions_B/B06_dfHFCE_tot.csv")
df8_tot          = pd.read_csv("Bench_predictions_B/B06_df8_tot.csv")
df9_tot          = pd.read_csv("Bench_predictions_B/B06_df9_tot.csv")
dfGDP_tot        = pd.read_csv("Bench_predictions_B/B06_dfGDP_tot.csv")
dfoutput_tot     = pd.read_csv("Bench_predictions_B/B06_dfoutput_tot.csv") # needed to get future years
dfGDPj_by_xj_tot = pd.read_csv("Bench_predictions_B/B06_dfGDPj_by_xj_tot.csv")



########################################                           parameters                       ##################################################
start_time = time.time()
print("working directory of B07_base_sectors.py is: ",os.getcwd())  # Print the current working directory

table_type = 'TTL' #or'DOM'   
OECD_path = "../Data/" # windows style: r".\\"
if table_type == 'DOM':
    output_filename = '/mnt/c/NavitComputer24/2024_NES/Economics/Textbook_EIA/OECD_salaries/EIA_matrices.xlsx'
    final_demand_columns = ['HFCE',	'NPISH', 'GGFC',	'GFCF',	'INVNT', 'CONS_NONRES', 'EXPO']
elif table_type == 'TTL':
    output_filename = '/mnt/c/NavitComputer24/2024_NES/Economics/Textbook_EIA/OECD_salaries/EIA_TTL_matrices.xlsx'
    final_demand_columns = ['HFCE', 'NPISH', 'GGFC', 'GFCF', 'INVNT', 'DPABR', 'CONS_NONRES', 'EXPO', 'IMPO']

# data years
first_year = 1995 
last_year = 2020  
year_range = [int(year) for year in range(int(first_year), int(last_year) + 1)]
# base years
n_years_for_base = 0
years_for_base = [year for year in range(int(2020)-n_years_for_base, int(2020)+1)]
# future years
max_future_year = dfoutput_tot.year.unique().max()
year_range_future = [int(year) for year in range(int(last_year+1), max_future_year+1)]
#(I don't extrapolate backwards here beacuse the base yyear should be different)
#report_title = f'ICT sectors, {last_year}'
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



# B07.1 calculate Tc base
#########################
if 1:
    # collecting Tc for base
    Tc_base = pd.DataFrame()  # start with empty DataFrame
    for country in countries:
        Tc_1country = dfTc[
            (dfTc['country'] == country) & 
            (dfTc['year'].isin(years_for_base))
        ]
        Tc_country_mean = (
            Tc_1country
            .groupby(["country", "selling_sector", "buying_sector"])["Tc"]
            .mean()
            .reset_index()
        )
        Tc_base = pd.concat([Tc_base, Tc_country_mean], ignore_index=True)
        

# B07.2 calculate all vector bases
####################################
HFCE_base = make_base_v(dfHFCE,"HFCE sector ratio",countries, years_for_base)
f8_base = make_base_v(df8,"8 final demand sector ratio",countries, years_for_base)
f9_base = make_base_v(df9,"9 final demand sector ratio",countries, years_for_base)
GDP_base = make_base_v(dfGDP,"GDP sector ratio",countries, years_for_base)
output_base = make_base_v(dfoutput,"output sector ratio",countries, years_for_base)
GDPj_by_xj_base = make_base_v(dfGDPj_by_xj,"GDPj_by_xj sector ratio",countries, years_for_base)

Tc_base.to_csv(f"Bench_predictions_B/B07_Tc_base_{n_years_for_base+1}years.csv", index=False)
HFCE_base.to_csv(f"Bench_predictions_B/B07_HFCE_base_{n_years_for_base+1}years.csv", index=False)
f8_base.to_csv(f"Bench_predictions_B/B07_f8_base_{n_years_for_base+1}years.csv", index=False)
f9_base.to_csv(f"Bench_predictions_B/B07_f9_base_{n_years_for_base+1}years.csv", index=False)
GDP_base.to_csv(f"Bench_predictions_B/B07_GDP_base_{n_years_for_base+1}years.csv", index=False)
output_base.to_csv(f"Bench_predictions_B/B07_output_base_{n_years_for_base+1}years.csv", index=False)
GDPj_by_xj_base.to_csv(f"Bench_predictions_B/B07_GDPj_by_xj_base_{n_years_for_base+1}years.csv", index=False)
#################################################################################################
#################################################################################################

'''
# check with n_years_for_base=0
for var1, var2 in zip(
    [dfHFCE, df8, df9, dfGDP, dfoutput, dfGDPj_by_xj],
    [HFCE_base, f8_base, f9_base, fGDP_base, output_base, fGDPj_by_xj_base],
):
    # find the column that ends with " sector ratio"
    col_name = [c for c in var1.columns if c.endswith(" sector ratio")][0]

    temp1 = (
        var1[(var1.country == "CAN") & (var1.year == 2020)]
        [["sector", col_name]]
        .reset_index(drop=True)
    )
    temp2 = (
        var2.loc[var2.country == "CAN"][["sector", col_name]]
        .reset_index(drop=True)
    )

    # Align by sector before subtracting
    merged = pd.merge(temp1, temp2, on="sector", suffixes=("_orig", "_base"))
    merged["diff"] = (merged[f"{col_name}_orig"] - merged[f"{col_name}_base"]).round()

    print(f"\n=== Differences for {col_name} ===")
    print(merged[["sector", "diff"]])

#if n_years_for_base=0 I could simply take the data from 2020
'''

#B07.3 unfolding from tot to numbers
#some have employees_compensation some have HFCE at the end

dfHFCE_data_and_extrap = pd.concat([dfHFCE.copy(), base_to_sectors(HFCE_base, dfHFCE_tot, 'HFCE', list(dfHFCE.columns), countries, year_range_future) ], axis=0, ignore_index=True)
df8_data_and_extrap = pd.concat([df8.copy(), base_to_sectors(f8_base, df8_tot, '8 final demand', list(df8.columns), countries, year_range_future) ], axis=0, ignore_index=True)
df9_data_and_extrap = pd.concat([df9.copy(), base_to_sectors(f9_base, df9_tot, '9 final demand', list(df9.columns), countries, year_range_future) ], axis=0, ignore_index=True)
dfGDP_data_and_extrap = pd.concat([dfGDP.copy(), base_to_sectors(GDP_base, dfGDP_tot, 'GDP', list(dfGDP.columns), countries, year_range_future) ], axis=0, ignore_index=True)
dfoutput_data_and_extrap = pd.concat([dfoutput.copy(), base_to_sectors(output_base, dfoutput_tot, 'output', list(dfoutput.columns), countries, year_range_future) ], axis=0, ignore_index=True)
dfGDPj_by_xj_data_and_extrap = pd.concat([dfGDPj_by_xj.copy(), base_to_sectors(GDPj_by_xj_base, dfGDPj_by_xj_tot, 'GDPj_by_xj', list(dfGDPj_by_xj.columns), countries, year_range_future) ], axis=0, ignore_index=True)


#output(HFCE) possibley output(f8) is not zero. it should be zero
#fixe E below
#save to files
#add past years 1975-1995 by extrapolating with 1995

#after I finish this - move to cagrs and gdpimpact graphs?
#delete files I no longer need
#document stages of B version (Later I will need to add things to the flow, document the flow) can I run them as 4 scripts?


print()
#Is this needed?
#I thought we already ahve Esectors
#should I add E
################################################################################################
################################################################################################
# This is the important part of A08
# preparing  for base for all future years
# collecting E for base

dfEbase_temp = dfE[dfE["year"].isin(years_for_E_base)].reset_index(drop=True).copy()
dfEbase_temp["E_tot"] = (dfEbase_temp.groupby(["country", "year"])["Employment"].transform("sum"))
dfEbase_temp["E sector to tot ratio"] = dfEbase_temp.Employment / dfEbase_temp.E_tot
dfEbase_temp.drop(columns=["Employment", "E_tot"], inplace=True)
dfEbase = pd.DataFrame()
for country in countries:
    dfEbase_1country = dfEbase_temp[
        (dfEbase_temp['country'] == country) & 
        (dfEbase_temp['year'].isin(years_for_gdp_base))
    ]
    dfEbase_1country_mean = (
        dfEbase_1country
        .groupby(["country", "sector"])["E sector to tot ratio"]
        .mean()
        .reset_index()
    )
    dfEbase = pd.concat([dfEbase, dfEbase_1country_mean], ignore_index=True)

dfEbase.to_csv("Bench_predictions/A08_dfEbase.csv", index=False)
#dfEbase: 1 country, mean over years, base for later getting Esector from Etot
#################################################################################################
#################################################################################################
















# 1. upload OECD intput-output tables 1995-2020
###############################################   
for country in countries:
    for year in years_for_base:
        print(country, year)
        # data upload
        Tc = (
            dfTc.loc[get_mask(dfTc,country,year)]
            .pivot(index="selling_sector", columns="buying_sector", values="Tc")
            .copy()
        )    
        T = Tc.iloc[:-1,:-1].copy()
        outputc = dfoutput.loc[get_mask(dfoutput, country, year)].copy()
        GDPc = dfGDP.loc[get_mask(dfGDP, country, year)].copy()
        fHFCEc = dfHFCE.loc[get_mask(dfHFCE,country,year)].copy() 
        f8c = df8.loc[get_mask(df8, country, year)].copy()
        f9c = df9.loc[get_mask(df9, country, year)].copy()
        GDPj_by_xjc = dfGDPj_by_xj.loc[get_mask(dfGDPj_by_xj,country,year)].copy()
        E = dfE.loc[get_mask(dfE, country, year)].copy()
        #remove country and year from E and add 0 at the end [employees_compensation, HFCE]=0
        # I do this to E because E doesn't have Etot etc. 
        # dfE already has data until 2040 - base extrapolation already done.
        E.drop(columns=['country','year'], inplace=True)
        E.set_index('sector', inplace=True)
        E.loc["HFCE"] = 0
        






 
        '''
        for GDP impact
        # . calculate multipliers
        #############################
        mo = Ldf.sum(axis=0)                       #dollar's worth of outcome per 1 dollar's worth of new final demand
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
        #sector2market multipliers
        #mo = s2s_mo.sum(axis=0)
        #moc = s2s_moc.sum(axis=0)
        #mh = s2s_mh.sum(axis=0)
        #mhc = s2s_mhc.sum(axis=0)
        #mg = s2s_mg.sum(axis=0)
        #mgc = s2s_mgc.sum(axis=0)


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
        
        # impacts
        # multipliers_by_f returns a vector, and I want a matrix. I need to do the multiplication again
        scale_df_by_series(direct_o, f8c.iloc[:-1]) # , 'Direct output impact' 
        #multipliers_by_f(indirect_o, fcdf[:-1], 'Indirect output impact'),
        #multipliers_by_f(induced_o, fcdf[:-1], 'Induced output impact'),  
        #multipliers_by_f(s2s_moc.iloc[:-1,:-1], fcdf[:-1], 'Total output impact'),
        #multipliers_by_f(direct_h, fcdf[:-1], 'Direct income impact'), 
        #multipliers_by_f(indirect_h, fcdf[:-1], 'Indirect income impact'),
        #multipliers_by_f(induced_h, fcdf[:-1], 'Induced income impact'),  
        #multipliers_by_f(s2s_mhc.iloc[:-1,:-1], fcdf[:-1], 'Total income impact'),
        #multipliers_by_f(direct_g, fcdf[:-1], 'Direct GDP impact'), 
        #multipliers_by_f(indirect_g, fcdf[:-1], 'Indirect GDP impact'),
        #multipliers_by_f(induced_g, fcdf[:-1], 'Induced GDP impact'),  
        #multipliers_by_f(s2s_mgc.iloc[:-1,:-1], fcdf[:-1], 'Total GDP impact'),  
        
             
        dfGDPimpact = get_impacts(dfGDPimpact, direct_g, indirect_g, induced_g, s2s_mgc.iloc[:-1,:-1], GDP, 'national GDP','GDP',country, year )
        dfEimpact   = get_impacts(dfEimpact, direct_h, indirect_h, induced_h, s2s_mhc.iloc[:-1,:-1], E, 'national Employment','Employment',country, year )
        '''
        


end_time = time.time()
print(f"Elapsed time: {(end_time - start_time)/60:.1f} minutes")


