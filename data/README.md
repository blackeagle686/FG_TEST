# FortyGuard Spatial-Temporal Urban Heat Dataset Suite

[![Dataset Version](https://img.shields.io/badge/Dataset%20Version-v1.0.0-blue.svg)](dataset_summary.json)
[![Data Resolution](https://img.shields.io/badge/Temporal%20Resolution-1%20Hour-brightgreen.svg)](dataset_summary.json)
[![Observations](https://img.shields.io/badge/Total%20Rows-4%2C320-orange.svg)](dataset_summary.json)
[![Locations](https://img.shields.io/badge/Locations-6%20Microclimates-purple.svg)](locations_metadata.csv)
[![Benchmark R²](https://img.shields.io/badge/Baseline%20R%C2%B2-0.983-success.svg)](train_baseline.py)

A production-ready spatial-temporal time-series dataset suite designed specifically for training, validating, and benchmarking machine learning and deep learning models for **urban heat, ambient temperature, heat index, and thermal stress forecasting**.

The dataset is derived from and calibrated against FortyGuard's **Large Temperature Models (LTMs)** and multidimensional environmental parameters (`/v1/env_params` and `/v1/heatmap`).

---

##  Dataset Architecture

- **Total Observations**: 4,320 hourly sequential samples across 6 distinct urban microclimates.
- **Time Horizon**: 30 consecutive days (720 hours per location) covering synoptic weather waves, diurnal thermal cycles, and simulated heatwave intervals.
- **Temporal Resolution**: Hourly (`1h`).
- **Feature Dimensionality**: 44 variables (target metrics, causal lags, rolling window statistics, atmospheric variables, air quality indices, and solar irradiance models).
- **Leakage Prevention**: Strictly partitioned using **chronological splitting** (no random shuffle):
  - **Train (`train.csv`)**: First 21 days (3,024 samples, 70%)
  - **Validation (`val.csv`)**: Days 22 to 25 (576 samples, 15%)
  - **Test (`test.csv`)**: Days 26 to 30 (720 samples, 15%)

---

##  Monitored Locations (Microclimates)

The locations represent diverse urban surfaces and microclimate conditions across New York City:

| Location ID | Microclimate Name | Coordinates (Lat, Lon) | Elev (m) | UHI Intensity | Urban Typology |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `LOC_001_DOWNTOWN` | Financial District | `40.7051, -74.0170` | 12.0 | +2.4 °C | Dense urban canyon, high thermal mass |
| `LOC_002_MIDTOWN` | Midtown Manhattan | `40.7580, -73.9855` | 22.0 | +2.8 °C | Commercial high-rise, peak anthropogenic heat |
| `LOC_003_CENTRAL_PARK`| Central Park | `40.7812, -73.9665` | 42.0 | 0.0 °C | Vegetative baseline cooling reference |
| `LOC_004_BROOKLYN_HGTS`| Brooklyn Heights | `40.6960, -73.9933` | 18.0 | +1.2 °C | Waterfront residential, maritime moderation |
| `LOC_005_QUEENS_LIC` | Long Island City | `40.7447, -73.9485` | 10.0 | +1.8 °C | Mixed industrial / low-albedo asphalt |
| `LOC_006_HARLEM` | East Harlem | `40.7957, -73.9389` | 8.0 | +2.1 °C | High-density residential masonry |

---

##  File Inventory

```text
data/
├── README.md                  # Detailed dataset card & usage guide
├── train.csv                  # 3,024 rows - Chronological training split (Days 1–21)
├── val.csv                    # 576 rows   - Validation split for tuning (Days 22–25)
├── test.csv                   # 720 rows   - Out-of-sample holdout test split (Days 26–30)
├── heat_timeseries_master.csv # 4,320 rows - Full unified dataset across all locations
├── locations_metadata.csv     # Metadata table for all monitoring stations
├── dataset_summary.json       # JSON metadata and statistical summary
├── build_dataset.py           # Reproducible data generation & feature engineering pipeline
├── train_baseline.py          # Standalone training script for baseline autoregressive models
└── baseline_predictions.csv   # Model forecast outputs on the test set
```

---

##  Feature Dictionary (44 Columns)

### 1. Spatial & Temporal Identifiers
- `location_id` *(str)*: Unique station identifier (`LOC_001_DOWNTOWN`, etc.).
- `location_name` *(str)*: Descriptive location name.
- `latitude`, `longitude` *(float)*: WGS84 geographic coordinates.
- `elevation_m` *(float)*: Elevation above sea level in meters.
- `urban_type` *(str)*: Urban morphology classification.
- `timestamp` *(str)*: Formatted datetime `YYYY-MM-DD HH:00:00`.
- `date` *(str)*: Date `YYYY-MM-DD`.
- `hour` *(int)*: Clock hour (0–23).
- `day_of_week` *(int)*: Day of the week (0 = Monday, 6 = Sunday).
- `day_of_year` *(int)*: Julian day of the year (1–365).
- `is_weekend` *(int)*: Binary indicator (1 if Saturday or Sunday, else 0).
- `sin_hour`, `cos_hour` *(float)*: Cyclical transformation of the 24-hour cycle.
- `sin_day_of_year`, `cos_day_of_year` *(float)*: Cyclical transformation of annual seasonality.

### 2. Target Variables (To Forecast)
- `target_temperature_celsius` *(float)*: Ambient dry-bulb air temperature (°C).
- `target_heat_index_celsius` *(float)*: "Feels like" temperature combining heat and humidity.
- `target_apparent_temperature_celsius` *(float)*: Steadman apparent temperature (°C).
- `target_wet_bulb_temperature_celsius` *(float)*: Stull wet-bulb thermal stress temperature (°C).

### 3. Causal Lag & Autoregressive Features
All lag and rolling features are strictly backward-looking to eliminate future lookahead bias:
- `temp_lag_1h` *(float)*: Temperature observed 1 hour prior ($T_{t-1}$).
- `temp_lag_2h` *(float)*: Temperature observed 2 hours prior ($T_{t-2}$).
- `temp_lag_3h` *(float)*: Temperature observed 3 hours prior ($T_{t-3}$).
- `temp_lag_6h` *(float)*: Temperature observed 6 hours prior ($T_{t-6}$).
- `temp_lag_12h` *(float)*: Temperature observed 12 hours prior ($T_{t-12}$).
- `temp_lag_24h` *(float)*: Temperature observed at the exact same hour yesterday ($T_{t-24}$).
- `temp_trend_1h` *(float)*: One-hour gradient $T_{t-1} - T_{t-2}$.

### 4. Rolling Window Statistics
- `temp_rolling_mean_3h` *(float)*: Moving average over the preceding 3-hour window.
- `temp_rolling_std_3h` *(float)*: Temperature standard deviation / volatility over 3 hours.
- `temp_rolling_mean_6h` *(float)*: Moving average over the preceding 6-hour window.
- `temp_rolling_max_6h` *(float)*: Maximum temperature observed in the preceding 6 hours.
- `temp_rolling_min_6h` *(float)*: Minimum temperature observed in the preceding 6 hours.
- `uhi_delta_celsius` *(float)*: Local urban heat island excess over vegetative baseline.

### 5. Meteorological & Solar Covariates
- `relative_humidity_percent` *(float)*: Ambient relative humidity (28% to 96%).
- `precipitation_mm` *(float)*: Liquid precipitation in mm.
- `cloud_cover_octas` *(int)*: Effective cloud cover (0 to 8 octas).
- `solar_ghi_wm2` *(float)*: Global Horizontal Irradiance in W/m².
- `solar_dni_wm2` *(float)*: Direct Normal Irradiance in W/m².
- `solar_dhi_wm2` *(float)*: Diffuse Horizontal Irradiance in W/m².

### 6. Atmospheric & Air Quality Covariates
- `air_quality_idx` *(float)*: Overall US Air Quality Index (AQI).
- `air_quality_pm25` *(float)*: Fine particulate matter (PM2.5) index.
- `air_quality_pm10` *(float)*: Coarse particulate matter (PM10) index.
- `air_quality_no2` *(float)*: Nitrogen dioxide index.
- `air_quality_o3` *(float)*: Ground-level ozone index.

---

##  Benchmark Model Evaluation

A baseline autoregressive model is provided in [`train_baseline.py`](train_baseline.py). It runs directly using the Python standard library.

### Test Set Performance (Holdout Days 26–30)

| Model Architecture | Features Used | Test MAE | Test RMSE | Test R² |
| :--- | :--- | :---: | :---: | :---: |
| **Naive Persistence Baseline** | $T_{t-1}$ only | 0.689 °C | 0.828 °C | 0.9577 |
| **Autoregressive Ridge Model** | Lags (1h, 2h, 24h) + Rolling 3h + Solar + RH + UHI | **0.420 °C** | **0.526 °C** | **0.9830** |

To reproduce these metrics:
```bash
python3 data/train_baseline.py
```

---

##  Quickstart: Training Models with Python

### Option A: Scikit-Learn (Random Forest / Gradient Boosting)
```python
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score

# Load splits
train_df = pd.read_csv("data/train.csv")
test_df = pd.read_csv("data/test.csv")

feature_cols = [
    "temp_lag_1h", "temp_lag_2h", "temp_lag_24h", 
    "temp_rolling_mean_3h", "sin_hour", "cos_hour",
    "relative_humidity_percent", "solar_ghi_wm2", "uhi_delta_celsius"
]
target = "target_temperature_celsius"

model = HistGradientBoostingRegressor(max_iter=200, random_state=42)
model.fit(train_df[feature_cols], train_df[target])

preds = model.predict(test_df[feature_cols])
print(f"Test MAE: {mean_absolute_error(test_df[target], preds):.3f} °C")
print(f"Test R²:  {r2_score(test_df[target], preds):.4f}")
```

### Option B: PyTorch (LSTM Sequence Model)
```python
import torch
import torch.nn as nn

class UrbanHeatLSTM(nn.Module):
    def __init__(self, input_dim=10, hidden_dim=64, num_layers=2):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        # Predict temperature at the final time step
        return self.fc(out[:, -1, :])
```

---

##  Regenerating or Extending the Dataset

To re-run the pipeline or extend it to new coordinates or time windows:
```bash
python3 data/build_dataset.py
```
