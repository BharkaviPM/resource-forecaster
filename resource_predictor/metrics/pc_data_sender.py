import psutil
import datetime
import time
import requests

API_URL = "http://127.0.0.1:8000/api/metrics/"

def send_metrics():
    while True:
        data = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "storage_usage": psutil.disk_usage('/').percent,
        }
        try:
            response = requests.post(API_URL, json=data)
            print(f"Sent: {data} Status: {response.status_code}")
        except Exception as e:
            print("Error:", e)
        time.sleep(10)

if __name__ == "__main__":
    send_metrics()
