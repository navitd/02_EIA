# benchmarking - the EIA from print2xls3.py is in a function and I choose sectors, years, calculate compound annual growth rate and plot
# input-output table from OECD
# https://www.oecd.org/en/data/datasets/input-output-tables.html


import sys
from pathlib import Path
import os
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import seaborn as sns
from openpyxl import load_workbook, Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import PatternFill, Alignment, Font, Border, Side

from openpyxl.cell.cell import MergedCell
# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent / 'EIAfunctions'))
from func_data_upload_OECD_salaries import data_upload_OECD_salaries
from func_plot_L import plot_matrix_columns
from func_clc_L import clc_L
from func_safe_divide import safe_divide, safe_divide_vector
from func_multipliers_by_f import multipliers_by_f
from func_plot_real_vs_predicted import plot_real_vs_predicted



def scale_df_by_series(direct_o: pd.DataFrame, fcdf: pd.Series) -> pd.DataFrame:
    
    return direct_o[fcdf.index].mul(fcdf, axis=1)


def pivot_matrix_to_3_columns(m: pd.DataFrame, value: str) -> pd.DataFrame:
    return m.reset_index().melt(id_vars=m.index.name or 'index',
                                var_name='buying sector',
                                value_name=value).rename(columns={m.index.name or 'index': 'selling sector'})






#Fig 1: CAGR data manipulation
def clc_cagr(dfoutput, first_year, last_year, value_column):
    # pivoting is a great idea there's no groupby. there's just taking first_year and last_year, then pivoting to ahve each row isolate an equation, then we manipulate numbers in each row
    df_filtered = dfoutput[dfoutput['year'].isin([str(first_year), str(last_year)])]
    pivot_df = df_filtered.pivot_table(
        index=['country', 'sector'],
        columns='year',
        values=value_column
    ).reset_index()
    #np.where is actually an if statement np.where(condition, value_if_true, value_if_false)
    pivot_df['CAGR'] = np.where(
        (pivot_df[str(first_year)] != 0) & (pivot_df[str(first_year)].notna()) & (pivot_df[str(last_year)].notna()),
        (pivot_df[str(last_year)] / pivot_df[str(first_year)]) ** (1 / (int(last_year) - int(first_year))) - 1,
        np.nan
    )
    #plotting - take all the ICT sectors and average CAGR, then plot.
    ICT_cagr = (
        pivot_df[pivot_df['sector'].isin(ICTsectors)]   # Filter for ICT sectors
        .groupby('country')['CAGR']                     # group by country
        .mean()                                         # calculate mean CAGR for each country                   
        .sort_values(ascending=False)
    )
    return ICT_cagr

# fig 1: plot CAGR
def plot_cagr(ICT_cagr, title):
        # Rename for plotting
    ICT_cagr.index = [country_map[c] for c in ICT_cagr.index]

    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(ICT_cagr))
    bars = ax.bar(x, ICT_cagr.values, color=[
        'green' if country_map.get(code, code) == 'Canada' else 'blue' for code in ICT_cagr.index
    ])

    # Add labels
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height + 0.002,
                f'{height*100:.1f}%', ha='center', va='bottom', fontsize=9)

    # Formatting
    ax.set_xticks(x)
    ax.set_xticklabels([country_map.get(code, code) for code in ICT_cagr.index], rotation=45, ha='right')
    ax.set_ylabel('Average CAGR [%]')
    ax.set_title(title)

    plt.tight_layout()
    plt.show()


# Fig 2: output share data manipulation
def get_share(dfoutput, first_year, last_year, ICTsectors, value_column):
    #the output row from OECD is the output needed according to Tanveer - it includes import and HFCE etc. I checked.
    df_filtered2 = dfoutput.pivot_table(
    index=['country', 'sector'],
    columns='year',
    values=value_column
    ).reset_index()

    yearly_output = dfoutput.groupby(['country', 'year'])[value_column].sum().reset_index()
    yearly_output = yearly_output.rename(columns={value_column: f'total yearly {value_column}'})

    for year in range(int(first_year), int(last_year) + 1):
        # merge yearly_output with df_filtered2 to get total output for each country and year
        df_filtered2 = df_filtered2.merge(
            yearly_output[yearly_output['year'] == str(year)][['country', f'total yearly {value_column}']],
            on='country',
            how='left'
        )
        df_filtered2 = df_filtered2.rename(columns={f'total yearly {value_column}': f'total yearly {value_column} {year}'})

        df_filtered2[f'{value_column} share {year}'] = df_filtered2[str(year)] / df_filtered2[f'total yearly {value_column} {year}']

    # Define the years
    years = list(range(int(first_year), int(last_year) + 1))

    # Build the list of output share columns
    share_cols = [f'{value_column} share {year}' for year in years]

    # Slice the DataFrame
    shares = df_filtered2[['country', 'sector'] + share_cols].copy()

    # Calculate the average share across the selected years
    shares[f'average_{value_column}_share'] = shares[share_cols].mean(axis=1)

    ICT_shares = shares[shares['sector'].isin(ICTsectors)][['country', 'sector', f'average_{value_column}_share']].copy()

    return shares, ICT_shares

