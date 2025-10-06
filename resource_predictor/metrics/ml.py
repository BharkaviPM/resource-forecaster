import pandas as pd
from prophet import Prophet

def forecast_prophet(df, col, periods=24):
    # Prepare dataframe for Prophet
    prophet_df = df.rename(columns={'timestamp': 'ds', col: 'y'})[['ds', 'y']].copy()

    # Remove timezone info from datetime to avoid Prophet error
    if prophet_df['ds'].dt.tz is not None:
        prophet_df['ds'] = prophet_df['ds'].dt.tz_localize(None)

    model = Prophet()
    model.fit(prophet_df)
    future = model.make_future_dataframe(periods=periods, freq='H')
    forecast = model.predict(future)
    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
