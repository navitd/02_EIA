#this file is called comp_multipliers.py but as it is now it only deals with mapping from NIACS to OECD
#thi sis the automated version of the mapping from NAICS to OECD sectors
#it works but I'mnot sure it does a good job
#this is for comparison with statcan, not with Tanveer.

import pandas as pd
import numpy as np  # numpy is installed but not used
import os
import re
import matplotlib.pyplot as plt
from fuzzywuzzy import process
import time
OECD_PATH = '../Data/'

start_time = time.time()
print("working directory of comp_multipliers.py is: ", os.getcwd())

output_path = "/mnt/c/NavitComputer24/2024_NES/Economics/Data/NAICS_OECD_map.xlsx"
year = '2015'
table_type = 'DOM'
if table_type == 'DOM':
    input_filename = f'{OECD_PATH}NATIO{table_type}IMP/CAN{year}{table_type.lower()}.csv'
elif table_type == 'TTL':
    input_filename = f'{OECD_PATH}NATIO{table_type}/CAN{year}{table_type.lower()}.csv'

# 1. uploading the map from statcan sectors to OECD sectors:
OECD_codes = pd.read_excel(
    '/mnt/c/NavitComputer24/2024_NES/Economics/Data/Input_Codes_Map.xlsx',
    usecols="A,B,C",
    header=None,
    names=['codes detailed', 'sector description', 'codes short list'],
    skiprows=1
)

multipliers_filepath = "/mnt/c/NavitComputer24/2024_NES/Economics/Data/statcan_multipliers_2015/36100594.csv"
data_rough = pd.read_csv(multipliers_filepath,dtype={13: str, 15: str})

# Keep only columns with more than one unique value, then explicitly copy
data = data_rough.loc[:, data_rough.nunique() > 1].copy()

# Rename columns without inplace to avoid warnings
data = data.rename(columns={
    'REF_DATE': 'year',
    'Variable': 'variable type',
    'Industry': 'sector',
    'VALUE': 'multiplier value',
    'UOM': 'per what?'
})

# Extract sector_code safely
data.loc[:, 'sector_code'] = data['sector'].str.extract(r'\[([^\[\]]+)\]')

# Remove brackets in sector names
data.loc[:, 'sector_clean'] = data['sector'].apply(lambda x: re.sub(r"\s*\[.*?\]\s*", "", str(x)).strip())

oecd_sector_list = OECD_codes['sector description'].dropna().unique().tolist()

# I shouldn't use fuzzywuzzy. the sectors are not close at all
def get_best_match(sector, choices):
    match, score = process.extractOne(sector, choices)
    return match if score >= 80 else None

data.loc[:, 'matched_OECD_sector'] = data['sector_clean'].apply(lambda x: get_best_match(x, oecd_sector_list))

# Write to Excel
data.to_excel(output_path, sheet_name='MAICS_OECD_map', index=False)

print(f"Data exported to {output_path}")



end_time = time.time()
print(f"Time taken to process data: {end_time - start_time:.2f} seconds")
