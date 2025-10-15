# benchmarking - the EIA from print2xls3.py is in a function and I choose sectors, years, calculate compound annual growth rate and plot
# input-output table from OECD
# https://www.oecd.org/en/data/datasets/input-output-tables.html

#I should correct evertying here Time -> year

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
from matplotlib.ticker import MaxNLocator
from matplotlib.lines import Line2D

#from openpyxl import load_workbook, Workbook
#from openpyxl.utils.dataframe import dataframe_to_rows
#from openpyxl.styles import PatternFill, Alignment, Font, Border, Side
#from openpyxl.cell.cell import MergedCell

#scikit-learn imports
from numpy.polynomial import Polynomial
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import Ridge  # or Lasso
from sklearn.pipeline import make_pipeline

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent / 'EIAfunctions'))
from func_data_upload_OECD_salaries import data_upload_OECD_salaries
from func_plot_L import plot_matrix_columns
from func_clc_L import clc_L
from func_safe_divide import safe_divide, safe_divide_vector
from func_multipliers_by_f import multipliers_by_f
from func_plot_real_vs_predicted import plot_real_vs_predicted

from func_clean_world_bank_data import clean_world_bank_data
#there isn't E information 1995-2010 on the OECD site. but Tanveer still wants report 1995-2024




####################################################         functions that Extrapolate       ##################################################
def polynomial_extrapolation_model(data, train_test_split, degree, alpha):
    """
    Polynomial extrapolation with regularization (Ridge/Lasso).
    
    Parameters
    ----------
    data : pd.DataFrame
        Must contain column 'Time' + one or more value columns.
    train_test_split : float
        If < 1, interpreted as fraction of data for training.
        If == 1, all rows are used for training (Xtest empty).
    degree : int
        Degree of polynomial.
    alpha : float
        Regularization strength (Ridge/Lasso). Default = 1.0.
    """
    data = data.astype(float)
    if train_test_split < 1:
        split_index = int(data.shape[0] * train_test_split)
        Xtrain, Xtest = data.iloc[:split_index][['Time']], data.iloc[split_index:][['Time']]
        ytrain, ytest = data.iloc[:split_index].drop(columns=['Time']), data.iloc[split_index:].drop(columns=['Time'])
    else:
        split_index = data.index[-1] + 1    
        Xtrain, Xtest = data.iloc[:split_index][['Time']], data.iloc[split_index:][['Time']]
        ytrain, ytest = data.iloc[:split_index].drop(columns=['Time']), data.iloc[split_index:].drop(columns=['Time'])

    # container for coefficients
    coef = pd.DataFrame()
    
    for col in [c for c in data.columns if c != 'Time']:
        model = make_pipeline(
            PolynomialFeatures(degree=degree, include_bias=True),
            Ridge(alpha=alpha)  # swap with Lasso(alpha=alpha) if desired
        )
        
        model.fit(Xtrain, ytrain[col])
        
        # store coefficients in coeff
        coef_rough = model.named_steps['ridge'].coef_
        intercept = model.named_steps['ridge'].intercept_
        coef[col] = np.concatenate(([intercept], coef_rough[1:]))  # drop bias term handled by intercept

        # predictions for test set
        if not Xtest.empty:
            predictions = model.predict(Xtest)
            data.loc[Xtest.index, f'{col} prediction'] = predictions
    
    # mark prediction rows
    data['prediction flag'] = False
    if not Xtest.empty:
        data.loc[Xtest.index, 'prediction flag'] = True
    
    return data, coef


# this function is used int the next function
#the following deals with both backwardsa and forwards extrapolation
def polynomial_extrapolation(data, train_test_split, degree, steps_forward, steps_back, alpha):
    #building the model - getting coefficients
    data, dfp = polynomial_extrapolation_model(data, train_test_split, degree, alpha) #dfp are the coeff. should change name
    # extrapolation
    back_years = np.arange(data['Time'].min() - steps_back, data['Time'].min()) if steps_back > 0 else np.array([], dtype=int)
    future_years = np.arange(data['Time'].max() + 1, data['Time'].max() + steps_forward + 1)
    extrap_years = np.concatenate([back_years, future_years])

    # Create a DataFrame with 'Time' column and other columns from df_ext, filled with NaN
    additional_rows = pd.DataFrame({
        col: ([np.nan] * (extrap_years) if col != 'Time' else extrap_years)
        for col in data.columns
    })
    additional_rows['prediction flag'] = True  
    data = pd.concat([data.copy(), additional_rows], ignore_index=True)
    data = data.sort_values('Time').reset_index(drop=True)

    for col in [c for c in countries]:
        p_object = Polynomial(dfp[col])  
        predictions = p_object(extrap_years)
        data.loc[ data['Time'].isin(extrap_years), f'{col} prediction'] = predictions
    return data


