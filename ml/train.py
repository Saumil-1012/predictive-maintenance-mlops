import json
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import MinMaxScaler
import joblib
import os

# ─────────────────────────────────────────────
# 1. LOAD DATA
# ─────────────────────────────────────────────
print("📂 Loading sensor data...")
with open("iot_simulator/sensor_data.json", "r") as f:
    raw = json.load(f)

df = pd.DataFrame(raw)
print(f"   {len(df)} total readings loaded")
print(f"   Anomalies in data: {df['is_anomaly_injected'].sum()}")

# ─────────────────────────────────────────────
# 2. FEATURE ENGINEERING
# ─────────────────────────────────────────────
print("\n⚙️  Engineering features...")

# Rolling averages (window of 5 readings)
df = df.sort_values("timestamp").reset_index(drop=True)
df["temp_rolling_avg"]  = df["temperature_c"].rolling(window=5, min_periods=1).mean()
df["vib_rolling_avg"]   = df["vibration_g"].rolling(window=5, min_periods=1).mean()

# Rate of change between readings
df["temp_delta"] = df["temperature_c"].diff().fillna(0)
df["vib_delta"]  = df["vibration_g"].diff().fillna(0)

# Select final feature columns for the model
FEATURE_COLS = [
    "temperature_c",
    "vibration_g",
    "pressure_bar",
    "rpm",
    "temp_rolling_avg",
    "vib_rolling_avg",
    "temp_delta",
    "vib_delta",
]

X = df[FEATURE_COLS].copy()
print(f"   Features used: {FEATURE_COLS}")

# ─────────────────────────────────────────────
# 3. NORMALIZE
# ─────────────────────────────────────────────
print("\n📏 Normalizing features...")
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)

# ─────────────────────────────────────────────
# 4. TRAIN ISOLATION FOREST
# ─────────────────────────────────────────────
print("\n🤖 Training Isolation Forest model...")
model = IsolationForest(
    n_estimators=100,
    contamination=0.05,   # we expect ~5% anomalies
    random_state=42,
    verbose=0
)
model.fit(X_scaled)

# ─────────────────────────────────────────────
# 5. EVALUATE ON TRAINING DATA
# ─────────────────────────────────────────────
print("\n📊 Evaluating model...")
preds  = model.predict(X_scaled)          # -1 = anomaly, 1 = normal
scores = model.decision_function(X_scaled) # lower = more anomalous

df["predicted_anomaly"] = (preds == -1)
df["anomaly_score"]     = scores

# Compare predictions vs injected anomalies
true_anomalies      = df["is_anomaly_injected"]
predicted_anomalies = df["predicted_anomaly"]

true_positives  = ((predicted_anomalies == True)  & (true_anomalies == True)).sum()
false_positives = ((predicted_anomalies == True)  & (true_anomalies == False)).sum()
false_negatives = ((predicted_anomalies == False) & (true_anomalies == True)).sum()
true_negatives  = ((predicted_anomalies == False) & (true_anomalies == False)).sum()

print(f"\n   Results:")
print(f"   ✅ True Positives  (caught real anomalies):   {true_positives}")
print(f"   ❌ False Positives (normal flagged as anomaly): {false_positives}")
print(f"   ⚠️  False Negatives (missed anomalies):         {false_negatives}")
print(f"   ✅ True Negatives  (normal correctly ignored): {true_negatives}")
print(f"\n   Mean anomaly score: {scores.mean():.4f}")
print(f"   Min anomaly score:  {scores.min():.4f}  ← most anomalous point")
print(f"   Max anomaly score:  {scores.max():.4f}  ← most normal point")

# ─────────────────────────────────────────────
# 6. SAVE MODEL + SCALER
# ─────────────────────────────────────────────
os.makedirs("model", exist_ok=True)
joblib.dump(model,  "model/model.pkl")
joblib.dump(scaler, "model/scaler.pkl")
joblib.dump(FEATURE_COLS, "model/feature_cols.pkl")

print("\n💾 Saved:")
print("   model/model.pkl")
print("   model/scaler.pkl")
print("   model/feature_cols.pkl")
print("\n✅ Training complete!")