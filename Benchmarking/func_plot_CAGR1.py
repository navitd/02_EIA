# func_plot_CAGR1.py

import sys
from pathlib import Path
import os
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from openpyxl import load_workbook, Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import PatternFill, Alignment, Font, Border, Side
import openpyxl
import inspect
from openpyxl.cell.cell import MergedCell
# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent / 'EIAfunctions'))
from func_data_upload_OECD_salaries import data_upload_OECD_salaries
from func_plot_L import plot_matrix_columns
from func_clc_L import clc_L
from func_safe_divide import safe_divide, safe_divide_vector


def plot_CAGR1_sum_sectors(cagr_by_country, plot_title):
# outputcagr_by_country
#sum over all ICT sectors and plot the CAGR by country, ordered from largest (left) to smallest(right)
    ICTcagr = {}
    for key in cagr_by_country.keys():
        ICTcagr[key] = cagr_by_country[key].sum()

   # Sort the data
    sorted_items = sorted(ICTcagr.items(), key=lambda item: item[1], reverse=True)
    countries, values = zip(*sorted_items)

    # Assign colors: green for Canada, blue for others
    colors = ['green' if country == 'CAN' else 'blue' for country in countries]

    # Plot
    x = np.arange(len(countries))
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(x, values, color=colors)

    # Add % labels
    for bar, value in zip(bars, values):
        height = bar.get_height()
        pct_text = f'{value * 100:.1f}%'
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + (0.005 if height >= 0 else -0.01),
            pct_text,
            ha='center',
            va='bottom' if height >= 0 else 'top',
            fontsize=9
        )

    # Style
    ax.set_xticks(x)
    ax.set_xticklabels(countries)
    ax.set_ylabel('CAGR')
    ax.set_title('ICT Sector CAGR by Country (Sorted, in %)')
    ax.set_ylim(min(values) * 1.2, max(values) * 1.2)

    plt.tight_layout()
    plt.show()
    
    return ICTcagr 