#the following packages together the pivoting, extrapolation and plotting. two plots - one for test and train and one for teh whoel data points
def package_extrapolation(df, col_name, col_total, train_test_split, degree, steps_forward=5, steps_back=4, alpha=1.0):
    dftotal = pd.DataFrame()
    # add total value_col per (country, year)
    df[col_total] = df.groupby(["country", "year"])[col_name].transform("sum")
    # ratio of sector employment to total
    df[col_name+"sector_ratio"] = df[col_name] / df[col_total]
    dftotal = df[["country", "year", col_total]].drop_duplicates()
    # Pivot the dataframe
    data_for_extrap = dftotal.pivot(index="year", columns="country", values=col_total)
    # Reset index and rename year -> time
    data_for_extrap = data_for_extrap.reset_index().rename(columns={"year": "Time"})

    # plotting the data points and the predictions one over the other
    data_and_prediction = polynomial_extrapolation(data_for_extrap.copy(), train_test_split, degree, steps_forward, steps_back, alpha)
    plot_polynomial_extrapolation(data_and_prediction, countries, title=f'Polinomial Extrapolation of {col_total}, degree={degree}, alpha={alpha}')

    ## actual extrapolation (all data points)
    #train_test_split = 1
    #data_and_prediction2 = polynomial_extrapolation(data_for_extrap.copy(), train_test_split, degree, steps_forward, steps_back, alpha)
    #plot_polynomial_extrapolation(data_and_prediction2, countries, title=f'Polinomial Extrapolation of {col_total}, degree={degree}, alpha={alpha}')
    return df, dftotal, data_and_prediction 

# all three functions above are used in forawrd extrapolation

# 10.b. extrapolation by gdp
def clc_v_tot(df, value_col, col_tot):
    # add total employment per (country, year)
    df[col_tot] = df.groupby(["country", "year"])[value_col].transform("sum")
    # ratio of sector employment to total
    df[value_col+"_sector_ratio"] = df[value_col] / df[col_tot]
    dftotal = df[["country", "year", col_tot]].drop_duplicates()
    return df, dftotal


def compute_E_G_ratio(dfEtotal, worldbank_gdp_data,countries, year_range):
    
    # Initialize output with same structure
    dfE_G_ratio = pd.DataFrame(index=year_range, columns=worldbank_gdp_data.columns[1:])
    
    # Loop through each country column (skip 'Time')
    for country in countries:
        for year in year_range:
            if int(year) not in worldbank_gdp_data.index:
                raise ValueError(f"Year {year} not found in worldbank_gdp_data.")
            
            gdp_temp = worldbank_gdp_data[worldbank_gdp_data.index == int(year)][country].values[0]
            if gdp_temp == 0:
                raise ValueError(f"GDP value for country {country} in year {year} is zero, cannot compute ratio.")
            else: 
                 ratio= dfEtotal[  (dfEtotal.year==year) & (dfEtotal.country== country)].Etotal.values[0] / gdp_temp
                 dfE_G_ratio.loc[ year, country] = ratio
    return dfE_G_ratio
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

def collecting_year_country_data_vector(country, year, dfv, v, vector_name):
            dftemp = pd.DataFrame()
            dftemp = v.reset_index()
            dftemp.columns = ['sector', vector_name]
            dftemp['country'] = country
            dftemp['year'] = year
            dftemp = dftemp[['country', 'year', 'sector', vector_name]]
            dfv = pd.concat([dfv, dftemp], ignore_index=True)
            return dfv
################################################         functions that plot              ######################################################

