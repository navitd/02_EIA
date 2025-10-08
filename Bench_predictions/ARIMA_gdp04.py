import pandas as pd
import matplotlib.pyplot as plt
import sys
from pathlib import Path
import os
# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent / 'EIAfunctions'))
from func_clean_world_bank_data import clean_world_bank_data
import warnings
from sklearn.metrics import mean_squared_error
import pmdarima as pm

# Ignore FutureWarnings from sklearn specifically
warnings.simplefilter(action='ignore', category=FutureWarning)

# Optional: ignore all warnings
warnings.simplefilter(action='ignore')


def get_worldbank_gdp_data(plot_flag):

    # Define the data directory relative to the script location
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    GDP_filename = os.path.join(SCRIPT_DIR, '..', '..', 'Data', 'World Bank G7 GDP', 
                            'cb6272d5-797d-4d20-970a-1286e5b13605_Data.csv')
    #Data from database: World Development Indicators
    #Last Updated: 07/01/2025

    # Add error handling for file loading

    if not os.path.exists(GDP_filename):
        raise FileNotFoundError(f"Data file not found at: {GDP_filename}")

    rough = pd.read_csv(GDP_filename)
    print(f"Successfully loaded data with shape: {rough.shape}")
        
    worldbank_gdp_data, file_description = clean_world_bank_data(rough)

    print("\n dataframe data:\n")
    print(worldbank_gdp_data.head())

    # Plotting
    if plot_flag:
        countries = data.columns[1:]  # all country columns
        plt.figure(figsize=(10, 6))

        for country in countries:
            plt.plot(data['Time'], data[country], marker = 'o',label=country)
            plt.text(data['Time'].iloc[-1], data[country].iloc[-1], country, 
                    fontsize=9, verticalalignment='center')

        plt.xlabel('Year')
        plt.ylabel(file_description[2])  
        plt.title('file_description[2] of countries')
        plt.grid(True)
        plt.legend()  
        plt.show()

        # Trending
        max_data_years = data.Time.max()
        past_years = 10


    return worldbank_gdp_data



def plot_gdp_forecast(worldbank_gdp_data, forecast_gdp, countries):
    
    plt.figure(figsize=(12, 6))

    for country in countries:
        # Plot historical data and get the color assigned
        line_actual, = plt.plot(worldbank_gdp_data.index, worldbank_gdp_data[country], label=f"{country} actual")
        color = line_actual.get_color()
        
        # Plot forecasted data with the same color
        plt.plot(forecast_gdp.index, forecast_gdp[country], linestyle='--', color=color, label=f"{country} forecast")

    plt.xlabel("Year")
    plt.ylabel("GDP (current USD)")
    plt.title("Historical and Forecasted GDP")
    plt.legend()
    plt.grid(True)
    plt.show()


# 01 upload gdp data
worldbank_gdp_data = get_worldbank_gdp_data(False)
worldbank_gdp_data.rename(columns={'Time': 'year'}, inplace=True   ) #renaming the column
worldbank_gdp_data['year'] = worldbank_gdp_data['year'].astype(int)  #recasting as int
worldbank_gdp_data.set_index('year', inplace=True)                   #setting year as index

# 1. Train–test split (e.g., 80% train, 20% test)
train_test_split = 0.8
train_size = int(len(worldbank_gdp_data) * train_test_split)
train, test = worldbank_gdp_data[:train_size], worldbank_gdp_data[train_size:]

forecast_horizon = 10  # years ahead to predict
forecast_years = list(range(worldbank_gdp_data.index.max() + 1,
                            worldbank_gdp_data.index.max() + forecast_horizon + 1))
countries = ['ITA','JPN','CAN','FRA','DEU','GBR','USA']

forecast_gdp = pd.DataFrame(index=pd.Index(forecast_years, dtype=int), columns=countries)

for country in countries:
    print(f"\nProcessing {country}...")
    
    # Extract series
    train = worldbank_gdp_data[:train_size][country]
    test = worldbank_gdp_data[train_size:][country]
    
    # Systematic grid search for ARIMA(p,d,q)
    # d=1 sets difference y(t)-y(t-1)
    model = pm.auto_arima(
        train,
        start_p=0, max_p=5,     # search range for AR terms
        start_q=0, max_q=5,     # search range for MA terms
        d=2,                 # let model decide via ADF test
        seasonal=False,
        stepwise=False,         # disable heuristic stepwise search
        suppress_warnings=True,
        error_action='ignore',
        information_criterion='aic',  # use AIC for model selection
        n_jobs=-1               # parallel processing for speed
    )
    
    print(f"\n\nSelected ARIMA order for {country}: {model.order}\n")
    
    # Forecast on test to evaluate
    prediction_on_test = model.predict(n_periods=len(test))
    mse = mean_squared_error(test, prediction_on_test)
    print(f"Test MSE for {country}: {mse:.2e}")
    
    # Refit on full series
    model.fit(worldbank_gdp_data[country])
    
    # Forecast 10 years ahead
    forecast_values = model.predict(n_periods=forecast_horizon)
    forecast_values.index = forecast_years
    
    # Assign to column
    forecast_gdp[country] = forecast_values


plot_gdp_forecast(worldbank_gdp_data, forecast_gdp, countries)

print("\n\n")





