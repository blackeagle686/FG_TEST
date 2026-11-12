# 1.
import requests

response = requests.post(
    'https://api.fortyguard.com/v1/heatmap',
    headers={'api-key': 'your_api_key'},
    json={
        'polygon_aoi': {
            'type': 'Polygon',
            'coordinates': [[
                [-74.0170, 40.7051],
                [-74.0031, 40.7051],
                [-74.0031, 40.7180],
                [-74.0170, 40.7180],
                [-74.0170, 40.7051]
            ]]
        },
        'date_time': {
            'start_date': '2024-07-15',
            'start_time': '14:00',
            'filter_type': 1
        },
        'granularity': 100
    }
)
import requests

response = requests.post(
    'https://api.fortyguard.com/v1/heatmap',
    headers={'api-key': 'your_api_key'},
    json={
        'polygon_aoi': {
            'type': 'Polygon',
            'coordinates': [[
                [-74.0170, 40.7051],
                [-74.0031, 40.7051],
                [-74.0031, 40.7180],
                [-74.0170, 40.7180],
                [-74.0170, 40.7051]
            ]]
        },
        'date_time': {
            'start_date': '2024-07-15',
            'start_time': '09:00',
            'end_time': '17:00',
            'filter_type': 2
        },
        'granularity': 80
    }
)
import requests

response = requests.post(
    'https://api.fortyguard.com/v1/heatmap',
    headers={'api-key': 'your_api_key'},
    json={
        'polygon_aoi': {
            'type': 'Polygon',
            'coordinates': [[
                [-74.0170, 40.7051],
                [-74.0031, 40.7051],
                [-74.0031, 40.7180],
                [-74.0170, 40.7180],
                [-74.0170, 40.7051]
            ]]
        },
        'date_time': {
            'start_date': '2024-07-15',
            'filter_type': 3
        },
        'granularity': 60
    }
)
import requests

response = requests.post(
    'https://api.fortyguard.com/v1/heatmap',
    headers={'api-key': 'your_api_key'},
    json={
        'polygon_aoi': {
            'type': 'Polygon',
            'coordinates': [[
                [-74.0170, 40.7051],
                [-74.0031, 40.7051],
                [-74.0031, 40.7180],
                [-74.0170, 40.7180],
                [-74.0170, 40.7051]
            ]]
        },
        'date_time': {
            'start_date': '2024-07-01',
            'end_date': '2024-07-31',
            'filter_type': 4
        },
        'granularity': 100
    }
)

import requests

# Analytic heatmap: hours above a temperature threshold over the window.
# analytic_type also accepts 'time_of_measure' and 'persistence'.
response = requests.post(
    'https://api.fortyguard.com/v1/heatmap',
    headers={'api-key': 'your_api_key'},
    json={
        'polygon_aoi': {
            'type': 'Polygon',
            'coordinates': [[
                [-74.0170, 40.7051],
                [-74.0031, 40.7051],
                [-74.0031, 40.7180],
                [-74.0170, 40.7180],
                [-74.0170, 40.7051]
            ]]
        },
        'date_time': {
            'start_date': '2024-07-15',
            'start_time': '06:00',
            'end_time': '18:00',
            'filter_type': 2
        },
        'granularity': 100,
        'analytic_type': 'exceedance',
        'threshold': 30,
        'direction': 'above'
    }
)

import requests

# Analytic heatmap: the hour of day (0-23, UTC) at which each cell peaks.
# threshold / direction are not used for time_of_measure.
response = requests.post(
    'https://api.fortyguard.com/v1/heatmap',
    headers={'api-key': 'your_api_key'},
    json={
        'polygon_aoi': {
            'type': 'Polygon',
            'coordinates': [[
                [-74.0170, 40.7051],
                [-74.0031, 40.7051],
                [-74.0031, 40.7180],
                [-74.0170, 40.7180],
                [-74.0170, 40.7051]
            ]]
        },
        'date_time': {
            'start_date': '2024-07-15',
            'filter_type': 3
        },
        'granularity': 100,
        'analytic_type': 'time_of_measure'
    }
)

import requests

# Analytic heatmap: the longest continuous run of hours past the threshold.
response = requests.post(
    'https://api.fortyguard.com/v1/heatmap',
    headers={'api-key': 'your_api_key'},
    json={
        'polygon_aoi': {
            'type': 'Polygon',
            'coordinates': [[
                [-74.0170, 40.7051],
                [-74.0031, 40.7051],
                [-74.0031, 40.7180],
                [-74.0170, 40.7180],
                [-74.0170, 40.7051]
            ]]
        },
        'date_time': {
            'start_date': '2024-07-15',
            'start_time': '06:00',
            'end_time': '18:00',
            'filter_type': 2
        },
        'granularity': 20,
        'analytic_type': 'persistence',
        'threshold': 30,
        'direction': 'above'
    }
)

# 2. 
import requests

