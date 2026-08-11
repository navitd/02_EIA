
# Economic Impact Analysis (EIA)

Economic-impact modeling pipeline built around Leontieff input-output analysis: computes sector multipliers and employment impact from national statistical data, benchmarks results against a reference report, and extrapolates forward with time-series trending. Developed for an applied consulting engagement.

## Methodology

- **Input-output modeling** — Leontieff matrix construction and multiplier calculation
- **Multi-source data integration** — StatCan salary data, OECD salary data, and World Bank indicators, each with dedicated cleaning/upload pipelines
- **Benchmarking** — reproduces sector-level impact of GDP, total output, and employment. Calculation is sector specific and separates direct, indirect and induced impacts.
- **Forecasting** — polynomial extrapolation of economic indicators (e.g. GDP), validated with real-vs-predicted comparison plots

## Structure

- `EIAfunctions/` — core library: data upload/cleaning, Leontieff matrix, multipliers, plotting
- `statcan_salaries/`, `OECD_salaries/` — additional data
- `Benchmarking/`, `Bench_predictions_B` — economic benchmark report reproduction for data ingestion and graphs. includes predictions

## Technologies

Python · pandas · Leontieff input-output modeling · World Bank / OECD / StatCan data sources · Economic Impact Analysis (EIA)