# plot fig 2: output share
def plot_share(ICT_shares, title,value_column):
    # Group by country and sort
    country_avg = ICT_shares.groupby('country')[f'average_{value_column}_share'].mean().sort_values(ascending=False)

    # Define colors
    colors = ['green' if country == 'CAN' else 'blue' for country in country_avg.index]

    # Plot
    plt.figure(figsize=(10, 6))
    bars = plt.bar(country_avg.index, country_avg.values, color=colors)

    # Adjust y-axis limit for label space
    max_height = country_avg.max()
    plt.ylim(0, max_height * 1.15)

    # Add percentage labels
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            height + max_height * 0.015,
            f'{height * 100:.1f}%',
            ha='center',
            va='bottom',
            fontsize=9
        )

    plt.ylabel(f'Average ICT {value_column} Share (%)')
    plt.title(title)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()

# fig2B: plot stacked output share
#def plot_stacked_output_shares(output_shares, ICT_factors, title):
def plot_stacked_shares(shares, ICT_factors, title, value_column):

    # Invert dictionary ICT_factors
    sector_to_category = {}
    for category, sectors in ICT_factors.items():
        if isinstance(sectors, list):
            for sector in sectors:
                sector_to_category[sector] = category
        else:
            sector_to_category[sectors] = category

    # Filter for ICT sectors
    ICTsectors = list(sector_to_category.keys())
    ICT_shares = shares.loc[shares['sector'].isin(ICTsectors), ['country', 'sector', f'average_{value_column}_share']].copy()

    # Map to ICT category
    ICT_shares['ICT_category'] = ICT_shares['sector'].map(sector_to_category)

    # Group by country and ICT_category, sum average_output_share
    grouped = ICT_shares.groupby(['country', 'ICT_category'])[f'average_{value_column}_share'].sum().unstack(fill_value=0)
                                                                                            # country and ICT_category are the index. unstack will create columns for each ICT_category
                                                                                            # fill_value=0 will fill NaN with 0
    # Reorder columns for consistent stacking: bottom to top
    desired_order = ['ICT - Manufacturing', 'ICT - Wholesaling', 'ICT - Software and computer services', 'ICT - Communications services']

    # Sum across ICT categories to get total ICT share per country, then sort descending
    grouped['total'] = grouped.sum(axis=1)
    grouped = grouped.sort_values('total', ascending=False).drop(columns='total')

    # Now `countries` is updated to match the new order
    countries = grouped.index.tolist()

    # Continue with plotting as before
    colors = ['#4CAF50', '#2196F3', '#FFC107', '#9C27B0']  # distinct colors
    bottom = np.zeros(len(countries))
    plt.figure(figsize=(10, 6))

    for idx, category in enumerate(desired_order):
        values = grouped[category].values
        #bars = plt.bar(countries, values, bottom=bottom, color=colors[idx], label=category)
        bars = plt.bar(countries, values * 100, bottom=bottom * 100, color=colors[idx], label=category)
        bottom += values
        
    # Add % labels on top
    for i, total in enumerate(bottom):
        plt.text(i, total * 100 + 0.2, f"{total * 100:.1f}%", ha='center', va='bottom', fontsize=9)

    #plt.ylabel('Average ICT Output Share')
    plt.ylabel(f'Average ICT {value_column} Share (%)')
    plt.title(title)
    plt.xticks(rotation=45, ha='right')
    plt.legend(title="ICT Category", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show()


# fig 3
def get_one_year_value(df, year, forward_or_backward, sector_list, value_column):
    if forward_or_backward == 'backward':
        col = 'buying sector'
    else:
        col = 'selling sector'
    #first slicing 
    one_year_impact = df[
        (df['year'] == year) & 
        (df[col].isin(sector_list))       
    ][['country', 'year', 'selling sector', 'buying sector', value_column, 'national GDP']]
    # division
    one_year_impact[value_column] = ( one_year_impact[value_column] / one_year_impact['national GDP'] )
    one_year_impact.drop(columns=['national GDP'], inplace=True)

    one_year_impact_grouped = one_year_impact.groupby(['country', 'year'], as_index=False)[value_column].sum()
    one_year_impact_grouped = one_year_impact_grouped.sort_values(by='GDP impact total', ascending=False)
    return one_year_impact_grouped


def plot_GDPimpact_side_by_side(
    first_year_backwards, last_year_backwards,
    first_year_forwards, last_year_forwards,
    value_column, graph_title):
    width = 0.35
    fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=True)

    # --- Panel 1: Backward Linkage ---
    ax = axes[0]
    last_year_backwards = last_year_backwards.sort_values(by=value_column, ascending=False)
    countries = last_year_backwards['country'].values

    first_year_backwards = first_year_backwards.set_index('country').loc[countries].reset_index()
    last_year_backwards = last_year_backwards.reset_index(drop=True)

    x = np.arange(len(countries))

    # Define colors
    colors_first = ['lightgreen' if c == 'CAN' else 'skyblue' for c in countries]
    colors_last = ['darkgreen' if c == 'CAN' else 'navy' for c in countries]

    bars1 = ax.bar(x - width/2, first_year_backwards[value_column], width,
                   label=f"{first_year_backwards['year'].iloc[0]}", color=colors_first)
    bars2 = ax.bar(x + width/2, last_year_backwards[value_column], width,
                   label=f"{last_year_backwards['year'].iloc[0]}", color=colors_last)

    for bar in bars1 + bars2:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}', xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)

    ax.set_title('Backward Linkage')
    ax.set_xlabel('Country')
    ax.set_xticks(x)
    ax.set_xticklabels(countries, rotation=45)
    ax.legend()

    # --- Panel 2: Forward Linkage ---
    ax = axes[1]
    last_year_forwards = last_year_forwards.sort_values(by=value_column, ascending=False)
    countries = last_year_forwards['country'].values

    first_year_forwards = first_year_forwards.set_index('country').loc[countries].reset_index()
    last_year_forwards = last_year_forwards.reset_index(drop=True)

    x = np.arange(len(countries))

    colors_first = ['lightgreen' if c == 'CAN' else 'skyblue' for c in countries]
    colors_last = ['darkgreen' if c == 'CAN' else 'navy' for c in countries]

    bars1 = ax.bar(x - width/2, first_year_forwards[value_column], width,
                   label=f"{first_year_forwards['year'].iloc[0]}", color=colors_first)
    bars2 = ax.bar(x + width/2, last_year_forwards[value_column], width,
                   label=f"{last_year_forwards['year'].iloc[0]}", color=colors_last)

    for bar in bars1 + bars2:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}', xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)

    ax.set_title('Forward Linkage')
    ax.set_xlabel('Country')
    ax.set_xticks(x)
    ax.set_xticklabels(countries, rotation=45)
    ax.legend()

    fig.supylabel(value_column)
    fig.suptitle(f'{graph_title}, {value_column}: Comparison of {first_year_backwards["year"].iloc[0]} and {last_year_backwards["year"].iloc[0]}')
    plt.tight_layout()
    plt.show()