def plot_E_line_graph(JPNE, col_name, title):
    years = sorted(JPNE['year'].unique())
    num_years = len(years)

    # Generate colors from red to purple using the 'rainbow' colormap
    colors = cm.rainbow(np.linspace(0, 1, num_years))

    plt.figure(figsize=(14, 6))

    for i, year in enumerate(years):
        data = JPNE[JPNE['year'] == year]
        plt.plot(data['sector'], data['Employment'], label=str(year), color=colors[i])

    plt.xlabel('Sector')
    plt.ylabel(col_name)
    plt.title(title)
    plt.xticks(rotation=90)
    plt.legend(title='Year')
    plt.tight_layout()
    plt.show()

def plot_Tc(dfTc, plot_sec):

    df_plot = dfTc[dfTc['buying_sector'] == plot_sec]

    if df_plot.empty:
        print(f"No data found for buying sector '{plot_sec}'.")
        return

    countries = sorted(df_plot['country'].unique())
    n_countries = len(countries)

    # Set up subplots: one row per country
    fig, axes = plt.subplots(n_countries, 1, figsize=(12, 4 * n_countries), sharex=True)

    if n_countries == 1:
        axes = [axes]  # make axes iterable

    for ax, country in zip(axes, countries):
        df_country = df_plot[df_plot['country'] == country]
        for year in sorted(df_country['year'].unique()):
            data = df_country[df_country['year'] == year]
            ax.plot(data['selling_sector'], data['Tc'], label=str(year))
        
        ax.set_title(f'{country}')
        ax.set_ylabel('Tc Value')
        ax.legend(title='Year')
        ax.tick_params(axis='x', rotation=90)

    axes[-1].set_xlabel('Selling Sector')  # label only bottom panel
    fig.suptitle(f"Tc Values for Buying Sector '{plot_sec}'", fontsize=14)
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plt.show()


def plot_subplots_vector_by_country(df, col_name, title=None):
    countries = df.country.unique()
    fig, axes = plt.subplots(7, 1, figsize=(12, 14), sharex=True)

    for i, country in enumerate(countries):
        ax = axes[i]
        df_country = df[df['country'] == country]
        years = sorted(df_country['year'].unique())
        
        cmap = cm.get_cmap('rainbow', len(years))  # Get rainbow colormap with n colors

        for j, year in enumerate(years):
            data = df_country[df_country['year'] == year]
            ax.plot(data['sector'], data[col_name], label=str(year), color=cmap(j))
        
        ax.set_title(country, fontsize=10)
        ax.set_ylabel(col_name)
        ax.legend(title='Year', fontsize=8)
        ax.tick_params(axis='x', rotation=90)

    axes[-1].set_xlabel('Sector')
    fig.suptitle(title or f'{col_name} by Sector in G7 Countries', fontsize=14)
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plt.show()


