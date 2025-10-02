
import time
import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator
import matplotlib.gridspec as gridspec
import matplotlib.colors as mcolors
import matplotlib.cm as cm

import os
from pathlib import Path
notebook_path = os.getcwd()
print(os.getcwd())
import sys
sys.path.append(str(Path(notebook_path) / 'EIAfunctions')) 
#sys.path.append('/mnt/c/NavitComputer24/2024_NES/Economics/Textbook_EIA/EIAfunctions')

#scikit-learn imports
from sklearn.linear_model import LinearRegression
from numpy.polynomial.polynomial import Polynomial
from numpy.polynomial import Polynomial


####################################################         functions that Extrapolate       ##################################################
# this function is used in the next function, polynomial_extrapolation 
def polynomial_extrapolation_model(data, train_test_split, degree):
    if train_test_split < 1:
        split_index = int(data.shape[0] * train_test_split)
        Xtrain, Xtest = data.iloc[:split_index][['Time']], data.iloc[split_index:][['Time']]
        ytrain, ytest = data.iloc[:split_index].drop(columns=['Time']), data.iloc[split_index:].drop(columns=['Time'])
        #note that index in ytest and Xtest are 40:49, not 0:9
    elif train_test_split == 1:
        split_index = data.index[-1] + 1    
        Xtrain, Xtest = data.iloc[:split_index][['Time']], data.iloc[split_index:][['Time']]
        ytrain, ytest = data.iloc[:split_index].drop(columns=['Time']), data.iloc[split_index:].drop(columns=['Time'])
              
    # polynomial extrapolation model
    dfp = pd.DataFrame()
    for col in [c for c in data.columns if c != 'Time']:
        col = str(col)
        coefs = Polynomial.fit(Xtrain['Time'], ytrain[col], degree).convert().coef
        p_object = Polynomial(coefs)   # coefs are in ascending order here (c0 + c1 x + c2 x^2 ...)
        #save p_object, these are the models
        dfp[col] = coefs #p_object
        predictions = p_object(Xtest.to_numpy())
        data.loc[Xtest.index, f'{col} prediction'] = predictions
        
    data['prediction flag'] = False
    data.loc[split_index:, 'prediction flag'] = True
    return data, dfp


#the following deals with both backwardsa and forwards extrapolation
def polynomial_extrapolation(data, train_test_split, degree, steps_forward=5, steps_back=4):
    #building the model - getting coefficients
    data, dfp = polynomial_extrapolation_model(data, train_test_split, degree) #dfp are the coeff. should change name
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


################################################        from function library            #######################################################


OECD_PATH = '../Data/' # windows style: r".\\"