def plot_GDPimpact_top_bottom(
    first_year_backwards, last_year_backwards,
    first_year_forwards, last_year_forwards,
    value_column, graph_title):

    width = 0.35
    fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=False)

    # --- Panel 1: Backward Linkage ---
    ax = axes[0]
    last_year_backwards = last_year_backwards.sort_values(by=value_column, ascending=False)
    countries = last_year_backwards['country'].values

    first_year_backwards = first_year_backwards.set_index('country').loc[countries].reset_index()
    last_year_backwards = last_year_backwards.reset_index(drop=True)

    x = np.arange(len(countries))
    colors_first = ['lightgreen' if c == 'CAN' else 'skyblue' for c in countries]
    colors_last = ['darkgreen' if c == 'CAN' else 'navy' for c in countries]

    bars1 = ax.bar(x - width/2, first_year_backwards[value_column], width, color=colors_first)
    bars2 = ax.bar(x + width/2, last_year_backwards[value_column], width, color=colors_last)

    for bar in bars1 + bars2:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}', xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)

    ax.set_title('Backward Linkage')
    ax.set_ylabel(value_column)
    ax.set_xticks(x)
    ax.set_xticklabels(countries, rotation=45)

    # Custom legend (light blue = first year, dark blue = last year)
    custom_legend = [
        Patch(facecolor='skyblue', label=str(first_year_backwards['year'].iloc[0])),
        Patch(facecolor='navy', label=str(last_year_backwards['year'].iloc[0]))
    ]
    ax.legend(handles=custom_legend)

    # --- Panel 2: Forward Linkage ---
    ax = axes[1]
    last_year_forwards = last_year_forwards.sort_values(by=value_column, ascending=False)
    countries = last_year_forwards['country'].values

    first_year_forwards = first_year_forwards.set_index('country').loc[countries].reset_index()
    last_year_forwards = last_year_forwards.reset_index(drop=True)

    x = np.arange(len(countries))
    colors_first = ['lightgreen' if c == 'CAN' else 'skyblue' for c in countries]
    colors_last = ['darkgreen' if c == 'CAN' else 'navy' for c in countries]

    bars1 = ax.bar(x - width/2, first_year_forwards[value_column], width, color=colors_first)
    bars2 = ax.bar(x + width/2, last_year_forwards[value_column], width, color=colors_last)

    for bar in bars1 + bars2:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}', xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)

    ax.set_title('Forward Linkage')
    ax.set_ylabel(value_column)
    ax.set_xticks(x)
    ax.set_xticklabels(countries, rotation=45)
    ax.legend(handles=custom_legend)

    fig.suptitle(f'{graph_title}, {value_column}: Comparison of {first_year_backwards["year"].iloc[0]} and {last_year_backwards["year"].iloc[0]}')
    plt.tight_layout()
    plt.show()




