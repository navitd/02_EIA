================================================================================
BENCH_PREDICTIONS_B FOLDER - EXECUTION ORDER & FILE DESCRIPTIONS
================================================================================

PYTHON FILES & EXECUTION ORDER:

1. B00_forecastEIA_verbal_steps.py
   - Verbal documentation of the forecasting workflow
   - Output: Documentation only

2. B03_ARIMA_gdp.py
   - Forecasts GDP using ARIMA model for G7 countries
   - Output: A04_gdp_ARIMAgdp_currentUSD04.csv

3. B03_ARIMA_gdp_JPN_adj.py
   - Adjusts Japan's GDP forecast with linear extrapolation
   - Output: Adjusted GDP data (supplements B03)

4. B04_multivariate_E_extrap.py
   - Extrapolates Employment (E) based on GDP ratio
   - Output: A05_Esectors_from_Etot05.csv

5. B05_Esectors_from_Etot.py
   - Disaggregates total employment into sector-level employment
   - Output: Sector employment distributions

6. B06_collecting_data_over_years.py
   - Collects OECD data (Tc, fHFCE, fother, output, GDPj_by_xj) for 1995-2020
   - Output: B06_df*.csv, B06_df*_tot.csv files

7. B07_base_sectors.py
   - Calculates base ratios (sector/total) for extrapolation
   - Output: B071_*_base_1years.csv files

8. B09_get_all_extrap_vectors.py
   - Extrapolates all vectors (Tc, fother, E) to 2040
   - Output: B072_*_data_and_extrap.csv files

9. B10_graphs1_and_excel3.py
   - Creates CAGR plots, share analysis, GDP impact visualizations
   - Exports data & plots to Excel with formatting
   - Output: B10_graph1_data_YYYY-YYYY.xlsx (with charts & tables)

10. B12_GDPimpact_code_benchmark_plots.py
    - Calculates direct/indirect/induced GDP impacts by sector
    - Creates backward & forward linkage analysis plots
    - Output: Impact matrices, comparison charts

================================================================================

KEY DATA FLOW:
World Bank GDP → B03 (ARIMA) → B04 (Employment extrap) → B05 (Sector E)
                                ↓
                    B06 (Data collection) → B07 (Base ratios)
                         ↓                     ↓
                    B09 (Extrapolation) → B10 (Graphs/Excel)
                                          ↓
                                    B12 (GDP Impacts)

================================================================================
