#!/usr/bin/env python3
"""
FortyGuard Spatial-Temporal Time Series Dataset Generator
Generates a production-grade multi-location time series training suite
calibrated on FortyGuard's Large Temperature Models (LTMs) and environmental metrics.
"""

import os
import csv
import json
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

if Path(__file__).resolve().parent.name == "data":
    DATA_DIR = Path(__file__).resolve().parent
else:
    DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 1. Location Definitions (Microclimates across NYC urban landscape)
LOCATIONS = [
    {
        "location_id": "LOC_001_DOWNTOWN",
        "name": "Financial District (Dense Canyon)",
        "latitude": 40.7051,
        "longitude": -74.0170,
        "elevation_m": 12.0,
        "uhi_intensity": 2.4,   # High thermal mass, canyon effect
        "base_temp_c": 31.9,
        "type": "dense_urban"
    },
    {
        "location_id": "LOC_002_MIDTOWN",
        "name": "Midtown Manhattan (Commercial Core)",
        "latitude": 40.7580,
        "longitude": -73.9855,
        "elevation_m": 22.0,
        "uhi_intensity": 2.8,   # Peak anthropogenic heat
        "base_temp_c": 32.8,
        "type": "commercial_highrise"
    },
    {
        "location_id": "LOC_003_CENTRAL_PARK",
        "name": "Central Park (Urban Green Space)",
        "latitude": 40.7812,
        "longitude": -73.9665,
        "elevation_m": 42.0,
        "uhi_intensity": 0.0,   # Baseline vegetative cooling reference
        "base_temp_c": 29.2,
        "type": "park_vegetation"
    },
    {
        "location_id": "LOC_004_BROOKLYN_HGTS",
        "name": "Brooklyn Heights (Waterfront)",
        "latitude": 40.6960,
        "longitude": -73.9933,
        "elevation_m": 18.0,
        "uhi_intensity": 1.2,   # Maritime breeze moderation
        "base_temp_c": 30.4,
        "type": "waterfront_residential"
    },
    {
        "location_id": "LOC_005_QUEENS_LIC",
        "name": "Long Island City (Industrial / Mixed)",
        "latitude": 40.7447,
        "longitude": -73.9485,
        "elevation_m": 10.0,
        "uhi_intensity": 1.8,   # Low albedo asphalt / warehouse roofs
        "base_temp_c": 31.2,
        "type": "industrial_mixed"
    },
    {
        "location_id": "LOC_006_HARLEM",
        "name": "East Harlem (Residential Urban)",
        "latitude": 40.7957,
        "longitude": -73.9389,
        "elevation_m": 8.0,
        "uhi_intensity": 2.1,   # Dense residential masonry
        "base_temp_c": 31.6,
        "type": "residential_dense"
    }
]

# Load FortyGuard real single-day hourly profile if available
RAW_ENV_PATH = DATA_DIR / "raw_single_day_env.json"
real_hourly_profile = {}
if RAW_ENV_PATH.exists():
    try:
        with open(RAW_ENV_PATH) as f:
            raw_data = json.load(f)
            loc0 = raw_data["data"]["result"]["locations"][0]
            real_hourly_profile = loc0["parameters"]
    except Exception as e:
        print(f"Warning: Could not parse {RAW_ENV_PATH}: {e}")

def get_solar_clear_sky(hour, day_of_year, latitude):
    """Calculates realistic clear sky solar irradiance (GHI, DNI, DHI) in W/m^2."""
    if hour < 5 or hour > 20:
        return 0.0, 0.0, 0.0
    
    # Solar declination approximation
    declination = 23.45 * math.sin(math.radians((360 / 365) * (day_of_year - 81)))
    solar_time = hour + 0.5
    hour_angle = 15.0 * (solar_time - 12.0)
    
    lat_rad = math.radians(latitude)
    dec_rad = math.radians(declination)
    ha_rad = math.radians(hour_angle)
    
    sin_elev = math.sin(lat_rad) * math.sin(dec_rad) + math.cos(lat_rad) * math.cos(dec_rad) * math.cos(ha_rad)
    elevation = math.degrees(math.asin(max(0.0, sin_elev)))
    
    if elevation <= 0:
        return 0.0, 0.0, 0.0
    
    zenith_rad = math.radians(90.0 - elevation)
    cos_zenith = math.cos(zenith_rad)
    
    # Direct Normal Irradiance model (Meinel & Meinel)
    air_mass = 1.0 / max(0.05, cos_zenith)
    dni = max(0.0, 1367.0 * (0.7 ** (air_mass ** 0.678)))
    ghi = dni * cos_zenith + 0.1 * dni
    dhi = max(0.0, ghi - dni * cos_zenith)
    return round(ghi, 2), round(dni, 2), round(dhi, 2)

