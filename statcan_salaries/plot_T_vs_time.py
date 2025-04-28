import pandas as pd
import numpy as np
import os
import time
from func_data_upload import data_upload
import matplotlib.pyplot as plt


###############################################               main               #########################


start_time = time.time()
print("working directory of income_multipliers.py is: ",os.getcwd())  # Print the current working directory

#ICT sectors information

OECD_sectors_for_indirect = ['C26',	'G',	'J58T60',	'J61',	'J62_63',	'M']
ICT_sectors_dict = {'ICT - Manufacturing': 'C26',
                    'ICT - Wholesaling': 'G',
                    'ICT - Software and computer services': ['J58T60', 'J62_63', 'M'],  
                    'ICT - Communications services': 'J61'}
# Build sector code to name mapping
code_to_name = {}
for name, codes in ICT_sectors_dict.items():
    if isinstance(codes, list):
        for code in codes:
            code_to_name[code] = name
    else:
        code_to_name[codes] = name

#yearvec = ['2007', '2008', '2009', '2010']
yearvec = ['2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020']


import matplotlib.pyplot as plt

# Collect T values for all years
T_yearly = {}

for year in yearvec:
    _, OECD, simple_II_labels, _, _ =  data_upload(year)

    II = OECD.loc[simple_II_labels, simple_II_labels]
    output = OECD.loc['OUTPUT', simple_II_labels]

    T = II.div(output, axis=0)
    T_yearly[year] = T

# Plot setup
fig, axes = plt.subplots(3, 2, figsize=(14, 10), sharey=True)
axes = axes.flatten()

for i, sector in enumerate(OECD_sectors_for_indirect):
    ax = axes[i]

    for year in yearvec:
        T = T_yearly[year]

        if sector in T.columns:
            y = T[sector].reindex(simple_II_labels)
            ax.plot(simple_II_labels, y, label=year, marker='o')

    sector_name = code_to_name.get(sector, 'Unknown')
    ax.set_title(f'{sector_name} ({sector})')
    ax.set_xlabel('Input Sector (rows of T)')
    ax.set_ylabel('Technical Coefficient')
    ax.tick_params(axis='x', rotation=90)
    ax.legend(fontsize='small')

fig.suptitle('Column Values in T per Sector, by Year', fontsize=16)
plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.show()
