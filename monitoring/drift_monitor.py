import json
import pandas as pd
import numpy as np
import os
from datetime import datetime

# ─────────────────────────────────────────────
# 1. LOAD REFERENCE DATA (training distribution)
# ─────────────────────────────────────────────
print("📂 Loading reference data (training distribution)...")
with open("iot_simulator/sensor_data.json", "r") as f:
    raw = json.load(f)

reference_df = pd.DataFrame(raw)
reference_df = reference_df[[
    "temperature_c", "vibration_g", "pressure_bar", "rpm"
]]
print(f"   Reference data: {len(reference_df)} readings")

# ─────────────────────────────────────────────
# 2. SIMULATE PRODUCTION DATA
# ─────────────────────────────────────────────
def generate_production_data(drifted=False, n=50):
    rows = []
    for _ in range(n):
        if drifted:
            rows.append({
                "temperature_c": round(np.random.uniform(100, 130), 2),
                "vibration_g":   round(np.random.uniform(0.5, 2.0), 3),
                "pressure_bar":  round(np.random.uniform(108, 120), 2),
                "rpm":           round(np.random.uniform(3100, 3400), 1),
            })
        else:
            rows.append({
                "temperature_c": round(np.random.uniform(70, 95), 2),
                "vibration_g":   round(np.random.uniform(0.1, 0.5), 3),
                "pressure_bar":  round(np.random.uniform(100, 110), 2),
                "rpm":           round(np.random.uniform(2900, 3100), 1),
            })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# 3. MANUAL DRIFT DETECTION using statistics
# (works with any evidently version)
# ─────────────────────────────────────────────
from scipy import stats

def run_drift_check(reference_df, current_df, label=""):
    print(f"\n{'='*55}")
    print(f"  Running drift check: {label}")
    print(f"{'='*55}")

    columns = ["temperature_c", "vibration_g", "pressure_bar", "rpm"]
    drifted_cols = []

    print(f"\n  Per-column drift (KS test, threshold p<0.05):")
    for col in columns:
        ref_vals  = reference_df[col].dropna()
        curr_vals = current_df[col].dropna()

        # Kolmogorov-Smirnov test
        ks_stat, p_value = stats.ks_2samp(ref_vals, curr_vals)
        drifted = p_value < 0.05

        if drifted:
            drifted_cols.append(col)

        ref_mean  = ref_vals.mean()
        curr_mean = curr_vals.mean()
        mean_shift = curr_mean - ref_mean

        print(f"    {'🚨' if drifted else '✅'} {col:<20} "
              f"p={p_value:.4f}  "
              f"ref_mean={ref_mean:.2f}  "
              f"curr_mean={curr_mean:.2f}  "
              f"shift={mean_shift:+.2f}")

    dataset_drift = len(drifted_cols) >= 2
    drift_share   = len(drifted_cols) / len(columns)

    print(f"\n  Dataset drift detected: {'🚨 YES' if dataset_drift else '✅ NO'}")
    print(f"  Drifted columns: {len(drifted_cols)}/{len(columns)}")
    print(f"  Drift share: {drift_share:.0%}")

    # Save simple report
    os.makedirs("monitoring/reports", exist_ok=True)
    report_path = f"monitoring/reports/drift_{label.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_path, "w") as f:
        f.write(f"Drift Report — {label}\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"Dataset drift: {dataset_drift}\n")
        f.write(f"Drifted columns: {drifted_cols}\n")
    print(f"\n  📄 Report saved: {report_path}")

    return dataset_drift


# ─────────────────────────────────────────────
# 4. RUN BOTH SCENARIOS
# ─────────────────────────────────────────────
print("\n🔍 Scenario 1: Normal production data (no drift expected)")
normal_df = generate_production_data(drifted=False, n=50)
drift_detected = run_drift_check(reference_df, normal_df, label="normal production")

if drift_detected:
    print("\n⚠️  Unexpected drift — would trigger retraining")
else:
    print("\n✅ No drift — model is healthy, no retraining needed")


print("\n\n🔍 Scenario 2: Drifted production data (drift expected)")
drifted_df = generate_production_data(drifted=True, n=50)
drift_detected = run_drift_check(reference_df, drifted_df, label="drifted production")

if drift_detected:
    print("\n🚨 DRIFT DETECTED — triggering retraining pipeline!")
    print("   In production this calls:")
    print("   → Azure ML pipeline REST endpoint")
    print("   → Kicks off ml/train.py with new data")
    print("   → Registers new model version in AzureML")
    print("   → CI/CD redeploys updated container to AKS")
else:
    print("\n✅ No drift detected")