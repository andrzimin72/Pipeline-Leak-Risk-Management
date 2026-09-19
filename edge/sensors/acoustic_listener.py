# edge/sensors/acoustic_listener.py
import paho.mqtt.client as mqtt
import time, json, numpy as np, sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from shared.constants import ALERT_THRESHOLD_DB

client = mqtt.Client()
client.connect("localhost", 1883, 60)
client.loop_start()

print("🎧 Starting Acoustic MQTT Publisher...")
try:
    while True:
        is_leak = np.random.choice([True, False], p=[0.1, 0.9])
        value = np.random.uniform(0.45, 0.60) if is_leak else np.random.uniform(0.10, 0.30)
        
        client.publish("exxonmobil/pipeline/node042/acoustic", json.dumps({"value": value, "timestamp": time.time()}))
        print(f"🎧 Acoustic RMS: {value:.3f} {'🚨 LEAK' if value > ALERT_THRESHOLD_DB else '✅ Normal'}")
        time.sleep(2)
except KeyboardInterrupt:
    client.loop_stop()