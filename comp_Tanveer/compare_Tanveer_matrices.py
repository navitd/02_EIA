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



def find_title_cells(df, title):
    return [(i, j) for i in range(df.shape[0]) for j in range(df.shape[1]) if str(df.iat[i, j]).strip() == title]

def extract_vector_v(df, i, j):
    i += 1
    data = []
    while i < len(df) and pd.notna(df.iat[i, j]):
        data.append(df.iat[i, j])
        i += 1
    return pd.DataFrame(data, columns=["value"])

def extract_vector_h(df, i, j):
    j += 1
    data = []
    while j < df.shape[1] and pd.notna(df.iat[i, j]):
        data.append(df.iat[i, j])
        j += 1
    return pd.DataFrame([data], index=["value"])

def extract_matrix(df, i, j, skip_rows=4):
    
    start_row = i + skip_rows      # row where the matrix really starts
    start_col = j                  # same column as the title cell

    # ----- find the right-most column (stop at first NaN) -----
    end_col = start_col
    while end_col < df.shape[1] and pd.notna(df.iat[start_row, end_col]):
        end_col += 1       # end_col will be 1 past the last data column

    # ----- find the bottom row (stop at first NaN) -----
    end_row = start_row
    while end_row < df.shape[0] and pd.notna(df.iat[end_row, start_col]):
        end_row += 1       # end_row will be 1 past the last data row

    # Slice (note: end_row / end_col are exclusive)
    return df.iloc[start_row:end_row, start_col:end_col].copy()



def print_two_matrices_with_spacing(left_matrix, right_matrix, output_path="outputfile2.xlsx", spacing=0):
    
    if right_matrix is None or right_matrix.empty:
        raise ValueError("Right-hand matrix is empty or None.")

    # Ensure both matrices have the same number of rows
    max_rows = max(left_matrix.shape[0], right_matrix.shape[0])

    def pad_df(df, rows):
        if df.shape[0] < rows:
            pad = pd.DataFrame([[""] * df.shape[1]] * (rows - df.shape[0]))
            df = pd.concat([df, pad], ignore_index=True)
        return df.reset_index(drop=True)

    left_padded = pad_df(left_matrix, max_rows)
    right_padded = pad_df(right_matrix, max_rows)
    space = pd.DataFrame([[""] * spacing] * max_rows)

    combined = pd.concat([left_padded, space, right_padded], axis=1)

    combined.to_excel(output_path, index=False, header=False)
    print(f"Saved combined matrix to {output_path}")







# Load entire Excel sheet into raw dataframe
file_name = '../old_EIA/Tanveer_Model/EIA-Canada V3.xlsx'
year = '2015'
raw_df = pd.read_excel(file_name, header=None, sheet_name=year)

# Define the titles and expected structure
targets = {
    "HFCE": "vector_v",
    "VALU": "vector_h",
    "OUTPUT": "vector_h",
    "Compensation": "vector_h",
    "Direct GDP/OUTPUT Ratio": "vector_h",
    "I-O Table": "matrix",
    "Type I: Technical Coefficients [T]": "matrix",
    "Leonteiff Inverse Matrix [L-1]": "matrix"
}



# Scan and extract
extracted = {}
for title, typ in targets.items():
    matches = find_title_cells(raw_df, title)
    if not matches:
        print(f"Title '{title}' not found.")
        continue
    for i, j in matches:
        if typ == "vector_v":
            extracted[title] = extract_vector_v(raw_df, i, j)
        elif typ == "vector_h":
            extracted[title] = extract_vector_h(raw_df, i, j)
        elif typ == "matrix":
            extracted[title] = extract_matrix(raw_df, i, j)
        break  # stop at first match