def data_upload_WorldBank(filename, year, country, WorldBank_table_type='GDP', currency_exchange_type='PA_NUS_USD'):

    start_time = time.time()
    print("working directory of func_data_upload_OECD_salaries3.py is: ",os.getcwd())  # Print the current working directory

    # 1. Loading OECD data
    rough = pd.read_csv(filename)


    # Remove imports from matrix
    OECD_rough = OECD_rough.set_index(OECD_rough.columns[0])  # Set first column as index
    OECD_rough.index = OECD_rough.index.astype(str)  # Ensure index is strings
    OECD = OECD_rough[~OECD_rough.index.str.startswith("IMP_")]
    simple_II_labels = OECD_rough.columns.tolist()[OECD_rough.columns.get_loc("A01_02") : OECD_rough.columns.get_loc("T") + 1]
    #In OECD there's no description of the labels (codes) in owrds. I should refer to Mira's file for that. try Input_Codes_Map.xlsx
    OECD.index = OECD.index.str.removeprefix(table_type + '_')
    # probably delete the following chunk:
    II = OECD.loc[simple_II_labels, simple_II_labels]
    household_expenditure = OECD.loc[simple_II_labels, 'HFCE']
    final_demand_columns = ['HFCE',	'NPISH',	'GGFC',	'GFCF',	'INVNT',	'DPABR',	'CONS_NONRES',	'EXPO',	'IMPO']
    other_final_demand = OECD.loc[simple_II_labels, final_demand_columns[1:]] #exluding HFCE - household expenditure
    GDP         = OECD.loc['VALU', simple_II_labels]
    output      = OECD.loc['OUTPUT', simple_II_labels]
    #I don't need to worry bout household_expenditure of GDP or output - they are both 0
    # but output of GDP is given and should be marked independently


    # 4. Upload salaries from a different file of OECD UTF-8SUT 

    # WSL-compatible path
    #old file, only Canada: additional_filepath = "/mnt/c/NavitComputer24/2024_NES/Economics/Data/OECDsalaries/UTF-8SUT Use, Value added and its components by activity.csv"
    # link for additional OECD https://data-explorer.oecd.org/vis?df[ds]=dsDisseminateFinalDMZ&df[id]=DSD_NASU%40DF_USEVA_T1600&df[ag]=
    # OECD.SDD.NAD&df[vs]=1.0&hc[Transaction]=Output&pg=0&snb=53&tm=input-output&utm_source=chatgpt.com&dq=A.FRA%2BJPN%2BUSA%2BGBR%2BITA%2BDEU%2B
    # CAN.B2A3G%2BB2A3N%2BD11%2BD1%2BD29X39%2BB3G%2BB1G%2BP2%2BP1._T%2BA%2BB%2BC%2BD%2BE%2BF%2BG%2BH%2BI%2BJ%2BK%2BL%2BM%2BN%2BO%2BP%2BQ%2BR%2BS%2BT%2BU%2B_
    # X....V.&pd=2011%2C2022&to[TIME_PERIOD]=false&vw=tb
    additional_filepath = "/mnt/c/NavitComputer24/2024_NES/Economics/Data/OECDsalaries/additionalOECD.csv"
    additional_data_rough = pd.read_csv(additional_filepath)
    # Keep only columns where there is more than one unique value
    data2 = additional_data_rough.loc[:, additional_data_rough.nunique() > 1]
    data2 = data2[data2.REF_AREA == country] # keep only the rows for the country
    data2 = data2.rename(columns={"ACTIVITY": "detailed_sectors"})
    # to look at the titles of the detailed sectors
    data2_descriptions = data2[(data2["TIME_PERIOD"] ==int(year)) ] #.drop(columns=['Reference area','TIME_PERIOD','Transaction','OBS_VALUE','ACCOUNTING_ENTRY',
                                                                    #            'OBS_STATUS','Currency'])
    sector_description = dict(zip(data2_descriptions['detailed_sectors'], data2_descriptions['Economic activity']))

    #year = re.search(r'\d{4}', OECD_name).group() #this is a function and the year is an input variable

    # 4.2 putting data2 in OECD_additionaol_data
    # columns in data2: Transaction - GDP, salaries, taxes, etc.
    # detailed_sectors, Economic Activity - A, M, G, etc.
    # VALUATIONI, Valuation - Purchasers price, not applicable, basic price
    # TIME_PERIOD, OBS_VALUE = year and value
    # ACCOUNTING_ENTRY, Accounting entry - Expenditure, Balance (revenue minus expenditure), Revenue

    transaction_names = ['Value added, gross', 'Other taxes less other subsidies on production', 'Operating surplus and mixed income, net', 
                        'Wages and salaries', 'Compensation of employees']
    column_names = ['GDP', 'net_taxes_on_production', 'surplus_and_mixed_income_net', 
                    'salaries', 'employees_compensation' ]

    
    OECDadditional = pd.DataFrame()
    for ix, name in enumerate(transaction_names):     
        one_transaction_type= data2[(data2["TIME_PERIOD"] == int(year)) & (data2["Transaction"] == name)].drop(columns=["Economic activity","TIME_PERIOD","Transaction", 
                                                                                                                        "TRANSACTION",
                                                                                                                        'Reference area','TIME_PERIOD','Transaction','ACCOUNTING_ENTRY',
                                                                                                                        'OBS_STATUS','Currency'])
        # now GSPstatcan is with detailed OECD codes and we need to translate it to known OECD codes
        # from A01 and A02 to A01_02
        one_transaction_type['OECD_codes'] = one_transaction_type['detailed_sectors'].map(mapping_dict)
        one_transaction_type = one_transaction_type.sort_values(by="OECD_codes")

        # sum A01 and A02 to A01_02
        # Group by OECD_codes and sum the OBS_VALUE column
        one_transaction_type_grouped = one_transaction_type.groupby('OECD_codes', as_index=False)['OBS_VALUE'].sum()
        # GDPstatcan_grouped has OECD sectors but also other sectors. it has 95 rows. but the OECD sectors are correct (summed correctly)
        # I checked.
        
        # convert CAD to USD by PPP_or_exch
        one_transaction_type_grouped['OBS_VALUE_USD'] = (one_transaction_type_grouped['OBS_VALUE'] / PPP_or_exch).round(1)
        one_transaction_type_grouped.drop(columns=['OBS_VALUE'], inplace=True)
        
        # last step:
        # choose from it only codes that appear in OECD:
        if 'J' not in simple_II_labels:
            simple_II_labels_plus_J = simple_II_labels + ['J']
        df = one_transaction_type_grouped.set_index('OECD_codes').reindex(simple_II_labels_plus_J, fill_value=0).copy()   

        # Add to statcan_data under the corresponding column name
        OECDadditional[column_names[ix]] = df['OBS_VALUE_USD']

    # from J to a correct value of J61
    if "j61" not in OECDadditional.index:
        OECDadditional.loc["J61"] = OECDadditional.loc["J"] - OECDadditional.loc["J58T60"] - OECDadditional.loc["J62_63"]   
    OECDadditional = OECDadditional.drop("J")

    return PPP_or_exch, OECD, simple_II_labels, OECDadditional, sector_description


