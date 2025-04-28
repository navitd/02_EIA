import pandas as pd
import numpy as np #numpy is installed but not used
import os
import time
import re
import matplotlib.pyplot as plt

# In this file I upload GDP from OECD and GDP from stat can and compare the two
# I also upload the PPP conversion table to convert from CAD to USD
# this is GDP_comp turned into a function
# finished 4.4.25


def data_upload(year)

    start_time = time.time()
    print("working directory of func_Read_StatCan.py is: ",os.getcwd())  # Print the current working directory

    OECD_path = "../Data/NATIODOMIMP/" # windows style: r".\\"
    OECD_name = filename = f'CAN{year}dom.csv'
    OECD_rough = pd.read_csv(OECD_path + OECD_name)

    # Remove imports from matrix
    OECD_rough = OECD_rough.set_index(OECD_rough.columns[0])  # Set first column as index
    OECD_rough.index = OECD_rough.index.astype(str)  # Ensure index is strings
    OECD = OECD_rough[~OECD_rough.index.str.startswith("IMP_")]
    simple_II_labels = OECD_rough.columns.tolist()[OECD_rough.columns.get_loc("A01_02") : OECD_rough.columns.get_loc("T") + 1]
    OECD.index = OECD.index.str.removeprefix("DOM_")
    II = OECD.loc[simple_II_labels, simple_II_labels]
    household_expenditure = OECD.loc[simple_II_labels, 'HFCE']
    final_demand_columns = ['HFCE',	'NPISH',	'GGFC',	'GFCF',	'INVNT',	'DPABR',	'CONS_NONRES',	'EXPO',	'IMPO']
    other_final_demand = OECD.loc[simple_II_labels, final_demand_columns[1:]] #exluding HFCE - household expenditure
    total       = OECD.loc[simple_II_labels, 'TOTAL'] #equals to output, this is x
    GDP         = OECD.loc['VALU', simple_II_labels]
    output      = OECD.loc['OUTPUT', simple_II_labels]
    #I don't need to worry bout household_expenditure of GDP or output - they are both 0
    # but output of GDP is given and should be marked independently

    #single values in OECD:
    GDP_of_household_expenditure = OECD.loc['VALU', 'HFCE']
    GDP_of_total_column = OECD.loc['VALU', 'TOTAL'] # total is the output, should be equal to f_row_sums.sum(axis=0)
    GDP_of_final_demand = OECD.loc['VALU', final_demand_columns]        #this could be added to the rows from the right or to the columns form the bottom
    output_of_final_demand = OECD.loc['OUTPUT', final_demand_columns]   #probably will not be needed

    # from looking at the numbers:
    # total = output
    # II_row_sums + f_row_sums (f has several columns)= total = output
    # household_expenditure is the column added to II to get the closed model
    # when uploading data for the first time run:
    # data_exploration_flags(II,household_expenditure,other_final_demand,output,output_of_final_demand,OECD_rough)

    #final demand and value added are not the same at all

    #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
    # Upload from StatCan:

    # uploading form CANSTAT from 
    # https://data-explorer.oecd.org/vis?tm=value%20added%20and%20its%20components%20by%20activity&pg=0&snb=10&df[ds]=dsDisseminateFinalDMZ&df[id]=DSD_NAMAIN10%40DF_TABLE6&df[ag]=OECD.SDD.NAD&df[vs]=2.0&dq=A.AUS...B1G.....V..&lom=LASTNPERIODS&lo=5&to[TIME_PERIOD]=false
    # I downloaded it to C:\NavitComputer24\2024_NES\Economics\Data\STATCAN
    # I want to make another file that compares STATCAN to OECD and checks consistency between them.
    # the statcan file: OECD_VA_Breakdown.csv or OECD_VA_Breakdown2.csv
    # OECD is in USD and STATCAN is in CAD?

    # WSL-compatible path
    filepath = "/mnt/c/NavitComputer24/2024_NES/Economics/Data/STATCAN/"
    #filename1 = 'OECD_VA_Breakdown.csv' #This file has, in addition to everything 2 has, 'wages and salaries'.
    filename2 = 'OECD_VA_Breakdown2.csv'
    statcan_rough = pd.read_csv(filepath + filename2)
    # Keep only columns where there is more than one unique value
    statcan = statcan_rough.loc[:, statcan_rough.nunique() > 1]
    statcan = statcan.drop(columns=["TRANSACTION"]).rename(columns={"ACTIVITY": "detailed_sectors"})

    #year = re.search(r'\d{4}', OECD_name).group() #this is a function and the year is an input variable

    GDPstatcan = statcan[(statcan["TIME_PERIOD"] == int(year)) & (statcan["Transaction"] == 'Value added, gross')].drop(columns=["Economic activity","TIME_PERIOD","Transaction"])
    #GDPstatcan.set_index("detailed_sectors")["OBS_VALUE"] #detailed_sectors is now the index

    # now GSPstatcan is with detailed OECD codes and we need to translate it to known OECD codes
    # from A01 and A02 to A01_02


    codes_map = pd.read_excel(
                                '/mnt/c/NavitComputer24/2024_NES/Economics/Data/Input_Codes_Map.xlsx', 
                                usecols="A,C",      # Use Excel column letters directly
                                header=None,        # Do not treat any row as the header
                                names=['Detailed_Codes', 'OECD_Codes'],  # Assign these names to the columns
                                skiprows=1          # Skip the first row (Excel is 1-based, so row 2 is index 1)
                                )
    mapping_dict = dict(zip(codes_map['Detailed_Codes'], codes_map['OECD_Codes']))
    #I checked this mapping dict and it is good

    GDPstatcan['OECD_codes'] = GDPstatcan['detailed_sectors'].map(mapping_dict)
    GDPstatcan = GDPstatcan.sort_values(by="OECD_codes")
    
    # sum A01 and A02 to A01_02
    # Group by OECD_codes and sum the OBS_VALUE column
    GDPstatcan_grouped = GDPstatcan.groupby('OECD_codes', as_index=False)['OBS_VALUE'].sum()
    # GDPstatcan_grouped I checked and it is correct

    #chose from it only codes that appear in OECD:
    #merge values to GDP

    GDP2 = GDP.reset_index(name='GDP_OECD').copy()
    GDP2.rename(columns={'index': 'OECD_codes1'}, inplace=True)
    GDP2 = pd.merge(GDP2, GDPstatcan_grouped, left_on='OECD_codes1', right_on='OECD_codes', how='inner')

    GDP2['ratio'] = GDP2['GDP_OECD'] / GDP2['OBS_VALUE']
    GDP2.rename(columns={'OBS_VALUE':"GDP_statcan_CAD"},inplace=True)
    GDP2.drop(columns=['OECD_codes'], inplace=True)

    # CAD to USD
    # Load the Excel file and read the specific sheet, selecting only the necessary columns
    file_path = '/mnt/c/NavitComputer24/2024_NES/Economics/Data/PPP_data.xlsx'  
    PPPtable = pd.read_excel(file_path, sheet_name='PPP_data', usecols=['TIME_PERIOD', 'OBS_VALUE'])
    PPP = PPPtable[PPPtable["TIME_PERIOD"]==int(year)]["OBS_VALUE"].values[0] #this is the value for 2020


    GDP2["GDP_statcan_USD"] = (GDP2["GDP_statcan_CAD"] / PPP).round(1) 



    #PPP?
    #https://data-explorer.oecd.org/vis?tm=PPP%20and%20exchange%20rates&pg=0&snb=17&df[ds]=dsDisseminateFinalDMZ&df[id]=DSD_NAMAIN10%40DF_TABLE4&df[ag]=OECD.SDD.NAD&df[vs]=2.0&dq=A.CAN...PPP_B1GQ.......&pd=2007%2C&to[TIME_PERIOD]=false&vw=tb



    # Create the plot
    plt.figure(figsize=(10, 6))

    # Plot the first line (GDP_OECD) with orange color and circles
    plt.plot(GDP2["OECD_codes1"], GDP2["GDP_OECD"], label='GDP of OECD [USD]', color='orange', marker='o')

    # Plot the second line (GDP_statcan_USD) with red color and circles
    plt.plot(GDP2["OECD_codes1"], GDP2["GDP_statcan_USD"], label='GDP of statcan [USD]', color='red', marker='o')

    # Set the title with the year variable
    plt.title(f'GDP [USD] of year={year}, plotted by GDP_comp.py')

    # Set the y-axis label
    plt.ylabel('GDP [Million USD]')

    # Set the x-axis label (you can change it based on your preference)
    plt.xlabel('OECD Codes')

    # Show the legend
    plt.legend()

    # Display the plot
    plt.xticks(rotation=45)  # Rotate x-ticks if necessary for better readability
    plt.grid(True)
    plt.tight_layout()  # Adjust layout for better spacing
    plt.show()


    return PPP, OECD, mapping_dict, statcan