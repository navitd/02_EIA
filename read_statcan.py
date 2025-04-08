import pandas as pd
import numpy as np
import os
import time
from func_data_upload import data_upload


#read from StatCan everything they have:
year = '2019'
PPP, OECD, simple_II_labels, mapping_dict, statcan =  data_upload(year)
transaction_names = ['Other taxes less other subsidies on production', 'Value added, gross',
 'Compensation of employees', 'Intermediate consumption', 'Output']
column_names = ['net_taxes', 'GDP', 'employees_compensation', 'intermediate_consumption', 'output']


statcan_sectors_data = pd.DataFrame()


for ix, name in enumerate(transaction_names):
        
    col_statcan = statcan[(statcan["TIME_PERIOD"] == int(year)) & (statcan["Transaction"] == name)].drop(columns=["Economic activity","TIME_PERIOD","Transaction"])
    # now GSPstatcan is with detailed OECD codes and we need to translate it to known OECD codes
    # from A01 and A02 to A01_02
    col_statcan['OECD_codes'] = col_statcan['detailed_sectors'].map(mapping_dict)
    col_statcan = col_statcan.sort_values(by="OECD_codes")

    # sum A01 and A02 to A01_02
    # Group by OECD_codes and sum the OBS_VALUE column
    col_statcan_grouped = col_statcan.groupby('OECD_codes', as_index=False)['OBS_VALUE'].sum()
    # GDPstatcan_grouped has OECD sectors but also other sectors. it has 95 rows. but the OECD sectors are correct (summed correctly)
    # I checked.

    # convert to USD
    # CAD to USD
    # Load the Excel file and read the specific sheet, selecting only the necessary columns
    file_path = '/mnt/c/NavitComputer24/2024_NES/Economics/Data/PPP_data.xlsx'  
    PPPtable = pd.read_excel(file_path, sheet_name='PPP_data', usecols=['TIME_PERIOD', 'OBS_VALUE'])
    PPP = PPPtable[PPPtable["TIME_PERIOD"]==int(year)]["OBS_VALUE"].values[0] 

    col_statcan_grouped['OBS_VALUE_USD'] = (col_statcan_grouped['OBS_VALUE'] / PPP).round(1)
    col_statcan_grouped.drop(columns=['OBS_VALUE'], inplace=True)
    
    # last step:
    # choose from it only codes that appear in OECD:
    df = col_statcan_grouped.set_index('OECD_codes').reindex(simple_II_labels, fill_value=0).copy()

    # Add to statcan_data under the corresponding column name
    statcan_sectors_data[column_names[ix]] = df['OBS_VALUE_USD']


print(statcan_sectors_data.head(10))