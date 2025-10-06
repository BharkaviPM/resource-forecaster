import pandas as pd
import json
from django.shortcuts import render, redirect
from .models import ResourceMetric
from .forms import UploadFileForm
from .ml import forecast_prophet


# Helper to convert all pd.Timestamp to ISO format strings for JSON
def convert_timestamps(obj):
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_timestamps(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_timestamps(item) for item in obj]
    else:
        return obj


def upload_data(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                df = pd.read_csv(request.FILES['file'])

                # Parse timestamps & drop invalid ones
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                df = df.dropna(subset=['timestamp'])

                # Localize timezone if naive
                if df['timestamp'].dt.tz is None:
                    df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')

                # Convert usage columns, fill missing with 0
                df['cpu_usage'] = pd.to_numeric(df['cpu_usage'], errors='coerce').fillna(0)
                df['memory_usage'] = pd.to_numeric(df['memory_usage'], errors='coerce').fillna(0)
                if 'storage_usage' in df.columns:
                    df['storage_usage'] = pd.to_numeric(df['storage_usage'], errors='coerce').fillna(0)
                else:
                    df['storage_usage'] = 0

                # Bulk save update or create
                existing_timestamps = set(ResourceMetric.objects.values_list('timestamp', flat=True))
                instances_to_create = []
                for _, row in df.iterrows():
                    if row['timestamp'] in existing_timestamps:
                        ResourceMetric.objects.filter(timestamp=row['timestamp']).update(
                            cpu_usage=row['cpu_usage'],
                            memory_usage=row['memory_usage'],
                            storage_usage=row['storage_usage']
                        )
                    else:
                        instances_to_create.append(ResourceMetric(
                            timestamp=row['timestamp'],
                            cpu_usage=row['cpu_usage'],
                            memory_usage=row['memory_usage'],
                            storage_usage=row['storage_usage']
                        ))
                if instances_to_create:
                    ResourceMetric.objects.bulk_create(instances_to_create)

                return redirect('dashboard')

            except Exception as e:
                return render(request, 'metrics/upload.html', {
                    'form': form,
                    'error': f'Failed to process file: {e}'
                })
    else:
        form = UploadFileForm()
    return render(request, 'metrics/upload.html', {'form': form})


def dashboard(request):
    qs = ResourceMetric.objects.order_by('timestamp').values()
    df = pd.DataFrame(qs)

    # Parse and clean timestamps to avoid invalid entries
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df = df.dropna(subset=['timestamp'])
    df.sort_values('timestamp', inplace=True)

    if df.empty:
        return render(request, 'metrics/dashboard.html', {
            'message': 'No data to display. Please upload a CSV file first.'
        })

    try:
        N = int(request.GET.get('n', 48))
        if N < 1:
            N = 48
    except (ValueError, TypeError):
        N = 48

    forecast_cpu = forecast_prophet(df, 'cpu_usage', periods=N)
    forecast_mem = forecast_prophet(df, 'memory_usage', periods=N)
    forecast_storage = forecast_prophet(df, 'storage_usage', periods=N)

    alerts = []
    if forecast_cpu['yhat'].max() > 85:
        alerts.append('Forecast CPU usage exceeds 85%.')
    if forecast_mem['yhat'].max() > 90:
        alerts.append('Forecast Memory usage exceeds 90%.')
    if forecast_storage['yhat'].max() > 95:
        alerts.append('Forecast Storage usage exceeds 95%.')

    safe_data = convert_timestamps(df.to_dict(orient='list'))
    safe_forecast_cpu = convert_timestamps(forecast_cpu.to_dict(orient='list'))
    safe_forecast_mem = convert_timestamps(forecast_mem.to_dict(orient='list'))
    safe_forecast_storage = convert_timestamps(forecast_storage.to_dict(orient='list'))

    historical_table = df.tail(50).to_dict('records')
    forecast_table_cpu = forecast_cpu.to_dict('records')
    forecast_table_mem = forecast_mem.to_dict('records')
    forecast_table_storage = forecast_storage.to_dict('records')

    return render(request, 'metrics/dashboard.html', {
        'data': json.dumps(safe_data),
        'forecast_cpu': json.dumps(safe_forecast_cpu),
        'forecast_mem': json.dumps(safe_forecast_mem),
        'forecast_storage': json.dumps(safe_forecast_storage),
        'alerts': alerts,
        'historical_table': historical_table,
        'forecast_table_cpu': forecast_table_cpu,
        'forecast_table_mem': forecast_table_mem,
        'forecast_table_storage': forecast_table_storage,
        'n_hours': N
    })