def clc_L(T):
    
    n = T.shape[0]
    identity_matrix = np.eye(n)
    I_minus_T = identity_matrix - T.to_numpy()

    if np.linalg.det(I_minus_T) != 0:
        L = np.linalg.inv(I_minus_T)
        Ldf = pd.DataFrame(L, columns=T.columns, index=T.index)
        L_minus_I = Ldf - pd.DataFrame(identity_matrix, index=T.index, columns=T.columns)
        return Ldf, L_minus_I
    else:
        print("Matrix I - T is not invertible.")
        raise ValueError("Stopping execution due to non-invertible matrix.")
    
    
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

################################################         functions that plot              ######################################################


#used for extrapolation and for looking at the data
def plot_gdp_panels(data, countries, title): #red line connects
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


#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@                    main                  @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

country_names = ['Canada', 'The United States', 'Great Britain', 'France', 'Germany', 'Italiy', 'Japan']
countries = ['CAN', 'USA', 'GBR', 'FRA', 'DEU', 'ITA', 'JPN'] 
country_map = dict(zip(countries, country_names))

# 1. Get data
############## 
rough = pd.read_csv('/mnt/c/NavitComputer24/2024_NES/Economics/Data/trending_data/World Bank G7 final demand and GDP/G7 final demand Data.csv')
series_name = 'GDP (current US$)'
data = rough[rough['Series Name'] == series_name].copy().drop(axis=1, labels=['Series Name', 'Series Code','Time Code'])

data.columns = [re.search(r'\[(.*?)\]', col).group(1) if '[' in col else col for col in data.columns]
data = data.apply(pd.to_numeric, errors='coerce')



steps_back = 4
steps_forward = 5
first_year = int(data['Time'].min())
last_year = int(data['Time'].max())

#the following deals with both backwardsa and forwards extrapolation
def polynomial_extrapolation(data, data_title, train_test_split, degree, steps_forward=5, steps_back=4):
    #building the model - getting coefficients
    data, dfp = polynomial_extrapolation_model(data, train_test_split, degree) #dfp are the coeff. should change name
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



def plot_extrapolation(data, first_year, last_year, countries, title): #red line connects
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




# 2. Parameter searching for an extrapolation model
####################################################
train_test_split = 0.8
degree = 2
data_and_prediction = polynomial_extrapolation(data.copy(), 'GDP', train_test_split, degree,5,4)
plot_gdp_panels(data_and_prediction, countries, title=f'Polinomial Extrapolation GDP, degree={degree}') #lots a line between backwards and forwards extrapolation

# 3. actual extrapolation
##########################
train_test_split = 1
data_and_prediction2 = polynomial_extrapolation(data.copy(), 'GDP', train_test_split, degree,5,4)
plot_gdp_panels(data_and_prediction2, countries, title=f'Polinomial Extrapolation GDP, degree={degree}')
