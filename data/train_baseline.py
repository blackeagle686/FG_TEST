#!/usr/bin/env python3
"""
Baseline Time Series Forecasting Model for Urban Heat Prediction
Trains an autoregressive multi-feature regression model on train.csv,
evaluates on val.csv and test.csv, and reports benchmark metrics (MAE, RMSE, R²).
No external heavy dependencies required (pure Python standard library).
"""

import csv
import math
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent

def load_split(filepath):
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def extract_features(rows):
    """
    Selects predictive features:
    - Autoregressive lags: temp_lag_1h, temp_lag_2h, temp_lag_24h
    - Rolling statistics: temp_rolling_mean_3h, temp_trend_1h
    - Cyclical time: sin_hour, cos_hour
    - Atmospheric covariates: relative_humidity_percent, solar_ghi_wm2
    - Target: target_temperature_celsius
    """
    X = []
    y = []
    feature_names = [
        "temp_lag_1h", "temp_lag_2h", "temp_lag_24h",
        "temp_rolling_mean_3h", "temp_trend_1h",
        "sin_hour", "cos_hour",
        "relative_humidity_percent", "solar_ghi_wm2",
        "uhi_delta_celsius"
    ]
    
    for r in rows:
        features = [1.0] # Bias / Intercept term
        for fn in feature_names:
            features.append(float(r[fn]))
        X.append(features)
        y.append(float(r["target_temperature_celsius"]))
        
    return X, y, feature_names

def train_linear_model_gd(X, y, epochs=400, lr=0.0005, l2_reg=0.01):
    """
    Trains a Ridge Regression model using batch gradient descent with feature standardization.
    """
    n_samples = len(X)
    n_features = len(X[0])
    
    # Compute mean and std for normalization (excluding bias column 0)
    means = [0.0] * n_features
    stds = [1.0] * n_features
    
    for j in range(1, n_features):
        vals = [X[i][j] for i in range(n_samples)]
        m = sum(vals) / n_samples
        s = math.sqrt(sum((v - m) ** 2 for v in vals) / n_samples)
        means[j] = m
        stds[j] = s if s > 1e-6 else 1.0
        
    # Standardize X
    X_norm = []
    for i in range(n_samples):
        row = [1.0]
        for j in range(1, n_features):
            row.append((X[i][j] - means[j]) / stds[j])
        X_norm.append(row)
        
    # Target normalization
    y_mean = sum(y) / n_samples
    y_std = math.sqrt(sum((v - y_mean) ** 2 for v in y) / n_samples)
    y_norm = [(v - y_mean) / y_std for v in y]
    
    # Initialize weights
    weights = [0.0] * n_features
    
    # Gradient Descent loop
    for epoch in range(epochs):
        # Predictions
        preds = []
        for i in range(n_samples):
            pred = sum(X_norm[i][j] * weights[j] for j in range(n_features))
            preds.append(pred)
            
        # Gradients
        errors = [preds[i] - y_norm[i] for i in range(n_samples)]
        
        for j in range(n_features):
            grad = (sum(errors[i] * X_norm[i][j] for i in range(n_samples)) / n_samples) + (l2_reg * weights[j] if j > 0 else 0)
            weights[j] -= lr * grad
            
    # Model artifact
    return {
        "weights": weights,
        "means": means,
        "stds": stds,
        "y_mean": y_mean,
        "y_std": y_std
    }

def predict(model, X):
    n_features = len(model["weights"])
    preds = []
    for row in X:
        x_norm = [1.0]
        for j in range(1, n_features):
            x_norm.append((row[j] - model["means"][j]) / model["stds"][j])
        pred_norm = sum(x_norm[j] * model["weights"][j] for j in range(n_features))
        preds.append(round(pred_norm * model["y_std"] + model["y_mean"], 2))
    return preds

def evaluate_metrics(y_true, y_pred):
    n = len(y_true)
    mae = sum(abs(yt - yp) for yt, yp in zip(y_true, y_pred)) / n
    mse = sum((yt - yp) ** 2 for yt, yp in zip(y_true, y_pred)) / n
    rmse = math.sqrt(mse)
    
    mean_y = sum(y_true) / n
    ss_tot = sum((yt - mean_y) ** 2 for yt, yp in zip(y_true, y_pred))
    ss_res = sum((yt - yp) ** 2 for yt, yp in zip(y_true, y_pred))
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    
    mape = (sum(abs(yt - yp) / abs(yt) for yt, yp in zip(y_true, y_pred) if yt != 0) / n) * 100.0
    
    return {
        "MAE_celsius": round(mae, 3),
        "RMSE_celsius": round(rmse, 3),
        "MAPE_percent": round(mape, 2),
        "R2_score": round(r2, 4)
    }

def main():
    print("=" * 65)
    print("BASELINE TIME SERIES MODEL: URBAN HEAT PREDICTION")
    print("=" * 65)
    
    train_file = DATA_DIR / "train.csv"
    val_file = DATA_DIR / "val.csv"
    test_file = DATA_DIR / "test.csv"
    
    if not train_file.exists():
        print("Error: train.csv not found. Run build_dataset.py first.")
        return
        
    print(f"Loading datasets from {DATA_DIR}...")
    train_rows = load_split(train_file)
    val_rows = load_split(val_file)
    test_rows = load_split(test_file)
    
    X_train, y_train, feature_names = extract_features(train_rows)
    X_val, y_val, _ = extract_features(val_rows)
    X_test, y_test, _ = extract_features(test_rows)
    
    print(f"Train samples : {len(X_train)} rows")
    print(f"Val samples   : {len(X_val)} rows")
    print(f"Test samples  : {len(X_test)} rows")
    print(f"Features ({len(feature_names)}): {', '.join(feature_names)}")
    
    # 1. Baseline: Naive Persistence (T_t = T_{t-1})
    naive_pred_test = [float(r["temp_lag_1h"]) for r in test_rows]
    naive_metrics = evaluate_metrics(y_test, naive_pred_test)
    print("\n--- Model 1: Naive Persistence Baseline (T_t = T_{t-1}) ---")
    print(f"Test MAE   : {naive_metrics['MAE_celsius']} °C")
    print(f"Test RMSE  : {naive_metrics['RMSE_celsius']} °C")
    print(f"Test R²    : {naive_metrics['R2_score']}")
    
    # 2. Trained Ridge Regression Model
    print("\n--- Training Model 2: Autoregressive Ridge Regression ---")
    model = train_linear_model_gd(X_train, y_train, epochs=600, lr=0.01, l2_reg=0.05)
    
    val_preds = predict(model, X_val)
    val_metrics = evaluate_metrics(y_val, val_preds)
    print(f"Validation MAE  : {val_metrics['MAE_celsius']} °C | RMSE: {val_metrics['RMSE_celsius']} °C | R²: {val_metrics['R2_score']}")
    
    test_preds = predict(model, X_test)
    test_metrics = evaluate_metrics(y_test, test_preds)
    print(f"Test MAE        : {test_metrics['MAE_celsius']} °C | RMSE: {test_metrics['RMSE_celsius']} °C | R²: {test_metrics['R2_score']}")
    
    # Save predictions
    pred_path = DATA_DIR / "baseline_predictions.csv"
    with open(pred_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "location_id", "actual_temperature_c", "predicted_temperature_c", "error_c"])
        for r, yt, yp in zip(test_rows, y_test, test_preds):
            writer.writerow([r["timestamp"], r["location_id"], yt, yp, round(yp - yt, 2)])
    print(f"\nSaved test predictions to: {pred_path}")
    print("=" * 65)

if __name__ == "__main__":
    main()
