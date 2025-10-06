import numpy as np
import pandas as pd

def clean_world_bank_data(rough):
    
    # a. data description:
    col = 0
    col_name = rough.columns[col] #column to search in
    mask = rough.iloc[:, col].apply(lambda x: isinstance(x, str) and x.lower().startswith("data from database"))

    idx = mask[mask].index[col]  # first matching row index

    file_description = [rough.at[idx, col_name], rough.at[idx + 1, col_name] if idx + 1 in rough.index else None]

    # replace both with NaN
    rough.at[idx, col_name] = np.nan
    if idx + 1 in rough.index:
        rough.at[idx + 1, col_name] = np.nan

    # b. remove NaN rows from the bottom
    rough.dropna(how='all', inplace=True)

    # c. remove constant columns while saving the entries in file_description
    for col in rough.columns:
        unique_vals = rough[col].unique()
        if len(unique_vals) == 1:
            file_description.append(unique_vals[0])
            rough = rough.drop(columns=[col])

    rough.Time = rough.Time.astype("Int16")

    rough.drop(columns=["Time Code"], inplace=True)

    # Replace column names with the letters inside brackets
    rough.columns = [col.split('[')[-1].split(']')[0] if '[' in col and ']' in col else col for col in rough.columns]

    return rough, file_description
