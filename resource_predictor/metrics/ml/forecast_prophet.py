import pandas as pd
from prophet import Prophet
from ..models import ResourceMetric

def get_df_from_db(metric='cpu_usage'):
    qs = ResourceMetric.objects.all().order_by('timestamp')
    df = pd.DataFrame.from_records(qs.values('timestamp', metric))
    if df.empty:
        return df
    df = df.rename(columns={'timestamp':'ds', metric:'y'})
    df['ds'] = pd.to_datetime(df['ds'])
    return df

def forecast_prophet(metric='cpu_usage', periods=24, freq='H'):
    df = get_df_from_db(metric)
    if df.empty or len(df) < 10:
        return {'error':'Not enough data'}
    m = Prophet(interval_width=0.95)
    m.fit(df)
    future = m.make_future_dataframe(periods=periods, freq=freq)
    forecast = m.predict(future)
    result = forecast[['ds','yhat','yhat_lower','yhat_upper']].tail(periods)
    result['ds'] = result['ds'].dt.strftime('%Y-%m-%d %H:%M:%S')
    return result.to_dict(orient='records')