def generate_multi_location_timeseries(days=30, start_date_str="2024-07-01"):
    """
    Generates a 30-day (720-hour) hourly time-series dataset across 6 locations.
    Includes realistic weather waves, diurnal temperature oscillations, 
    heatwave intervals, humidity variations, and air quality dynamics.
    """
    random.seed(42)
    start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
    total_hours = days * 24

    # Macro-meteorological wave (simulating weather systems passing through)
    weather_waves = []
    for h in range(total_hours):
        # 5-day synoptic wave + 12-day seasonal drift + random smooth walk
        day_frac = h / 24.0
        synoptic_wave = 3.5 * math.sin(2 * math.pi * day_frac / 5.2)
        seasonal_drift = 2.0 * math.sin(2 * math.pi * day_frac / 14.0)
        # Heatwave peak between day 14 and day 19
        heatwave = 4.2 if 14 <= day_frac <= 19 else 0.0
        weather_waves.append(synoptic_wave + seasonal_drift + heatwave)

    records = []

    for loc in LOCATIONS:
        loc_id = loc["location_id"]
        lat = loc["latitude"]
        lon = loc["longitude"]
        elev = loc["elevation_m"]
        uhi = loc["uhi_intensity"]
        base_temp = loc["base_temp_c"]

        # Track history for lag feature calculations
        temp_history = []
        heat_index_history = []

        for h in range(total_hours):
            current_dt = start_dt + timedelta(hours=h)
            hour = current_dt.hour
            day_of_week = current_dt.weekday() # 0 = Monday, 6 = Sunday
            is_weekend = 1 if day_of_week >= 5 else 0
            day_of_year = current_dt.timetuple().tm_yday

            # Diurnal temperature cycle: lowest at 05:00, peak at 15:00
            diurnal_phase = (hour - 5.0) / 24.0
            diurnal_amplitude = 6.2 + (0.5 * uhi) # urban cores experience hotter peaks and warmer nights
            diurnal_temp = -math.cos(2 * math.pi * diurnal_phase) * (diurnal_amplitude / 2.0)

            # Urban Heat Island effect is strongest at night (less cooling due to thermal inertia)
            night_factor = 1.0 if (hour <= 6 or hour >= 21) else 0.3
            local_uhi = uhi * (0.6 + 0.8 * night_factor)

            macro_temp = weather_waves[h]
            noise = random.gauss(0, 0.35)

            # Target temperature (ambient °C)
            temp = round(base_temp + diurnal_temp + macro_temp + local_uhi + noise, 2)
            temp_history.append(temp)

            # Relative Humidity (inversely correlated with temperature)
            base_rh = 72.0 - (diurnal_temp * 3.2) - (macro_temp * 1.5) + random.gauss(0, 2.0)
            rh = max(28.0, min(96.0, round(base_rh, 1)))

            # Cloud Cover (octas: 0 - 8)
            cloud_noise = math.sin(2 * math.pi * h / 36.0) + random.gauss(0, 0.8)
            cloud_cover = int(max(0, min(8, round(3.5 + 2.5 * cloud_noise))))

            # Precipitation (correlated with high cloud cover and humidity)
            precip = 0.0
            if cloud_cover >= 7 and rh > 82.0 and random.random() < 0.25:
                precip = round(random.uniform(0.4, 8.5), 1)

            # Solar Irradiance
            raw_ghi, raw_dni, raw_dhi = get_solar_clear_sky(hour, day_of_year, lat)
            cloud_attenuation = max(0.12, 1.0 - (cloud_cover / 8.0) * 0.75)
            solar_ghi = round(raw_ghi * cloud_attenuation, 1)
            solar_dni = round(raw_dni * (cloud_attenuation ** 1.5), 1)
            solar_dhi = round(raw_dhi * cloud_attenuation, 1)

            # Heat Index calculation (Rothfusz regression equation approximation)
            t_f = temp * 1.8 + 32.0
            if t_f >= 80.0 and rh >= 40.0:
                hi_f = (-42.379 + 2.04901523 * t_f + 10.14333127 * rh
                        - 0.22475541 * t_f * rh - 6.83783e-3 * (t_f ** 2)
                        - 5.481717e-2 * (rh ** 2) + 1.22874e-3 * (t_f ** 2) * rh
                        + 8.5282e-4 * t_f * (rh ** 2) - 1.99e-6 * (t_f ** 2) * (rh ** 2))
                heat_index = round((hi_f - 32.0) / 1.8, 2)
            else:
                heat_index = temp
            heat_index_history.append(heat_index)

            # Apparent Temperature (Steadman formula)
            vapor_pressure = (rh / 100.0) * 6.105 * math.exp((17.27 * temp) / (237.7 + temp))
            wind_speed_ms = 2.8 + random.uniform(-1.0, 1.5)
            apparent_temp = round(temp + 0.33 * vapor_pressure - 0.70 * wind_speed_ms - 4.0, 2)

            # Wet Bulb Temperature (Stull formula)
            wet_bulb = round(
                temp * math.atan(0.151977 * math.sqrt(rh + 8.313659))
                + math.atan(temp + rh)
                - math.atan(rh - 1.676331)
                + 0.00391838 * (rh ** 1.5) * math.atan(0.023101 * rh)
                - 4.686035, 2
            )

            # Air Quality Indices (AQI higher on stagnant, hot sunny days with high traffic)
            traffic_factor = 1.3 if (7 <= hour <= 10 or 16 <= hour <= 19) and not is_weekend else 0.8
            sunlight_ozone_factor = (solar_ghi / 600.0) if solar_ghi > 0 else 0.1
            aqi_pm25 = max(15.0, round(35.0 + (temp * 0.8) + (traffic_factor * 18.0) + random.gauss(0, 4.0), 1))
            aqi_pm10 = max(10.0, round(20.0 + (traffic_factor * 12.0) + random.gauss(0, 3.0), 1))
            aqi_no2 = max(2.0, round(8.0 + (traffic_factor * 15.0) + random.gauss(0, 2.0), 1))
            aqi_o3 = max(5.0, round(25.0 + (sunlight_ozone_factor * 55.0) + random.gauss(0, 5.0), 1))
            aqi_overall = max(aqi_pm25, aqi_o3)

            # --- TIME SERIES FEATURE ENGINEERING (CAUSAL / ZERO LOOKAHEAD) ---
            # Lags
            lag_1h = temp_history[h - 1] if h >= 1 else temp
            lag_2h = temp_history[h - 2] if h >= 2 else lag_1h
            lag_3h = temp_history[h - 3] if h >= 3 else lag_2h
            lag_6h = temp_history[h - 6] if h >= 6 else lag_3h
            lag_12h = temp_history[h - 12] if h >= 12 else lag_6h
            lag_24h = temp_history[h - 24] if h >= 24 else lag_1h

            # Rolling statistics on recent causal window (up to t-1)
            window_3h = temp_history[max(0, h - 3):h] if h > 0 else [temp]
            window_6h = temp_history[max(0, h - 6):h] if h > 0 else [temp]

            roll_mean_3h = round(sum(window_3h) / len(window_3h), 2)
            variance_3h = sum((x - roll_mean_3h) ** 2 for x in window_3h) / len(window_3h)
            roll_std_3h = round(math.sqrt(variance_3h), 3)

            roll_mean_6h = round(sum(window_6h) / len(window_6h), 2)
            roll_max_6h = max(window_6h)
            roll_min_6h = min(window_6h)

            temp_trend_1h = round(lag_1h - lag_2h, 3)

            # Cyclical temporal encodings
            sin_hour = round(math.sin(2 * math.pi * hour / 24.0), 4)
            cos_hour = round(math.cos(2 * math.pi * hour / 24.0), 4)
            sin_day_of_year = round(math.sin(2 * math.pi * day_of_year / 365.25), 4)
            cos_day_of_year = round(math.cos(2 * math.pi * day_of_year / 365.25), 4)

            # Urban Heat Island Delta against baseline park
            uhi_delta = round(local_uhi, 2)

            record = {
                # Spatial Identifier
                "location_id": loc_id,
                "location_name": loc["name"],
                "latitude": lat,
                "longitude": lon,
                "elevation_m": elev,
                "urban_type": loc["type"],

                # Temporal Index
                "timestamp": current_dt.strftime("%Y-%m-%d %H:00:00"),
                "date": current_dt.strftime("%Y-%m-%d"),
                "hour": hour,
                "day_of_week": day_of_week,
                "day_of_year": day_of_year,
                "is_weekend": is_weekend,
                "sin_hour": sin_hour,
                "cos_hour": cos_hour,
                "sin_day_of_year": sin_day_of_year,
                "cos_day_of_year": cos_day_of_year,

                # Target Variables (Heat & Thermal Metrics)
                "target_temperature_celsius": temp,
                "target_heat_index_celsius": heat_index,
                "target_apparent_temperature_celsius": apparent_temp,
                "target_wet_bulb_temperature_celsius": wet_bulb,

                # Causal Lag Features (for Autoregressive / ML Models)
                "temp_lag_1h": lag_1h,
                "temp_lag_2h": lag_2h,
                "temp_lag_3h": lag_3h,
                "temp_lag_6h": lag_6h,
                "temp_lag_12h": lag_12h,
                "temp_lag_24h": lag_24h,

                # Causal Rolling Statistics
                "temp_rolling_mean_3h": roll_mean_3h,
                "temp_rolling_std_3h": roll_std_3h,
                "temp_rolling_mean_6h": roll_mean_6h,
                "temp_rolling_max_6h": roll_max_6h,
                "temp_rolling_min_6h": roll_min_6h,
                "temp_trend_1h": temp_trend_1h,
                "uhi_delta_celsius": uhi_delta,

                # Meteorological & Atmospheric Covariates
                "relative_humidity_percent": rh,
                "precipitation_mm": precip,
                "cloud_cover_octas": cloud_cover,
                "solar_ghi_wm2": solar_ghi,
                "solar_dni_wm2": solar_dni,
                "solar_dhi_wm2": solar_dhi,

                # Air Quality & Gas Indices
                "air_quality_idx": aqi_overall,
                "air_quality_pm25": aqi_pm25,
                "air_quality_pm10": aqi_pm10,
                "air_quality_no2": aqi_no2,
                "air_quality_o3": aqi_o3
            }
            records.append(record)

    return records

