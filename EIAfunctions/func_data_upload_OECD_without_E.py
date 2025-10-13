
import pandas as pd
import numpy as np
import time

OECD_PATH = '../Data/' # windows style: r".\\"

def data_upload_OECD_without_E(year, currency_exchange_type, table_type='TTL', country = 'CAN'):

    start_time = time.time()
    if table_type == 'DOM':
        input_filename = f'{OECD_PATH}NATIO{table_type}IMP/{country}{year}{table_type.lower()}.csv' # windows style: r".\\"
    elif table_type == 'TTL':
        input_filename = f'{OECD_PATH}NATIO{table_type}/{country}{year}{table_type.lower()}.csv'

    #print("working directory of func_data_upload_OECD_salaries3.py is: ",os.getcwd())  # Print the current working directory

    # 1. uploading the map from statcan sectors to OECD sectors:
    codes_map = pd.read_excel(
                                '/mnt/c/NavitComputer24/2024_NES/Economics/Data/Input_Codes_Map.xlsx', 
                                usecols="A,C",      # Use Excel column letters directly
                                header=None,        # Do not treat any row as the header
                                names=['Detailed_Codes', 'OECD_Codes'],  # Assign these names to the columns
                                skiprows=1          # Skip the first row (Excel is 1-based, so row 2 is index 1)
                                )
    mapping_dict = dict(zip(codes_map['Detailed_Codes'], codes_map['OECD_Codes']))

    # 2. Load the Excel file for OECD PPP table (OECD salaries are in local currency)
    file_path = '/mnt/c/NavitComputer24/2024_NES/Economics/Data/OECDsalaries/UTF-8OECD - XY Rates.csv'
    PPP_cols_to_load = ['LOCATION', 'TIME_PERIOD', 'INDICATOR', 'OBS_VALUE']
    PPP_rough = pd.read_csv(file_path, usecols=PPP_cols_to_load)
    PPP_filtered = PPP_rough[
        (PPP_rough['LOCATION'] == country) &
        (PPP_rough['TIME_PERIOD'] == int(year)) &
        (PPP_rough['INDICATOR'] == currency_exchange_type) ]
    if PPP_filtered.empty:
        PPP_or_exch = np.nan
    else:
        PPP_or_exch = PPP_filtered['OBS_VALUE'].iloc[0]


    # 3. Loading OECD data
    OECD_rough = pd.read_csv(input_filename)

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


    return PPP_or_exch, OECD,simple_II_labels