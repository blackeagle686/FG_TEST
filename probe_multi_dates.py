import requests
import json
import time

API_KEY = "f2012cbf956d74fd478c29b84ee54b4a"
BASE_URL = "https://api.fortyguard.com"
headers = {'api-key': API_KEY, 'Content-Type': 'application/json'}

dates = ["2024-07-14", "2024-07-15", "2024-07-16", "2024-07-17", "2024-07-18", "2024-07-19", "2024-07-20"]
locations = [
    {"id": "LOC_001_DOWNTOWN", "name": "Financial District", "lat": 40.7051, "lon": -74.0170, "base_temp": 31.5},
    {"id": "LOC_002_MIDTOWN", "name": "Midtown Manhattan", "lat": 40.7580, "lon": -73.9855, "base_temp": 32.8},
    {"id": "LOC_003_CENTRAL_PARK", "name": "Central Park", "lat": 40.7812, "lon": -73.9665, "base_temp": 29.2},
    {"id": "LOC_004_BROOKLYN", "name": "Brooklyn Heights", "lat": 40.6960, "lon": -73.9933, "base_temp": 30.4},
    {"id": "LOC_005_QUEENS", "name": "Long Island City", "lat": 40.7447, "lon": -73.9485, "base_temp": 31.0}
]

print("Probing multiple dates for LOC_001_DOWNTOWN...")
for d in dates[:3]:
    p = {
        'latitude': locations[0]['lat'],
        'longitude': locations[0]['lon'],
        'temperature': locations[0]['base_temp'],
        'date_time': {'start_date': d, 'filter_type': 3}
    }
    r = requests.post(f"{BASE_URL}/v1/env_params", headers=headers, json=p, timeout=20)
    print(f"Date {d}: Submit status {r.status_code}")
    if r.status_code == 200:
        aid = r.json().get('data', {}).get('activity_id')
        print(f"  Activity ID: {aid}")
        time.sleep(2)
        r_poll = requests.get(f"{BASE_URL}/v1/status/{aid}", headers=headers, timeout=20)
        st = r_poll.json().get('data', {}).get('status')
        print(f"  Poll status: {st}")
