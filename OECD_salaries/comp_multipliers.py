# uploading multipliers data from statcan and comparing with my calculation (DOM, not TTL)

import pandas as pd
import numpy as np #numpy is installed but not used
import os
import time
import re
import matplotlib.pyplot as plt
from fuzzywuzzy import process

OECD_PATH = '../Data/' # windows style: r".\\"


print("working directory of comp_multipliers.py is: ",os.getcwd())  # Print the current working directory
#OECD_PATH = '../Data/' # windows style: r".\\"

year = '2015'
table_type='DOM'
if table_type == 'DOM':
    input_filename = f'{OECD_PATH}NATIO{table_type}IMP/CAN{year}{table_type.lower()}.csv' # windows style: r".\\"
elif table_type == 'TTL':
    input_filename = f'{OECD_PATH}NATIO{table_type}/CAN{year}{table_type.lower()}.csv'

# 1. uploading the map from statcan sectors to OECD sectors:
OECD_codes = pd.read_excel(
                            '/mnt/c/NavitComputer24/2024_NES/Economics/Data/Input_Codes_Map.xlsx', 
                            usecols="A,B,C",      # Use Excel column letters directly
                            header=None,        # Do not treat any row as the header
                            names=['codes detailed', 'sector description' ,'codes short list'],  # Assign these names to the columns
                            skiprows=1          # Skip the first row (Excel is 1-based, so row 2 is index 1)
                            )
#mapping_dict = dict(zip(codes_map['Detailed_Codes'], codes_map['OECD_Codes']))

# WSL-compatible path
multipliers_filepath = "/mnt/c/NavitComputer24/2024_NES/Economics/Data/statcan_multipliers_2015/36100594.csv"
data_rough = pd.read_csv(multipliers_filepath)
# Keep only columns where there is more than one unique value
data = data_rough.loc[:, data_rough.nunique() > 1]

rename_dict = {
    'REF_DATE': 'year',
    'Variable': 'variable type',
    'Industry': 'sector',
    'VALUE': 'multiplier value',
    'UOM': 'per what?'
}
data.rename(columns=rename_dict, inplace=True)
data['sector_code'] = data['sector'].str.extract(r'\[([^\[\]]+)\]')



# Remove [BS312200] etc.
data['sector_clean'] = data['sector'].apply(lambda x: re.sub(r"\s*\[.*?\]\s*", "", str(x)).strip())

# 2. Prepare a list of OECD sector names to match against
oecd_sector_list = OECD_codes['sector description'].dropna().unique().tolist()

# 3. Fuzzy match and assign best match to new column
def get_best_match(sector, choices):
    match, score = process.extractOne(sector, choices)
    return match if score >= 80 else None  # Adjust threshold as needed

data['matched_OECD_sector'] = data['sector_clean'].apply(lambda x: get_best_match(x, oecd_sector_list))
















sectors = data['sector'].unique()


