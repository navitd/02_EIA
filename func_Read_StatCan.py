# I will have a module for upload input and a module for calculation and a module for comparison between different inputs/results
# I want the same function to be used to upload, inside it the treatment is very different for an original OECD file and Mira's file
# no. perhaps it would be better to have a function that uploads Mira's data, returns matrices and vectors
# and another function that uploads original OECD files (letontief matrices as well)

# !in this file, not like func_Read_CAN2020.py, E uploaded from VA Breakdown is assumed to be basic price already 

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import traceback
import time



##############################################################     functions made for this file    #######################################################

def upload_from_statcan(file_path, file_nameM, col, col_value):
    
    
    # column Y is the "Value Added, Gross" = I would like to sum to each 'A01_02' category all Ys where 
    # J = 'Value Added, Gross'
    # K = 'A01_02'
    # W = '2020'
    columns_str = "K, W, Y, " + col
    columns_list = columns_str.split(", ")
    columns_list.sort()
    columns_str_sorted = ", ".join(columns_list)

    VA_Breakdown = pd.read_excel(
                                file_path + file_nameM, 
                                sheet_name='VA Breakdown (PP)', 
                                usecols = columns_str_sorted,  # Use Excel column letters directly
                                header = None,        # Do not treat any row as the header
                                names = columns_list  # Assign these names to the columns
                                )
    VA_Breakdown = VA_Breakdown[(VA_Breakdown['W'] == 2020) & (VA_Breakdown[col] == col_value)] #add .copy() only if I modify the dataframe later
    # now VA_rough is with detailed OECD codes and we need to translate it to known OECD codes
    # from A01 and A02 to A01_02
    codes_map = pd.read_excel(
                                file_path + 'Input_Codes_map.xlsx', 
                                usecols="A,C",      # Use Excel column letters directly
                                header=None,        # Do not treat any row as the header
                                names=['Detailed_Codes', 'OECD_Codes'],  # Assign these names to the columns
                                skiprows=1          # Skip the first row (Excel is 1-based, so row 2 is index 1)
                                )
    mapping_dict = dict(zip(codes_map['Detailed_Codes'], codes_map['OECD_Codes']))

    # Replace values in VA_rough['K'] using the mapping
    VA_Breakdown['K'] = VA_Breakdown['K'].map(mapping_dict)

    # Group VA by 'K' and sum the 'Y' values
    VA_Gross = VA_Breakdown.groupby('K')['Y'].sum()
    return VA_Gross




##############################################################                Main                 #######################################################
# Stat CAn is in CAD and OECD is in USD
# column Y is the Values = I would like to sum to each 'A01_02' category all Ys where 
# J possible values: 
# J = 'Value Added, Gross'
# K = 'A01_02'
# W = '2020'


# Convert Windows path to WSL-compatible path
filepath = "/mnt/c/NavitComputer24/2024_NES/Economics/Data/STATCAN/"
#filename1 = 'OECD_VA_Breakdown.csv' #This file has, in addition to everything 2 has, 'wages and salaries'.
filename2 = 'OECD_VA_Breakdown2.csv'
df2_rough = pd.read_csv(filepath + filename2)
# Keep only columns where there is more than one unique value
df2 = df2_rough.loc[:, df2_rough.nunique() > 1]
#ACTIVITY is the Sectors how many? 125 A01, A02 etc.
#df1 (['Other taxes less other subsidies on production', 'Value added, gross', 'Wages and salaries', 'Compensation of employees', 'Intermediate consumption', 'Output']
#df2 (['Other taxes less other subsidies on production', 'Value added, gross', 'Compensation of employees', 'Intermediate consumption', 'Output']
# df1: 'how about the number of years? array([2020, 2019, 2018, 2017, 2016, 2015, 2014, 2013, 2012, 2011, 2010, 2009, 2008, 2007, 2021])
# df2: [2020 2019 2018 2017 2016 2015 2014 2013 2012 2011 2010 2009 2008 2007 2021]

print(df2.columns)
# Ensure TIMEPERIOD is sorted properly
df2 = df2.sort_values(by="TIME_PERIOD")

change sectors "ACTIVITY" to OECD sectors


## Filter the DataFrame for "Value added, gross" and year 2019
df_filtered = df2[(df2["Transaction"] == "Value added, gross") & 
                  (df2["TIME_PERIOD"].astype(str).str.startswith("2019"))]

# Create plot
plt.figure(figsize=(24, 6))
plt.plot(df_filtered["ACTIVITY"], df_filtered["OBS_VALUE"], marker='o', linestyle='-', label="Value added, gross")

# Formatting
plt.xlabel("ACTIVITY")
plt.ylabel("OBS_VALUE")
plt.title("OBS_VALUE vs. ACTIVITY for 'Value added, gross' (2019)")
plt.xticks(rotation=90)  # Rotate x-axis labels for better readability
plt.grid(True)
plt.legend()

plt.show()







print(df2.head())



'''    
# This ensures the script only runs when executed directly, not when imported
if __name__ == "__main__":


    # Start the timer
    start_time = time.time()

    print("Running Read_CAN2020 function")
   
    #dfppp = pd.read_excel(file_path+file_nameM, sheet_name="PPP")
    #ppp = dfppp.loc[(dfppp["TIME_PERIOD"] == 2020) & (dfppp["CURRENCY"] == "CAD"), "OBS_VALUE"]
    # reading from file is very slow
    # Extract the single value (assuming only one match)
    ppp = 1.341153


    
    # column Y is the Values = I would like to sum to each 'A01_02' category all Ys where 
    # J = 'Value Added, Gross'
    # K = 'A01_02'
    # W = '2020'

    col = "J"
    col_value = 'Value added, gross'
    VA_gross = upload_from_VA_Breakdown(file_path, file_nameM, col, col_value)

    #2.1.2 Compensation of Employees
    # in this analysis that are two columns named "Compensation of Employees", one is in VA (%) and the other in CAN2020
    col = "J"
    col_value = 'Compensation of employees' 
    E = upload_from_VA_Breakdown(file_path, file_nameM, col, col_value)
    

    print('Read_CAN2020 function is done')
    # Stop the timer
    end_time = time.time()
    # Print the execution time
    print(f"func_Read_CAN2020 Execution time: {end_time - start_time:.1f} seconds")


'''