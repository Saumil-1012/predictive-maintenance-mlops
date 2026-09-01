import asyncio
import json
import random
import time
import os
from datetime import datetime

CONNECTION_STRING = os.getenv("IOT_CONNECTION_STRING", None)
DEVICE_ID = "machine-001"
SEND_INTERVAL_SECONDS = 3


def generate_telemetry(device_id: str) -> dict:
    is_anomaly = random.random() < 0.05

    if is_anomaly:
        temperature = round(random.uniform(120, 150), 2)
        vibration   = round(random.uniform(2.0, 5.0), 3)
    else:
        temperature = round(random.uniform(70, 95), 2)
        vibration   = round(random.uniform(0.1, 0.5), 3)

    return {
        "device_id":           device_id,
        "timestamp":           time.time(),
        "datetime":            datetime.utcnow().isoformat() + "Z",
        "temperature_c":       temperature,
        "vibration_g":         vibration,
        "pressure_bar":        round(random.uniform(100, 110), 2),
        "rpm":                 round(random.uniform(2900, 3100), 1),
        "is_anomaly_injected": is_anomaly,
    }


def print_reading(payload: dict):
    status = "🚨 ANOMALY" if payload["is_anomaly_injected"] else "✅ Normal "
    print(
        f"[{payload['datetime']}] {status} | "
        f"Temp: {payload['temperature_c']:>6}°C | "
        f"Vib: {payload['vibration_g']:>5}g | "
        f"Pressure: {payload['pressure_bar']} bar"
    )


async def run_local():
    print("=" * 65)
    print("  IoT Simulator — LOCAL MODE")
    print("  Saving data to: iot_simulator/sensor_data.json")
    print("  Press Ctrl+C to stop")
    print("=" * 65)

    readings = []
    output_path = "iot_simulator/sensor_data.json"

    try:
        while True:
            payload = generate_telemetry(DEVICE_ID)
            readings.append(payload)
            print_reading(payload)

            with open(output_path, "w") as f:
                json.dump(readings, f, indent=2)

            await asyncio.sleep(SEND_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print(f"\n✅ Stopped. {len(readings)} readings saved to {output_path}")


async def run_azure():
    from azure.iot.device.aio import IoTHubDeviceClient

    print("=" * 65)
    print("  IoT Simulator — AZURE MODE")
    print(f"  Sending to IoT Hub every {SEND_INTERVAL_SECONDS}s")
    print("  Press Ctrl+C to stop")
    print("=" * 65)

    client = await IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)

    try:
        while True:
            payload = generate_telemetry(DEVICE_ID)
            await client.send_message(json.dumps(payload))
            print_reading(payload)
            await asyncio.sleep(SEND_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\n✅ Stopped.")
    finally:
        await client.shutdown()


if __name__ == "__main__":
    if CONNECTION_STRING:
        asyncio.run(run_azure())
    else:
        print("ℹ️  No IOT_CONNECTION_STRING found — running in local mode\n")
        asyncio.run(run_local())