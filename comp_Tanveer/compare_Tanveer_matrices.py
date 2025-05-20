import pandas as pd



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
    """
    Extract a rectangular numeric block that starts *skip_rows* below the title
    cell (i, j) and is bounded on the bottom and the right by NaNs.

    Parameters
    ----------
    df : pandas.DataFrame         # the raw sheet
    i, j : int, int               # coordinates of the title cell
    skip_rows : int               # how many rows to skip after the title

    Returns
    -------
    pd.DataFrame                  # the extracted matrix
    """
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








# Load entire Excel sheet into raw dataframe
file_name = '../../old_EIA/Tanveer_Model/EIA-Canada V3.xlsx'
year = '2015'
raw_df = pd.read_excel(file_name, header=None, sheet_name=year)

# Define the titles and expected structure
targets = {
    "HFCE": "vector_v",
    "VALU": "vector_h",
    "OUTPUT": "vector_h",
    "Compensation of employees": "vector_h",
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

# Example: access the OUTPUT vector
print(extracted["OUTPUT"])