# My data
year = '2015'
table_type = 'TTL' #or'DOM'   
OECD_path = "../Data/" # windows style: r".\\"
currency_exchange_type = 'EXCH' #'EXCH' or 'PPP'
PPP_or_exch, OECD, simple_II_labels, OECDadditional, sector_description =  data_upload_OECD_salaries(year, currency_exchange_type, table_type)
II = OECD.loc[simple_II_labels, simple_II_labels]
household_expenditure = OECD.loc[simple_II_labels, 'HFCE']
final_demand_columns = ['HFCE',	'NPISH',	'GGFC',	'GFCF',	'INVNT',	'CONS_NONRES', 'EXPO'] # 'IMPO', 'DPABR', 
other_final_demand = OECD.loc[simple_II_labels, final_demand_columns[1:]] #exluding HFCE - household expenditure
GDP         = OECD.loc['VALU', simple_II_labels]
output      = OECD.loc['OUTPUT', simple_II_labels]
T = safe_divide(II, output)
Ldf, L_minus_I = clc_L(T)

IIc = II.copy()
IIc["HFCE"] = household_expenditure # added a column for closed model
IIc.loc['employees_compensation'] = OECDadditional['employees_compensation'] #If I wanted a column I would have written IIC['employees_compensation']
IIc.loc['employees_compensation', 'HFCE'] = 0 #T97_values.loc[T97_values['Transaction'] == 'Compensation of employees', 'OBS_VALUE_USD'].values[0]

outputc = output.copy()
outputc['HFCE'] = OECDadditional['employees_compensation'].sum()
Tc = safe_divide(IIc, outputc)
Lcdf, Lc_minus_I = clc_L(Tc)

#compare T
# Tanveer doesn't have Tc. the bottom row of T is output
Tanveer_T = extracted["Type I: Technical Coefficients [T]"]
Tanveer_T.columns = Tanveer_T.iloc[0]  # Set first row as column names
Tanveer_T = Tanveer_T[1:].reset_index(drop=True)  # Drop the first row and reset index
Tanveer_T.index = Tc.index

diff_sum_T = (T.iloc[:45, :45] - Tanveer_T.iloc[:45, :45]).abs().sum().sum()

#compare L
Tanveer_inv_L = extracted["Leonteiff Inverse Matrix [L-1]"]
Tanveer_inv_L.columns = Tanveer_inv_L.iloc[0]  # Set first row as column names
Tanveer_inv_L = Tanveer_inv_L[1:].reset_index(drop=True)  # Drop the first row and reset index
Tanveer_inv_L.index = Ldf.index
diff_sum_L = (Ldf.iloc[:45, :45] - Tanveer_inv_L.iloc[:45, :45]).abs().sum().sum()

print_two_matrices_with_spacing(Ldf, extracted["Leonteiff Inverse Matrix [L-1]"],output_path="./comp_Tanveer/outputfile2.xlsx")
#this file does not clean itself. it'll have the matrixes from before if the new matrices are smaller.


print('')
print(f'absolute value of difference between T and Tanveer_T: {diff_sum_T}')
print(f'absolute value of difference between L and Tanveer_inv_L: {diff_sum_L}')
print('')
print('')


Tanveer_E = extracted["Compensation"]
Navit_E = OECDadditional["employees_compensation"]
diff_E = np.abs(Tanveer_E.values[0] - Navit_E.values).sum()
print(f'absolute value of difference compensation of employees Tanveer and Navit: {diff_E}')
print('')

#print(np.abs(Tanveer_E.values[0] - Navit_E.values))
top4 = np.abs(Tanveer_E.values[0] - Navit_E.values).argsort()[::-1][:4]
Navit_E.index[top4]
print(Navit_E.index[top4])
print( Tanveer_E.values[0][top4])
print(Navit_E.iloc[top4])

Tanveer_o = extracted["Compensation"].iloc[:45]
Navit_o = OECD.loc["OUTPUT"]
diff_o = np.abs(Tanveer_o.values[0] - Navit_o.values).sum()
print(f'absolute value of difference output Tanveer and Navit: {diff_o}')
print('')



