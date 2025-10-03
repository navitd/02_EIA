# auxiliary file to combine 2010 compensation of employees with 2011-2020 data
# additionalOECD has detailed sector E 2011-2020
# salaries_1995_2010 has 7 files, one for each country, with 2010 all sectors data

# I download data again from https://data-explorer.oecd.org/vis?df[ds]=dsDisseminateFinalDMZ&df[id]=DSD_NASU%40DF_USEVA_T1600&df[ag]=OECD.SDD.NAD&df[vs]=1.0&hc[Transaction]=Output&pg=0&snb=53&tm=input-output&utm_source=chatgpt.com&dq=A.CAN%2BFRA%2BDEU%2BITA%2BJPN%2BUSA%2BGBR.D1.A%2BB%2BC%2BD%2BE%2BF%2BG%2BH%2BI%2BJ%2BK%2BL%2BM%2BN%2BO%2BP%2BQ%2BR%2BS%2BT%2BU%2BA01%2BA02%2BA03%2BB05%2BB06%2BB07%2BB08%2BB09%2BC10T12%2BC13T15%2BC16%2BC17%2BC18%2BC19%2BC20%2BC21%2BC22%2BC23%2BC24%2BC25%2BC26%2BC27%2BC28%2BC29%2BC30%2BC31_32%2BC33%2BE36%2BE37T39%2BF41%2BF42%2BG45%2BG46%2BG47%2BH49%2BH50%2BH51%2BH52%2BH53%2BI55%2BI56%2BJ58%2BJ59_60%2BJ61%2BJ62_63%2BK64%2BK65%2BK66%2BL68A%2BL68B%2BM69_70%2BM71%2BM72%2BM73%2BM74_75%2BN77%2BN78%2BN79%2BN80T82%2BQ86%2BQ87_88%2BR90T92%2BR93%2BS94%2BS95%2BS96%2BT97....V.&pd=2010%2C2022&to[TIME_PERIOD]=false&vw=tb



import pandas as pd
# upload 2010 data and check for missing data
file_path = '/mnt/c/NavitComputer24/2024_NES/Economics/Data/OECDsalaries/OECD E 88 sectors 2010-2022 G7.csv'
data_rough = pd.read_csv(file_path)
data_rough.head()




print('data_rough.columns')






'''

# 2. Load the Excel file for OECD PPP table (OECD salaries are in local currency)
    file_path = '/mnt/c/NavitComputer24/2024_NES/Economics/Data/OECDsalaries/UTF-8OECD - XY Rates.csv'
    PPP_cols_to_load = ['LOCATION', 'TIME_PERIOD', 'INDICATOR', 'OBS_VALUE']
    PPP_rough = pd.read_csv(file_path, usecols=PPP_cols_to_load)
    PPP_filtered = PPP_rough[
        (PPP_rough['LOCATION'] == country) &
        (PPP_rough['TIME_PERIOD'] == int(year)) &
        (PPP_rough['INDICATOR'] == currency_exchange_type) ]
    PPP_or_exch = PPP_filtered['OBS_VALUE'].iloc[0]





additional_filepath = "/mnt/c/NavitComputer24/2024_NES/Economics/Data/OECDsalaries/additionalOECD.csv"
additional_data_rough = pd.read_csv(additional_filepath)
# Keep only columns where there is more than one unique value
data2 = additional_data_rough.loc[:, additional_data_rough.nunique() > 1]
data2 = data2[data2.REF_AREA == country] # keep only the rows for the country
data2 = data2.rename(columns={"ACTIVITY": "detailed_sectors"})
# to look at the titles of the detailed sectors
data2_descriptions = data2[(data2["TIME_PERIOD"] ==int(year)) ] #.drop(columns=['Reference area','TIME_PERIOD','Transaction','OBS_VALUE','ACCOUNTING_ENTRY',
                                                                #            'OBS_STATUS','Currency'])
sector_description = dict(zip(data2_descriptions['detailed_sectors'], data2_descriptions['Economic activity']))

#year = re.search(r'\d{4}', OECD_name).group() #this is a function and the year is an input variable

# 4.2 putting data2 in OECD_additionaol_data
# columns in data2: Transaction - GDP, salaries, taxes, etc.
# detailed_sectors, Economic Activity - A, M, G, etc.
# VALUATIONI, Valuation - Purchasers price, not applicable, basic price
# TIME_PERIOD, OBS_VALUE = year and value
# ACCOUNTING_ENTRY, Accounting entry - Expenditure, Balance (revenue minus expenditure), Revenue

transaction_names = ['Value added, gross', 'Other taxes less other subsidies on production', 'Operating surplus and mixed income, net', 
                    'Wages and salaries', 'Compensation of employees']
column_names = ['GDP', 'net_taxes_on_production', 'surplus_and_mixed_income_net', 
                'salaries', 'employees_compensation' ]


OECDadditional = pd.DataFrame()
for ix, name in enumerate(transaction_names):     
    one_transaction_type= data2[(data2["TIME_PERIOD"] == int(year)) & (data2["Transaction"] == name)].drop(columns=["Economic activity","TIME_PERIOD","Transaction", 
                                                                                                                    "TRANSACTION",
                                                                                                                    'Reference area','TIME_PERIOD','Transaction','ACCOUNTING_ENTRY',
                                                                                                                    'OBS_STATUS','Currency'])
    # now GSPstatcan is with detailed OECD codes and we need to translate it to known OECD codes
    # from A01 and A02 to A01_02
    one_transaction_type['OECD_codes'] = one_transaction_type['detailed_sectors'].map(mapping_dict)
    one_transaction_type = one_transaction_type.sort_values(by="OECD_codes")

    # sum A01 and A02 to A01_02
    # Group by OECD_codes and sum the OBS_VALUE column
    one_transaction_type_grouped = one_transaction_type.groupby('OECD_codes', as_index=False)['OBS_VALUE'].sum()
    # GDPstatcan_grouped has OECD sectors but also other sectors. it has 95 rows. but the OECD sectors are correct (summed correctly)
    # I checked.
    
    # convert CAD to USD by PPP_or_exch
    one_transaction_type_grouped['OBS_VALUE_USD'] = (one_transaction_type_grouped['OBS_VALUE'] / PPP_or_exch).round(1)
    one_transaction_type_grouped.drop(columns=['OBS_VALUE'], inplace=True)
    
    # last step:
    # choose from it only codes that appear in OECD:
    if 'J' not in simple_II_labels:
        simple_II_labels_plus_J = simple_II_labels + ['J']
    df = one_transaction_type_grouped.set_index('OECD_codes').reindex(simple_II_labels_plus_J, fill_value=0).copy()   

    # Add to statcan_data under the corresponding column name
    OECDadditional[column_names[ix]] = df['OBS_VALUE_USD']

# from J to a correct value of J61
if "j61" not in OECDadditional.index:
    OECDadditional.loc["J61"] = OECDadditional.loc["J"] - OECDadditional.loc["J58T60"] - OECDadditional.loc["J62_63"]   
OECDadditional = OECDadditional.drop("J")
'''