def plot_GDPimpact_wrapper(dfGDPimpact, first_year, last_year, sector_list, value_column, sector_label):
    #this function uses the plot function above to plot 4 different categories of the ICT sector
    # Extract data for backward and forward linkages
    first_year_backward = get_one_year_value(dfGDPimpact, first_year, 'backward', sector_list, value_column)
    last_year_backward = get_one_year_value(dfGDPimpact, last_year, 'backward', sector_list, value_column)
    first_year_forward = get_one_year_value(dfGDPimpact, first_year, 'forward', sector_list, value_column)
    last_year_forward = get_one_year_value(dfGDPimpact, last_year, 'forward', sector_list, value_column)

    # Plot using existing plotting function
    plot_GDPimpact_top_bottom(first_year_backward, last_year_backward,
                              first_year_forward, last_year_forward,
                             'GDP impact total', sector_label)
    # Optionally set a custom plot title
    #plt.suptitle(f'{value_column} for {sector_label}', fontsize=14)
    #plt.tight_layout()
    #plt.show()




##################################################             old functions               ######################################################

def multipliers2prediction(s2s_mo, fdf_year2, column_name):
    predicted_output_year2_np  = np.round(s2s_mo.to_numpy() @ fdf_year2.values.reshape(-1, 1), 1)
    
    predicted_output_year2 = pd.DataFrame(predicted_output_year2_np, index=s2s_mo.index, columns=[column_name])
    
    return predicted_output_year2



 
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@                    main                  @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
start_time = time.time()
print("working directory of GDPsupplychain.py is: ",os.getcwd())  # Print the current working directory

table_type = 'TTL' #or'DOM'   
OECD_path = "../Data/" # windows style: r".\\"
if table_type == 'DOM':
    output_filename = '/mnt/c/NavitComputer24/2024_NES/Economics/Textbook_EIA/OECD_salaries/EIA_matrices.xlsx'
elif table_type == 'TTL':
    output_filename = '/mnt/c/NavitComputer24/2024_NES/Economics/Textbook_EIA/OECD_salaries/EIA_TTL_matrices.xlsx'

first_year = '2011'
last_year = '2020'
year_range = [str(year) for year in range(int(first_year), int(last_year) + 1)]
report_title = f'ICT sectors, {last_year}'
ICT_factors = {'ICT - Manufacturing': 'C26',
                'ICT - Wholesaling': 'G',
                'ICT - Software and computer services': ['J58T60', 'J62_63', 'M'],  
                'ICT - Communications services': 'J61'}
ICTsectors = ['C26', 'G', 'J58T60', 'J62_63', 'M', 'J61']

country_names = ['Canada', 'The United States', 'Great Britain', 'France', 'Germany', 'Italiy', 'Japan']
countries = ['CAN', 'USA', 'GBR', 'FRA', 'DEU', 'ITA', 'JPN'] # 'CHN' is not available in OECD, but it is in OECDadditional
country_map = dict(zip(countries, country_names))

currency_exchange_type = 'EXCH' #'EXCH' or 'PPP'

