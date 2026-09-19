# edge/sensors/pressure_listener.py
import paho.mqtt.client as mqtt
import time, json, numpy as np, sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from shared.constants import PRESSURE_DROP_THRESHOLD_PSI

client = mqtt.Client()
client.connect("localhost", 1883, 60)
client.loop_start()

print("📉 Starting Pressure MQTT Publisher...")
try:
    while True:
        is_leak = np.random.choice([True, False], p=[0.1, 0.9])
        value = np.random.uniform(30.0, 50.0) if is_leak else np.random.uniform(2.0, 8.0)
        
        client.publish("exxonmobil/pipeline/node042/pressure", json.dumps({"value": value, "timestamp": time.time()}))
        print(f"📉 Pressure Drop: {value:.2f} PSI {'🚨 LEAK' if value > PRESSURE_DROP_THRESHOLD_PSI else '✅ Normal'}")
        time.sleep(2)
except KeyboardInterrupt:
    client.loop_stop()