from statsmodels.tsa.statespace.sarimax import SARIMAX

model = SARIMAX(y, exog=x, order=(1,0,0))
results = model.fit(disp=False)
forecast = results.forecast(steps=1, exog=[[x.iloc[-1]]])