#used for extrapolation and for looking at the data
def plot_polynomial_extrapolation(data, countries, title):
    plotstr1 = 'o-'
    plotstr2 = '^-'
    #countries = data.drop(['Time', 'prediction flag'], axis=1)
    fig, axes = plt.subplots(nrows=len(countries), ncols=1, figsize=(10, 10), sharex=True)

    if 'prediction flag' in data.columns:

        for i, country in enumerate(countries):
            
            pred_mask = data['prediction flag'] == True

            #plot original data in blue
            axes[i].plot(data['Time'], data[country], plotstr1, color='tab:blue')
           
            axes[i].plot(data['Time'][pred_mask], data[f'{country} prediction'][pred_mask], plotstr2, color='tab:red')

            axes[i].set_title(country, loc='left', fontsize=10, pad=5)
            axes[i].set_ylabel('GDP', rotation=0, labelpad=30)
            axes[i].yaxis.set_major_locator(MaxNLocator(nbins=3, prune='both'))
            axes[i].grid(True)

    else:
        for i, country in enumerate(countries.columns):
            axes[i].plot(data['Time'], data[country], plotstr1, label=country, color='tab:blue')
            axes[i].set_title(country, loc='left', fontsize=10, pad=5)
            axes[i].set_ylabel('GDP', rotation=0, labelpad=30)
            axes[i].yaxis.set_major_locator(MaxNLocator(nbins=3, prune='both'))
            axes[i].grid(True)

    axes[-1].set_xlabel('Year')
    fig.suptitle(title, fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    # Create custom legend handles
    legend_handles = [
    Line2D([0], [0], color='tab:blue', marker=plotstr1[0], linestyle='-', label='Data'),
    Line2D([0], [0], color='tab:red', marker=plotstr2[0], linestyle='-', label='Prediction')
        ]

    # Add a single legend for the whole figure
    fig.legend(handles=legend_handles, loc='upper right', fontsize=10, frameon=False)

    plt.show()

def plot_v_by_year_1panel(df, countries, ylabel, title):
    plt.figure(figsize=(10,6))

    for country in df.columns:
        plt.plot(df.index, Eextrap[country], marker='o', label=country)

    plt.xlabel("Year")
    plt.ylabel(ylabel + " [Millions USD]")
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.show()


#################################################### uploading WorldBank data    ##################################################

def get_worldbank_gdp_data(plot_flag):

    # Define the data directory relative to the script location
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    GDP_filename = os.path.join(SCRIPT_DIR, '..', '..', 'Data', 'World Bank G7 GDP', 
                            'cb6272d5-797d-4d20-970a-1286e5b13605_Data.csv')
    #Data from database: World Development Indicators
    #Last Updated: 07/01/2025

    # Add error handling for file loading

    if not os.path.exists(GDP_filename):
        raise FileNotFoundError(f"Data file not found at: {GDP_filename}")

    rough = pd.read_csv(GDP_filename)
    print(f"Successfully loaded data with shape: {rough.shape}")
        
    worldbank_gdp_data, file_description = clean_world_bank_data(rough)

    print("\n dataframe data:\n")
    print(worldbank_gdp_data.head())

    # Plotting
    if plot_flag:
        countries = data.columns[1:]  # all country columns
        plt.figure(figsize=(10, 6))

        for country in countries:
            plt.plot(data['Time'], data[country], marker = 'o',label=country)
            plt.text(data['Time'].iloc[-1], data[country].iloc[-1], country, 
                    fontsize=9, verticalalignment='center')

        plt.xlabel('Year')
        plt.ylabel(file_description[2])  
        plt.title('file_description[2] of countries')
        plt.grid(True)
        plt.legend()  
        plt.show()

        # Trending
        max_data_years = data.Time.max()
        past_years = 10


    return worldbank_gdp_data









#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@                    main                  @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
start_time = time.time()
print("working directory of GDPsupplychain.py is: ",os.getcwd())  # Print the current working directory

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

dfoutput = pd.DataFrame() # this will hold output by country, year, sector, output
dfGDP = pd.DataFrame() # this will hold the GDP by country, year, sector, GDP
dfGDPimpact = pd.DataFrame() # this will hold country, year, buying sector, selling sector, GDPimpact
dfE = pd.DataFrame() # this will hold country, year, buying sector, selling sector, Eimpact
dfEimpact = pd.DataFrame()
dffc = pd.DataFrame()
dfother_final_demand = pd.DataFrame()
dfTc = pd.DataFrame()
for country in countries:
    for year in year_range:
        
        # I have decided on the format: I'll put GDPimpact in a dfGDPimpact. I need for that the whole impact code
        PPP_or_exch, OECD, simple_II_labels, OECDadditional, sector_description =  data_upload_OECD_salaries(year, currency_exchange_type, table_type, country)
        
        # the following is calculated twice: in data_upload_OECD_salaries and here. I want to leave it here, but I also need it there - do I??
        II = OECD.loc[simple_II_labels, simple_II_labels]
        household_expenditure = OECD.loc[simple_II_labels, 'HFCE']
        other_final_demand = OECD.loc[simple_II_labels, final_demand_columns[1:]] #exluding HFCE - household expenditure
        E           = OECDadditional['employees_compensation'] 
        GDP         = OECD.loc['VALU', simple_II_labels]
        output      = OECD.loc['OUTPUT', simple_II_labels]

        #dfother_final_demand = collecting_year_country_data_matrix(country, year, dfother_final_demand, other_final_demand , 'other_final_demand')
    
        dfoutput = collecting_year_country_data_vector(country, year, dfoutput, output, 'output')   
        dfGDP    = collecting_year_country_data_vector(country, year, dfGDP,    GDP, 'GDP')
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


        # 2. calculate L and Lc
        ##########################
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
            
        IIc.loc['employees_compensation', 'HFCE'] = 0 
        outputc = output.copy()
        outputc['HFCE'] = OECDadditional['employees_compensation'].sum()
        Tc = safe_divide(IIc, outputc)
        Lcdf, Lc_minus_I = clc_L(Tc)

              
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
        
        


end_time = time.time()
print(f"\n Elapsed time: {(end_time - start_time)/60:.1f} minutes \n")

#plot_Tc(dfTc, 'G') # Tc is very similar over the different years. I can use T of 2019
#all I need is to infer final demand in order to get x
#plot_subplots_vector_by_country(dffc, 'final demand', title='final demand')
#plot_subplots_vector_by_country(dfE, 'Employment', title='Employment')



###########################
#10. Employment extrapolation
###########################
dfEict = (
    dfE[dfE['sector'].isin(ICTsectors)]
    .groupby(['country', 'year'], as_index=False)['Employment']
    .sum()
    .rename(columns={'Employment': 'Etotal'})
)

## 10.a. polynomial extrapolation
#package extrapolation is polynomial extrapolation only with E
#dfE, dfEtotal, data_and_predictionE = package_extrapolation(dfE, 'Employment', 'Etotal', 0.8, 1, steps_forward=5, steps_back=4, alpha=50)
#dfGDP, dfGDPtotal, data_and_predictionGDP = package_extrapolation(dfGDP, 'GDP', 'GDPtotal', 0.8, 1, steps_forward=5, steps_back=4, alpha=50)

#10.b. extrapolation by gdp
dfE, dfEtotal = clc_v_tot(dfE, 'Employment', 'Etotal')
dfGDP, dfGDPtotal = clc_v_tot(dfGDP, 'GDP', 'GDPtotal')

# upload GDP data from World Bank - 1995-2024 or from "Bench_predictions/gdp_ARIMAgdp_currentUSD04.csv"
# GDP of world bank is in current USD dollars. 
# input-ouput tables and E are in millions of that year's USD dollars.
upload_from_gdp_extrapolated = True
if upload_from_gdp_extrapolated:
    #SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    #gdp_filename = os.path.join(SCRIPT_DIR, '..', '..', 'Data', 'Bench_predictions', 'gdp_ARIMAgdp_currentUSD04.csv')
    gdp_filename = "Bench_predictions/gdp_ARIMAgdp_currentUSD04.csv"
    gdp_data = pd.read_csv(gdp_filename)
    gdp_data.rename(columns={'Unnamed: 0': 'year'}, inplace=True) #renaming the column
    gdp_data['year'] = gdp_data['year'].astype(int)
    gdp_data.set_index('year', inplace=True)                  #setting year as index
else:
    worldbank_gdp_data = get_worldbank_gdp_data(False)
    worldbank_gdp_data.rename(columns={'Time': 'year'}, inplace=True   ) #renaming the column
    worldbank_gdp_data['year'] = worldbank_gdp_data['year'].astype(int) #recasting as int
    worldbank_gdp_data.set_index('year', inplace=True) 
    gdp_data = worldbank_gdp_data.copy()                 #setting year as index

    

#adjust to gdp_data or worldbank_gdp_data
dfE_G_ratio = compute_E_G_ratio(dfEtotal, gdp_data,countries, year_range)
avg_ratio_per_country = dfE_G_ratio.mean(axis=0)  # axis=0 → down the rows
std_ratio_per_country = dfE_G_ratio.std(axis=0)

Eextrap = pd.DataFrame(index=gdp_data.index , columns=gdp_data.columns)
for country in countries:
    Eextrap[country] = gdp_data[country] * avg_ratio_per_country[country]
    
#Eextrap is the extrapolation E
plot_v_by_year_1panel(Eextrap, countries, 'Employment', "Extrapolated Employment by Country")

# print to excel
Eextrap.to_csv("Bench_predictions/Etotal_multivariate_E_extrap03.csv", index=True)
print("\n \n")