def compute_E_G_ratio(dfEtotal, worldbank_gdp_data,countries, year_range):
    
    # Initialize output with same structure
    dfE_G_ratio = pd.DataFrame(index=year_range, columns=worldbank_gdp_data.columns[1:])
    
    # Loop through each country column (skip 'Time')
    for country in countries:
        for year in year_range:
            if int(year) not in worldbank_gdp_data['year'].values:
                raise ValueError(f"Year {year} not found in worldbank_gdp_data 'year' column.")
            
            gdp_temp = worldbank_gdp_data[worldbank_gdp_data['year'] == int(year)][country].values[0]
            if gdp_temp == 0:
                raise ValueError(f"GDP value for country {country} in year {year} is zero, cannot compute ratio.")
            else: 
                 ratio= dfEtotal[  (dfEtotal.year==year) & (dfEtotal.country=='ITA')].Etotal.values[0] / gdp_temp
                 dfE_G_ratio.loc[ year, country] = ratio
    return dfE_G_ratio





def compute_E_G_ratio(dfEtotal, worldbank_gdp_data, countries, year_range):
    
    dfE_G_ratio = pd.DataFrame(index=year_range, columns=worldbank_gdp_data.columns)
    for country in countries:
        for year in year_range:
            if int(year) not in worldbank_gdp_data.index:
                raise ValueError(f"Year {year} not found in worldbank_gdp_data index.")
            
            gdp_temp = worldbank_gdp_data.loc[int(year), country]
            
            if gdp_temp == 0:
                raise ValueError(f"GDP value for country {country} in year {year} is zero, cannot compute ratio.")
            else: 
                ratio = (
                    dfEtotal[(dfEtotal.year == year) & (dfEtotal.country == country)].Etotal.values[0]
                    / gdp_temp
                )
                dfE_G_ratio.loc[year, country] = ratio
    
    return dfE_G_ratio