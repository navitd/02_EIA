Idea: create features E_{t-1}, E_{t-2}, ..., GDP_{t}, GDP_{t-1}, ... then predict E_t. Use Ridge to avoid overfitting.

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV

def make_lagged_df(df, target_col='E', exog_col='GDP', n_lag_target=3, n_lag_exog=3, include_current_exog=True):
    """Return DataFrame with lagged features and y (aligned so row t has y=E_t and features from past)."""
    df = df.copy().reset_index(drop=True)
    cols = {}
    # target lags: E_{t-1} ... E_{t-n}
    for lag in range(1, n_lag_target + 1):
        cols[f'{target_col}_lag{lag}'] = df[target_col].shift(lag)
    # exog lags (and optionally current)
    if include_current_exog:
        cols[f'{exog_col}_lag0'] = df[exog_col]  # current GDP at time t
    for lag in range(1, n_lag_exog + 1):
        cols[f'{exog_col}_lag{lag}'] = df[exog_col].shift(lag)
    lagged = pd.DataFrame(cols)
    lagged['y'] = df[target_col]  # y_t
    return lagged.dropna().reset_index(drop=True)

# Example usage:
# df should have columns: 'Time', 'E', 'GDP' sorted by Time ascending
# choose lags:
n_lag_E = 3
n_lag_GDP = 2
include_current_gdp = True

lagged = make_lagged_df(df, target_col='E', exog_col='GDP',
                        n_lag_target=n_lag_E, n_lag_exog=n_lag_GDP,
                        include_current_exog=include_current_gdp)

X = lagged.drop(columns='y').values
y = lagged['y'].values

# time-series CV to select alpha
tscv = TimeSeriesSplit(n_splits=5)
param_grid = {'ridge__alpha': [0.1, 1, 10, 100]}
pipe = make_pipeline(StandardScaler(), Ridge())
g = GridSearchCV(pipe, param_grid, cv=tscv, scoring='neg_mean_squared_error', n_jobs=-1)
g.fit(X, y)

model = g.best_estimator_

# Predict next step (one-step ahead). You need the most recent lags.
def predict_next(model, df_original, n_lag_E, n_lag_GDP, include_current_gdp=True):
    last = df_original.reset_index(drop=True)
    # build feature vector in same order as make_lagged_df:
    feats = []
    for lag in range(1, n_lag_E+1):
        feats.append(last['E'].iat[-lag])
    if include_current_gdp:
        feats.append(last['GDP'].iat[-1])   # current GDP available
    for lag in range(1, n_lag_GDP+1):
        feats.append(last['GDP'].iat[-lag])
    Xnext = np.array(feats).reshape(1, -1)
    return model.predict(Xnext)[0]

next_E = predict_next(model, df, n_lag_E, n_lag_GDP, include_current_gdp)
print("Predicted next E:", next_E)



Notes / choices

If current GDP at time t is available before predicting E_t, include it (include_current_gdp=True). If not, set False and rely only on past GDP.

For multi-step forecasts, either:

Recursive: predict E_{t+1}, append it, shift lags and predict E_{t+2}, etc.; or

Direct: train separate models for each horizon.

Use StandardScaler + Ridge (or Lasso) to limit blowups.

Choose lags using domain knowledge or automated selection (grid search, AIC on ARX).

Alternatives (short)

ARIMAX / SARIMAX (statsmodels): SARIMAX(endog=E, exog=GDP, order=(p,d,q)) — classical approach with statistical inference and AIC/BIC for order selection.

VAR (vector autoregression) if you treat E and GDP as jointly endogenous and want multivariate dynamics: statsmodels.tsa.api.VAR.

State-space / Kalman filter (if you want time-varying coefficients).

Nonlinear ML: RandomForest / XGBoost on the same lagged features if nonlinearity is important.

Quick guidance for practice

Start simple: try n_lag_E=1..3, n_lag_GDP=0..3, use Ridge(alpha=1/10/100) and time-series CV.

Check residuals and short forecast horizon — with little data prefer low complexity.

If seasonal structure exists, include seasonal lags (e.g., lag 12).