fixed_sectors = ['A01_02', 'A03', 'B05_06', 'B07_08', 'B09', 'C10T12', 'C13T15', 'C16', 'C17_18', 'C19', 'C20', 'C21', 'C22', 'C23', 'C24', 
                 'C25', 'C26', 'C27', 'C28', 'C29', 'C30', 'C31T33', 'D', 'E', 'F', 'G', 'H49', 'H50', 'H51', 'H52', 'H53', 'I', 'J58T60', 'J61',
                  'J62_63', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T']



# 1. Get IO=II, X, GDP, from OECD, compensation of employees, more GDP and II from OECDadditional as well as taxes, incomegross surplus etc.
##########################################################################################################################################   


# to delete:
#single values in OECD:
#GDP_of_household_expenditure = OECD.loc['VALU', 'HFCE']
#GDP_of_total_column = OECD.loc['VALU', 'TOTAL'] # total is the output, should be equal to f_row_sums.sum(axis=0)
#GDP_of_final_demand = OECD.loc['VALU', final_demand_columns]        #this could be added to the rows from the right or to the columns form the bottom
#output_of_final_demand = OECD.loc['OUTPUT', final_demand_columns]   #probably will not be needed

# from looking at the numbers:
# total = output
# II_row_sums + f_row_sums = total = output
# household_expenditure is the column added to II to get the closed model
# when uploading data for the first time run:
# data_exploration_flags(II,household_expenditure,other_final_demand,output,output_of_final_demand,OECD_rough)

#final demand and value added are not the same at all
final_demand_columns = ['HFCE',	'NPISH',	'GGFC',	'GFCF',	'INVNT',	'CONS_NONRES', 'EXPO'] # 'IMPO', 'DPABR', 
#other_final_demand = OECD.loc[simple_II_labels, final_demand_columns[1:]] #exluding HFCE - household expenditure

dfoutput = pd.DataFrame() # this will hold output by country, year, sector, output
dfGDP = pd.DataFrame() # this will hold the GDP by country, year, sector, GDP
dfGDPimpact = pd.DataFrame() # this will hold country, year, buying sector, selling sector, GDPimpact
dftemp = pd.DataFrame()
for country in countries:
    for year in year_range:
        
        # I have decided on the format: I'll put GDPimpact in a dfGDPimpact. I need for that the whole impact code
        PPP_or_exch, OECD, simple_II_labels, OECDadditional, sector_description =  data_upload_OECD_salaries(year, currency_exchange_type, table_type, country)
        # the following is calculated twice: in data_upload_OECD_salaries and here. I want to leave it here, but I also need it there - do I??
        II = OECD.loc[simple_II_labels, simple_II_labels]
        household_expenditure = OECD.loc[simple_II_labels, 'HFCE']
        
        GDP         = OECD.loc['VALU', simple_II_labels]
        output      = OECD.loc['OUTPUT', simple_II_labels]
        
        dftemp = output.reset_index()
        dftemp.columns = ['sector', 'output']
        dftemp['country'] = country
        dftemp['year'] = year
        dftemp = dftemp[['country', 'year', 'sector', 'output']]
        dfoutput = pd.concat([dfoutput, dftemp], ignore_index=True)

        dftemp = pd.DataFrame()
        dftemp = GDP.reset_index()
        dftemp.columns = ['sector', 'GDP']
        dftemp['country'] = country
        dftemp['year'] = year
        dftemp = dftemp[['country', 'year', 'sector', 'GDP']]
        dfGDP = pd.concat([dfGDP, dftemp], ignore_index=True)

        # 2. calculate L and Lc
        ##########################
        T = safe_divide(II, output)
        Ldf, L_minus_I = clc_L(T)

        IIc = II.copy()
        IIc["HFCE"] = household_expenditure # added a column for closed model
        IIc.loc['employees_compensation'] = OECDadditional['employees_compensation'] #If I wanted a column I would have written IIC['employees_compensation']
        IIc.loc['employees_compensation', 'HFCE'] = 0 

        outputc = output.copy()
        outputc['HFCE'] = OECDadditional['employees_compensation'].sum()
        Tc = safe_divide(IIc, outputc)
        Lcdf, Lc_minus_I = clc_L(Tc)


        # 3. calculate multipliers
        #############################
        mo = Ldf.sum(axis=0)                       #dollar's worth of outcome per 1 dollar's worth of new final demand
        moc_trancated = Lcdf.iloc[:-1].sum(axis=0) #dollar's worth of outcome per 1 dollar's worth of new final demand

        # income multipliers mh
        Ej_by_xj = Tc.iloc[-1,:-1] #hosehold income received per dollar's worth of sector output  
        income_F_multipliers = Ldf.mul(Ej_by_xj, axis=0) #household income recieved per dollar's worth of secotr final demand
        # Ej/xj*Ljk - Ljk is how much output was sold from j to k. and j is the sector that paid the salaries, so Ej/xj is used.
        sum_income_F_multipliers = income_F_multipliers.sum(axis=0) 
        # m(h)_k = sum_j(Ej/xj*Ljk) - sum over j of the detailed income_F_multipliers - sum over the rows
        # an additional dolar of final demand in sector k generates m(h)_k dollars of new household income when all direct and
        # indirect effects are converted into dollar estimates of income.
        # income_F_multipliers is the details for each sector - how much income is generated by an additional dollar of final demand in sector k for each of the other sectors
        # the above is only direct+indirect effects
        # direct + indirect + induced effect - same calculation but with Lcdf

        #income multipliers second time
        Ej_by_xj = Tc.iloc[-1,:]
        
        # GDP multipliers
        GDPc = OECD.loc['VALU', simple_II_labels + ['HFCE']]
        GDPj_by_xj = safe_divide_vector(GDPc, outputc)

        # summary of multipliers without typeI and typeII - 
        # 6 multipliers output, income, GDP, X sector2sector X simple model, closed model
        # all of the closed model multipliers are trancated (the row and column of salaries and final demand are not included)
        s2s_mo = Ldf                       # direct + indirect effect
        s2s_moc = Lcdf                     # direct + indirect + iduced effect
        s2s_mh = Ldf.mul(Ej_by_xj.iloc[ :-1 ], axis=0) 
        s2s_mhc = Lcdf.mul(Ej_by_xj.rename(index={'HFCE': 'employees_compensation'}), axis=0)
        s2s_mg =  Ldf.mul(GDPj_by_xj.iloc[ :-1 ], axis=0)    
        s2s_mgc = Lcdf.mul(GDPj_by_xj.rename(index={'HFCE': 'employees_compensation'}), axis=0)
        #sector2market multipliers
        #mo = s2s_mo.sum(axis=0)
        #moc = s2s_moc.sum(axis=0)
        #mh = s2s_mh.sum(axis=0)
        #mhc = s2s_mhc.sum(axis=0)
        #mg = s2s_mg.sum(axis=0)
        #mgc = s2s_mgc.sum(axis=0)


        ###################################################
        # multipliers: direct, indirect, induced separately
        ###################################################
        n = T.shape[0]
        # direct
        direct_o = pd.DataFrame(np.eye(n), index=s2s_mo.index, columns=s2s_mo.columns)
        direct_h = pd.DataFrame(np.zeros((n, n)), index=Ej_by_xj.iloc[:-1].index, columns=Ej_by_xj.iloc[:-1].index)
        np.fill_diagonal(direct_h.values, Ej_by_xj.values)
        direct_g = pd.DataFrame(np.zeros((n, n)), index=GDPj_by_xj.iloc[:-1].index, columns=GDPj_by_xj.iloc[:-1].index)
        np.fill_diagonal(direct_g.values, GDPj_by_xj.values)
        #indirect
        indirect_o = s2s_mo - direct_o
        #Ej_by_xj*L_minus_I = s2s_mh-Ej_by_xj
        indirect_h  = s2s_mh - direct_h
        #GDPj_by_xj*L_minus_I = s2s_mg-GDPj_by_xj
        indirect_g  = s2s_mg - direct_g
        #induced
        induced_o = s2s_moc.iloc[:-1,:-1] - s2s_mo
        induced_h = s2s_mhc.iloc[:-1,:-1] - s2s_mh
        induced_g = s2s_mgc.iloc[:-1,:-1] - s2s_mg

        #################################
        # impacts instead of multipliers
        #################################
        fdf = OECD.loc[simple_II_labels, final_demand_columns].sum(axis=1)
        #there is what causes closed model to be in accuarete:
        #fcdf_year2 = OECD_year2.loc[simple_II_labels,final_demand_columns[1:]].sum(axis=1)
        #I should take HFCE inside fcdf_year2. 
        fcdf = OECD.loc[simple_II_labels,final_demand_columns].sum(axis=1)
        fcdf.loc['employees_compensation'] = 0

        # impacts
        # multipliers_by_f returns a vector, and I want a matrix. I need to do the multiplication again
        scale_df_by_series(direct_o, fcdf[:-1]) # , 'Direct output impact' 
        #multipliers_by_f(indirect_o, fcdf[:-1], 'Indirect output impact'),
        #multipliers_by_f(induced_o, fcdf[:-1], 'Induced output impact'),  
        #multipliers_by_f(s2s_moc.iloc[:-1,:-1], fcdf[:-1], 'Total output impact'),
        #multipliers_by_f(direct_h, fcdf[:-1], 'Direct income impact'), 
        #multipliers_by_f(indirect_h, fcdf[:-1], 'Indirect income impact'),
        #multipliers_by_f(induced_h, fcdf[:-1], 'Induced income impact'),  
        #multipliers_by_f(s2s_mhc.iloc[:-1,:-1], fcdf[:-1], 'Total income impact'),
        #multipliers_by_f(direct_g, fcdf[:-1], 'Direct GDP impact'), 
        #multipliers_by_f(indirect_g, fcdf[:-1], 'Indirect GDP impact'),
        #multipliers_by_f(induced_g, fcdf[:-1], 'Induced GDP impact'),  
        #multipliers_by_f(s2s_mgc.iloc[:-1,:-1], fcdf[:-1], 'Total GDP impact'),  
        
        GDPimpact_cols = ['GDP impact direct', 'GDP impact indirect', 'GDP impact induced', 'GDP impact total']
        dftemp2 = None
        for data, value in zip( [direct_g, indirect_g, induced_g, s2s_mgc.iloc[:-1, :-1]], GDPimpact_cols ):
            m = scale_df_by_series(data, fcdf[:-1])       #this is the multiplication
            dftemp1 = pivot_matrix_to_3_columns(m, value) #this is the matrix in 3 columns
            if dftemp2 is None:
                dftemp2 = dftemp1  # First iteration: just assign
            else:
                dftemp2 = pd.merge(
                    dftemp2,
                    dftemp1,
                    on=["selling sector", "buying sector"],
                    how="outer"
                )
        # dftemp2 contains 4 GDP impacts 
        dftemp2['country'] = country
        dftemp2['year'] = year
        dftemp2['national GDP'] = GDP.sum()
        cols = ['country', 'year', 'buying sector', 'selling sector'] + GDPimpact_cols + ['national GDP']
        dftemp2 = dftemp2[cols]
        dfGDPimpact = pd.concat([dfGDPimpact, dftemp2], ignore_index=True)
        #print(country, year, 'done')
        


end_time = time.time()
print(f"Elapsed time: {(end_time - start_time)/60:.1f} minutes")


##########################################             Benchmark  plots            ######################################################

print(f'Fig 1: ICT Sector Revenue Compound Annual Growth Rate (CAGR) ({first_year}-{last_year})')
# graph 1,2 for output
if 0:
    # fig 1: output CAGR 
    ICT_cagr = clc_cagr(dfoutput, first_year, last_year,'output')
    # fig1: plot output CAGR
    plot_cagr(ICT_cagr, f'Average CAGR for ICT sectors ({first_year}–{last_year})')


    print(f'Fig 2: Average ICT Sector Share in Total National Output ({first_year}-{last_year})')
    # fig 2: average ICT sector share in total output 2010-2020
    # data manipulation for figure 2: output share of ICT sectors
    output_shares, ICT_output_shares = get_share(dfoutput, first_year, last_year, ICTsectors,'output')
    # TODO: I'm not sure if ICT_output_shares should be in data manipulation or plotting
    plot_share(ICT_output_shares, f'Average ICT Output Share by Country, {first_year}-{last_year}','output')
    #the above is average of average - average over the 6 ICT sectorsa as well as over the years

    # fig2B: stacked output share
    #this is the average of each category (factor) - stacked. 
    plot_stacked_shares(output_shares, ICT_factors,f'Stacked Average ICT Output Share by Country, {first_year}-{last_year}','output')


# graphs 1 and 2 for GDP
if 0:
    # fig 1: output CAGR 
    ICT_GDP_cagr = clc_cagr(dfGDP, first_year, last_year,'GDP') 
    # fig1: plot output CAGR
    plot_cagr(ICT_GDP_cagr, f'Average GDP CAGR for ICT sectors ({first_year}–{last_year})')

    # fig 2: average ICT sector share in GDP 2011-2020
    GDP_shares, ICT_GDP_shares = get_share(dfGDP, first_year, last_year, ICTsectors,'GDP')
    plot_share(ICT_GDP_shares, f'Average ICT GDP Share by Country, {first_year}-{last_year}','GDP')

    # fig2B: stacked output share
    #this is the average of each category (factor) - stacked. 
    plot_stacked_shares(GDP_shares, ICT_factors,f'Stacked Average ICT GDP Share by Country, {first_year}-{last_year}','GDP')

print('graphs 1 and 2 are done')


# graph 3: GDP impact of ICT sectors total, 5 graphs
if 0:
    ICT_first_year_backward_impact= get_one_year_value(dfGDPimpact, first_year,'backward', ICTsectors, 'GDP impact total')
    ICT_last_year_backward_impact = get_one_year_value(dfGDPimpact, last_year,'backward', ICTsectors, 'GDP impact total')
    ICT_first_year_forward_impact= get_one_year_value(dfGDPimpact, first_year,'forward', ICTsectors, 'GDP impact total')
    ICT_last_year_forward_impact = get_one_year_value(dfGDPimpact, last_year,'forward', ICTsectors, 'GDP impact total')
    plot_GDPimpact_top_bottom( ICT_first_year_backward_impact, ICT_last_year_backward_impact,
                            ICT_first_year_forward_impact, ICT_last_year_forward_impact,
                            'GDP impact total','ICT' )

    for sector_label, sector_list in ICT_factors.items():
        if isinstance(sector_list, str):
            sector_list = [sector_list]
        plot_GDPimpact_wrapper(dfGDPimpact, first_year, last_year, sector_list, 'GDP impact total', sector_label)
        # plot_GDPimpact_top_bottom is inside it

# graph 4 GDP stacked backward forward

ICT_first_year_backward_impact= get_one_year_value(dfGDPimpact, first_year,'backward', ICTsectors, 'GDP impact total')
ICT_last_year_backward_impact = get_one_year_value(dfGDPimpact, last_year,'backward', ICTsectors, 'GDP impact total')
ICT_first_year_forward_impact= get_one_year_value(dfGDPimpact, first_year,'forward', ICTsectors, 'GDP impact total')
ICT_last_year_forward_impact = get_one_year_value(dfGDPimpact, last_year,'forward', ICTsectors, 'GDP impact total')

import matplotlib.pyplot as plt
import pandas as pd

def plot_stacked_ict_impact(backward_df, forward_df, year, value_col, title):
    """
    Plot backward and forward ICT GDP impacts stacked by country for a given year,
    using green bars for Canada and purple bars for others.

    Parameters:
        backward_df (pd.DataFrame): DataFrame with backward impact values.
        forward_df (pd.DataFrame): DataFrame with forward impact values.
        year (int or str): Year to filter by.
        value_col (str): Name of the column holding the impact value.
        title (str): Title for the plot.
    """
    # Filter for the given year and reindex
    back = backward_df[backward_df['year'] == year][['country', value_col]].set_index('country')
    fwd = forward_df[forward_df['year'] == year][['country', value_col]].set_index('country')

    # Align and fill missing values
    back, fwd = back.align(fwd, join='outer', fill_value=0)

    # Sort by total impact
    total = back[value_col] + fwd[value_col]
    sorted_countries = total.sort_values(ascending=False).index

    # Sort the data
    back_sorted = back.loc[sorted_countries]
    fwd_sorted = fwd.loc[sorted_countries]

    # Create the bar plot
    fig, ax = plt.subplots(figsize=(12, 6))
    for i, country in enumerate(sorted_countries):
        back_val = back_sorted.loc[country, value_col]
        fwd_val = fwd_sorted.loc[country, value_col]
        total_val = back_val + fwd_val

        # Choose colors
        if country == 'CAN':
            back_color = 'forestgreen'
            fwd_color = 'lightgreen'
        else:
            back_color = 'indigo'
            fwd_color = 'orchid'

        # Plot bars
        ax.bar(i, back_val, color=back_color)
        ax.bar(i, fwd_val, bottom=back_val, color=fwd_color)

        # Add percentage label
        ax.text(i, total_val + 0.01, f'{total_val * 100:.1f}%', ha='center', va='bottom', fontsize=9)

    # Final plot settings
    ax.set_title(f"{title} in {year}", fontsize=14)
    ax.set_ylabel('GDP Impact')
    ax.set_xlabel('Country')
    ax.set_xticks(range(len(sorted_countries)))
    ax.set_xticklabels(sorted_countries, rotation=45)

    # Legend
    from matplotlib.patches import Patch
    legend_handles = [
        Patch(color='indigo', label='Backward (others)'),
        Patch(color='orchid', label='Forward (others)'),
        Patch(color='forestgreen', label='Backward (CAN)'),
        Patch(color='lightgreen', label='Forward (CAN)')
    ]
    ax.legend(handles=legend_handles)

    ax.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()



plot_stacked_ict_impact(ICT_last_year_backward_impact, ICT_last_year_forward_impact, year, 'GDP impact total', 'ICT GDP Impact')






print('')


##############################  calculating and plotting predictions  ################################
'''
        predicted_output = multipliers2prediction(s2s_mo, fdf, 'Predicted_Output')
        predicted_outputc = multipliers2prediction(s2s_moc, fcdf, 'Predicted_Output')
        predicted_income = multipliers2prediction(s2s_mh, fdf, 'Predicted_Income')  
        predicted_incomec = multipliers2prediction(s2s_mhc, fcdf, 'Predicted_Income') 
        predicted_GDP = multipliers2prediction(s2s_mg, fdf, 'Predicted_GDP') 
        predicted_GDPc = multipliers2prediction(s2s_mgc, fcdf, 'Predicted_GDP') 

        plot_real_vs_predicted(output, predicted_output,
                       OECDadditional['employees_compensation'], predicted_income,
                       GDP, predicted_GDP,  
                       year, year,'Simple Model')

        plot_real_vs_predicted(output, predicted_outputc.iloc[:-1],
                       OECDadditional['employees_compensation'], predicted_incomec.iloc[:-1],
                       GDP, predicted_GDPc.iloc[:-1],  
                       year, year,'Closed Model')
'''

##############################              ICT old         #############################                      
# bar graphs of direct, indirect and induced
'''
ICT_sectors = ['ICT - Manufacturing', 'ICT - Wholesaling', 'ICT - Software and computer services', 'ICT - Communications services',
               'ICT - Software and computer services',	'ICT - Software and computer services']
OECD_sectors_ICT = ['C26',	'G',	'J58T60',	'J61',	'J62_63',	'M']
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

# assume I want to see the ICT sectors as selling sectors. how much they will sell
plot_multipliers(OECD_sectors_ICT, direct_o.loc[OECD_sectors_ICT,:].sum(axis=1), indirect_o.loc[OECD_sectors_ICT,:].sum(axis=1), 
                 induced_o.loc[OECD_sectors_ICT,:].sum(axis=1),
                 direct_h.loc[OECD_sectors_ICT,:].sum(axis=1), indirect_h.loc[OECD_sectors_ICT,:].sum(axis=1),
                 induced_h.loc[OECD_sectors_ICT,:].sum(axis=1),
                 direct_g.loc[OECD_sectors_ICT,:].sum(axis=1), indirect_g.loc[OECD_sectors_ICT,:].sum(axis=1),
                 induced_g.loc[OECD_sectors_ICT,:].sum(axis=1), 
                  title="Multipliers")
'''




