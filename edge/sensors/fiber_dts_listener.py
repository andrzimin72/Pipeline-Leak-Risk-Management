# edge/sensors/fiber_dts_listener.py
import paho.mqtt.client as mqtt
import time, json, numpy as np, sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from shared.constants import FIBER_THERMAL_ANOMALY_THRESHOLD_C

client = mqtt.Client()
client.connect("localhost", 1883, 60)
client.loop_start()

print("🌡️  Starting Fiber DTS MQTT Publisher...")
try:
    while True:
        is_leak = np.random.choice([True, False], p=[0.1, 0.9])
        value = np.random.uniform(2.5, 5.0) if is_leak else np.random.uniform(0.1, 0.5)
        
        client.publish("exxonmobil/pipeline/node042/fiber_dts", json.dumps({"value": value, "timestamp": time.time()}))
        print(f"🌡️  Fiber Thermal Anomaly: {value:.2f}°C {'🚨 LEAK' if value > FIBER_THERMAL_ANOMALY_THRESHOLD_C else '✅ Normal'}")
        time.sleep(2)
except KeyboardInterrupt:
    client.loop_stop()