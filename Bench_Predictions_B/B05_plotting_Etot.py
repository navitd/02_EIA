

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
from func_data_upload_OECD_salaries import data_upload_OECD_salaries
from func_safe_divide import safe_divide, safe_divide_vector
from func_clc_L import clc_L

# for SHRED report
# ratio E_G to Etot 2010-2020
#graph E_G 1975-2040


dfE = pd.read_csv("Bench_predictions_B/A05_Esectors_from_Etot05.csv")

order = ["ITA", "JPN", "CAN", "FRA", "DEU", "GBR", "USA"]

dfE['country'] = pd.Categorical(dfE['country'], categories=order, ordered=True)
dfE = dfE.sort_values(['country', 'year'])


df = dfE.copy()
# share = E(G) / sum(E)
g = df[df['sector'] == 'G']
tot = df.groupby(['country','year'])['E'].sum().reset_index(name='E_total')

merged = g.merge(tot, on=['country','year'])
merged['share_G'] = merged['E'] / merged['E_total']


merged_1020 = merged[(merged['year'] >= 2010) & (merged['year'] <= 2020)]

for country, d in merged_1020.groupby('country'):
    plt.plot(d['year'], d['share_G'], marker='o', label=country)

plt.xlabel("Year")
plt.ylabel("E_G / sum(E)")
plt.title("Ratio of compensation of employees (sector G) to total Employment (2010-2020)")
plt.legend(loc='upper right', bbox_to_anchor=(0.40, 0.85))
plt.tight_layout()
plt.show()




# select sector G
g = dfE[dfE['sector'] == 'G'].copy()

# plot
for country, d in g.groupby('country'):
    plt.plot(d['year'], d['E'], marker='o', label=country)

plt.xlabel("Year")
plt.ylabel("E (sector G)")
plt.title("Compensation of employees (sector G) data and extrapolation")
plt.legend()
plt.tight_layout()
plt.show()





print(dfE.head())