response = requests.post(
    'https://api.fortyguard.com/v1/satellite',
    headers={'api-key': 'your_api_key'},
    json={
        'sat': {
            'latitude': 41.84632807720175,
            'longitude': -87.74329628220852
        },
        'date_time': {
            'start_date': '2024-07-15',
            'start_time': '14:00',
            'filter_type': 1
        },
        'granularity': 80
    }
)

# 3
import requests

response = requests.post(
    'https://api.fortyguard.com/v1/streetview',
    headers={'api-key': 'your_api_key'},
    json={
        'latitude': 40.7128,
        'longitude': -74.0060,
        'vertical_angle': 10.0,
        'horizontal_angle': 90.0,
        'back_view': False
    }
)

# 4
import time
from pathlib import Path

import requests

activity_id = "f3e1c68b-1cc3-46bc-8589-1faaf30ef30a"
headers = {"api-key": "your_api_key"}
status_url = f"https://api.fortyguard.com/v1/status/{activity_id}"

for _ in range(120):
    status_resp = requests.get(status_url, headers=headers, timeout=30)
    status_resp.raise_for_status()
    data = status_resp.json()["data"]
    status = data.get("status")

    if status == "Completed":
        download_link = (data.get("result") or {}).get("download_link")
        if not download_link:
            raise RuntimeError(f"Activity {activity_id} completed without a download_link")

        report_resp = requests.get(download_link, timeout=60)
        report_resp.raise_for_status()
        Path("report.pdf").write_bytes(report_resp.content)
        print("Saved to report.pdf")
        break

    if status == "Failed":
        raise RuntimeError(f"Activity {activity_id} failed")

    time.sleep(5)
else:
    raise TimeoutError(f"Activity {activity_id} did not complete in time")


# 5

import requests

response = requests.post(
    'https://api.fortyguard.com/v1/env_params',
    headers={'api-key': 'your_api_key'},
    json={
        'latitude': 40.7128,
        'longitude': -74.0060,
        'temperature': 32.5,
        'date_time': {
            'start_date': '2024-07-15',
            'start_time': '14:00',
            'filter_type': 1
        }
    }
)

# 6
import requests

response = requests.post(
    "https://api.fortyguard.com/v1/routing",
    headers={"api-key": "your_api_key"},
    json={
        "origin": {
            "lat": 40.7812,
            "lon": -73.9665
        },
        "destination": {
            "lat": 40.7580,
            "lon": -73.9855
        },
        "departure_time": "2026-10-19T12:00:00Z"
    }
)

print(response.json())
# 7
import requests

response = requests.post(
    "https://api.fortyguard.com/v1/monitors",
    headers={"api-key": "your_api_key"},
    json={
        "heatmap_id": "heatmap_abc123",
        "name": "Downtown heat watch",
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[[-74.01, 40.70], [-73.93, 40.70], [-73.93, 40.85], [-74.01, 40.70]]]
        },
        "rules": [
            {
                "temporal_aggregation": "average",
                "spatial_aggregation": "minimum",
                "operator": "above",
                "threshold": 40,
                "unit": "celsius"
            }
        ],
        "notifications": {"email": ["ops@example.com"]},
        "enabled": True,
        "generate_report": True
    }
)

print(response.json())

# 8
import requests

response = requests.get(
    "https://api.fortyguard.com/v1/monitors",
    headers={"api-key": "your_api_key"},
    params={"heatmap_id": "heatmap_abc123", "limit": 25}
)

print(response.json())
# 9
import requests

response = requests.get(
    "https://api.fortyguard.com/v1/monitors/monitor_abc123",
    headers={"api-key": "your_api_key"}
)

print(response.json())

# 10 
import requests

response = requests.patch(
    "https://api.fortyguard.com/v1/monitors/monitor_abc123",
    headers={"api-key": "your_api_key"},
    json={"enabled": False, "name": "Downtown heat watch (paused)"}
)

print(response.json())

#11
import requests

response = requests.delete(
    "https://api.fortyguard.com/v1/monitors/monitor_abc123",
    headers={"api-key": "your_api_key"}
)

print(response.json())

# 12
import requests

response = requests.get(
    "https://api.fortyguard.com/v1/monitors/monitor_abc123/alerts",
    headers={"api-key": "your_api_key"},
    params={"limit": 25}
)

print(response.json())
#13
import requests

# Read the report
report = requests.get(
    "https://api.fortyguard.com/v1/monitors/monitor_abc123/alerts/alert_123/report",
    headers={"api-key": "your_api_key"}
)
print(report.json())

# Download it as a PDF file
pdf = requests.get(
    "https://api.fortyguard.com/v1/monitors/monitor_abc123/alerts/alert_123/report/download",
    headers={"api-key": "your_api_key"},
    params={"file_type": "pdf"}
)
open("alert-report.pdf", "wb").write(pdf.content)
#14

import requests

# Replace {activity_id} with the actual activity ID from your submission
activity_id = "heatmap_abc123"

response = requests.get(
    f'https://api.fortyguard.com/v1/status/{activity_id}',
    headers={'api-key': 'your_api_key'}
)