import pandas as pd
import numpy as np #numpy is installed but not used
import os
import time
import re
import matplotlib.pyplot as plt



def data_upload_OECD_salaries(year, currency_exchange_type):

    start_time = time.time()
    print("working directory of func_data_upload_OECD_salaries.py is: ",os.getcwd())  # Print the current working directory

    # 1. uploading the map from statcan sectors to OECD sectors:
    codes_map = pd.read_excel(
                                '/mnt/c/NavitComputer24/2024_NES/Economics/Data/Input_Codes_Map.xlsx', 
                                usecols="A,C",      # Use Excel column letters directly
                                header=None,        # Do not treat any row as the header
                                names=['Detailed_Codes', 'OECD_Codes'],  # Assign these names to the columns
                                skiprows=1          # Skip the first row (Excel is 1-based, so row 2 is index 1)
                                )
    mapping_dict = dict(zip(codes_map['Detailed_Codes'], codes_map['OECD_Codes']))

    # 2. Load the Excel file for OECD PPP table (OECD salaries are in CAD)
    file_path = '/mnt/c/NavitComputer24/2024_NES/Economics/Data/OECDsalaries/UTF-8OECD - XY Rates.csv'
    PPP_cols_to_load = ['LOCATION', 'TIME_PERIOD', 'INDICATOR', 'OBS_VALUE']
    PPP_rough = pd.read_csv(file_path, usecols=PPP_cols_to_load)
    PPP_filtered = PPP_rough[
        (PPP_rough['LOCATION'] == 'CAN') &
        (PPP_rough['TIME_PERIOD'] == int(year)) &
        (PPP_rough['INDICATOR'] == currency_exchange_type) ]
    PPP_or_exch = PPP_filtered['OBS_VALUE'].iloc[0]

  
    # 3. Loading OECD data
    OECD_path = "../Data/NATIODOMIMP/" # windows style: r".\\"
    OECD_name = filename = f'CAN{year}dom.csv'
    OECD_rough = pd.read_csv(OECD_path + OECD_name)

    # Remove imports from matrix
    OECD_rough = OECD_rough.set_index(OECD_rough.columns[0])  # Set first column as index
    OECD_rough.index = OECD_rough.index.astype(str)  # Ensure index is strings
    OECD = OECD_rough[~OECD_rough.index.str.startswith("IMP_")]
    simple_II_labels = OECD_rough.columns.tolist()[OECD_rough.columns.get_loc("A01_02") : OECD_rough.columns.get_loc("T") + 1]
    #In OECD there's no description of the labels (codes) in owrds. I should refer to Mira's file for that. try Input_Codes_Map.xlsx
    OECD.index = OECD.index.str.removeprefix("DOM_")
    # probably delete the following chunk:
    II = OECD.loc[simple_II_labels, simple_II_labels]
    household_expenditure = OECD.loc[simple_II_labels, 'HFCE']
    final_demand_columns = ['HFCE',	'NPISH',	'GGFC',	'GFCF',	'INVNT',	'DPABR',	'CONS_NONRES',	'EXPO',	'IMPO']
    other_final_demand = OECD.loc[simple_II_labels, final_demand_columns[1:]] #exluding HFCE - household expenditure
    total       = OECD.loc[simple_II_labels, 'TOTAL'] #equals to output, this is x
    GDP         = OECD.loc['VALU', simple_II_labels]
    output      = OECD.loc['OUTPUT', simple_II_labels]
    #I don't need to worry bout household_expenditure of GDP or output - they are both 0
    # but output of GDP is given and should be marked independently
 
    
    # 4. Upload salaries from a different file of OECD UTF-8SUT Use, Value added and its components by activity.csv

    # WSL-compatible path
    filepath = "/mnt/c/NavitComputer24/2024_NES/Economics/Data/OECDsalaries/UTF-8SUT Use, Value added and its components by activity.csv"
   
    additional_data_rough = pd.read_csv(filepath)
    # Keep only columns where there is more than one unique value
    data2 = additional_data_rough.loc[:, additional_data_rough.nunique() > 1]
    data2 = data2.drop(columns=["TRANSACTION"]).rename(columns={"ACTIVITY": "detailed_sectors"})
    # to look at the titles of the detailed sectors
    data2_descriptions = data2[(data2["TIME_PERIOD"] ==int(year)) ].drop(columns=['TIME_PERIOD','Transaction','OBS_VALUE'])
    sector_description = dict(zip(data2_descriptions['detailed_sectors'], data2_descriptions['Economic activity']))
    
    #year = re.search(r'\d{4}', OECD_name).group() #this is a function and the year is an input variable

    # 4.2 putting data2 in OECD_additionaol_data
    # columns in data2: Transaction - GDP, salaries, taxes, etc.
    # detailed_sectors, Economic Activity - A, M, G, etc.
    # VALUATIONI, Valuation - Purchasers price, not applicable, basic price
    # TIME_PERIOD, OBS_VALUE = year and value
    # ACCOUNTING_ENTRY, Accounting entry - Expenditure, Balance (revenue minus expenditure), Revenue

    transaction_names = ['Intermediate consumption', 'Mixed income, gross', 'Other taxes less other subsidies on production',
                         'Operating surplus and mixed income, gross', 'Output', 'Wages and salaries', 'Compensation of employees',
                         'Value added, gross']
    column_names = ['intermediate_consumption', 'mixed_income_gross', 'net_taxes_on_production',
                    'surplus_and_mixed_income_gross', 'output', 'salaries', 'employees_compensation', 'GDP' ]

    OECDadditional = pd.DataFrame()
    for ix, name in enumerate(transaction_names):     
        col_data2= data2[(data2["TIME_PERIOD"] == int(year)) & (data2["Transaction"] == name)].drop(columns=["Economic activity","TIME_PERIOD","Transaction"])
        # now GSPstatcan is with detailed OECD codes and we need to translate it to known OECD codes
        # from A01 and A02 to A01_02
        col_data2['OECD_codes'] = col_data2['detailed_sectors'].map(mapping_dict)
        col_data2 = col_data2.sort_values(by="OECD_codes")

        # sum A01 and A02 to A01_02
        # Group by OECD_codes and sum the OBS_VALUE column
        col_data2_grouped = col_data2.groupby('OECD_codes', as_index=False)['OBS_VALUE'].sum()
        # GDPstatcan_grouped has OECD sectors but also other sectors. it has 95 rows. but the OECD sectors are correct (summed correctly)
        # I checked.

        # convert CAD to USD by PPP_or_exch
        col_data2_grouped['OBS_VALUE_USD'] = (col_data2_grouped['OBS_VALUE'] / PPP_or_exch).round(1)
        col_data2_grouped.drop(columns=['OBS_VALUE'], inplace=True)
        
        # last step:
        # choose from it only codes that appear in OECD:
        df = col_data2_grouped.set_index('OECD_codes').reindex(simple_II_labels, fill_value=0).copy()

        # Add to statcan_data under the corresponding column name
        OECDadditional[column_names[ix]] = df['OBS_VALUE_USD']

    

    return PPP_or_exch, OECD, simple_II_labels, OECDadditional, sector_description