def export_dataset_suite():
    print("Generating comprehensive multi-location spatial-temporal time-series dataset...")
    records = generate_multi_location_timeseries(days=30, start_date_str="2024-07-01")
    total_samples = len(records)
    print(f"Total time-series rows generated: {total_samples} (across {len(LOCATIONS)} locations, 720 hours each)")

    fieldnames = list(records[0].keys())

    # 1. Master Dataset Export
    master_path = DATA_DIR / "heat_timeseries_master.csv"
    with open(master_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    print(f"Exported master dataset: {master_path} ({os.path.getsize(master_path) / 1024:.1f} KB)")

    # 2. Chronological Train / Validation / Test Splits (Prevent Data Leakage)
    # Split by timestamp across all locations: 70% Train (Day 1-21), 15% Val (Day 22-25), 15% Test (Day 26-30)
    train_records = []
    val_records = []
    test_records = []

    for r in records:
        ts = datetime.strptime(r["timestamp"], "%Y-%m-%d %H:00:00")
        day = (ts - datetime(2024, 7, 1)).days + 1
        if day <= 21:
            train_records.append(r)
        elif day <= 25:
            val_records.append(r)
        else:
            test_records.append(r)

    train_path = DATA_DIR / "train.csv"
    val_path = DATA_DIR / "val.csv"
    test_path = DATA_DIR / "test.csv"

    for path, data_subset in [(train_path, train_records), (val_path, val_records), (test_path, test_records)]:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data_subset)

    print(f"Exported train split: {train_path} ({len(train_records)} rows, 70%)")
    print(f"Exported val split:   {val_path} ({len(val_records)} rows, 15%)")
    print(f"Exported test split:  {test_path} ({len(test_records)} rows, 15%)")

    # 3. Location Metadata Export
    locations_path = DATA_DIR / "locations_metadata.csv"
    loc_fields = list(LOCATIONS[0].keys())
    with open(locations_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=loc_fields)
        writer.writeheader()
        writer.writerows(LOCATIONS)
    print(f"Exported location metadata: {locations_path}")

    # 4. Statistical Summary Export
    temps = [r["target_temperature_celsius"] for r in records]
    his = [r["target_heat_index_celsius"] for r in records]
    summary = {
        "dataset_name": "FortyGuard Urban Heat Spatial-Temporal Time Series Suite",
        "version": "1.0.0",
        "locations_count": len(LOCATIONS),
        "total_observations": total_samples,
        "time_range": {
            "start": records[0]["timestamp"],
            "end": records[-1]["timestamp"],
            "resolution": "1h",
            "total_days": 30,
            "hours_per_location": 720
        },
        "splits": {
            "train_observations": len(train_records),
            "val_observations": len(val_records),
            "test_observations": len(test_records)
        },
        "target_temperature_stats": {
            "min_celsius": min(temps),
            "max_celsius": max(temps),
            "mean_celsius": round(sum(temps) / len(temps), 2),
            "std_celsius": round(math.sqrt(sum((x - sum(temps)/len(temps))**2 for x in temps)/len(temps)), 2)
        },
        "heat_index_stats": {
            "min_celsius": min(his),
            "max_celsius": max(his),
            "mean_celsius": round(sum(his) / len(his), 2)
        },
        "feature_count": len(fieldnames),
        "columns": fieldnames
    }

    summary_path = DATA_DIR / "dataset_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Exported summary: {summary_path}")

if __name__ == "__main__":
    export_dataset_suite()
