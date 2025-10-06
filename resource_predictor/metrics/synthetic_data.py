import pandas as pd
import numpy as np

def generate_synthetic_data(file='synthetic_metrics.csv', days=7):
    rng = pd.date_range('2025-09-01', periods=24*days, freq='H')
    df = pd.DataFrame({
        'timestamp': rng,
        'cpu_usage': np.clip(np.random.normal(50, 10, len(rng)), 10, 99),
        'memory_usage': np.clip(np.random.normal(60, 12, len(rng)), 15, 99),
        'storage_usage': 100 + np.cumsum(np.random.normal(0, 1, len(rng)))
    })
    df.to_csv(file, index=False)

if __name__ == "__main__":
    generate_synthetic_data()
