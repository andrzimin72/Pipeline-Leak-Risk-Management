# edge/sensors/soil_moisture_listener.py
import paho.mqtt.client as mqtt
import time, json, numpy as np, sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from shared.constants import SOIL_MOISTURE_CHANGE_THRESHOLD_PERCENT

client = mqtt.Client()
client.connect("localhost", 1883, 60)
client.loop_start()

print("💧 Starting Soil Moisture MQTT Publisher...")
try:
    while True:
        is_leak = np.random.choice([True, False], p=[0.1, 0.9])
        value = np.random.uniform(10.0, 20.0) if is_leak else np.random.uniform(1.0, 3.0)
        
        client.publish("exxonmobil/pipeline/node042/soil_moisture", json.dumps({"value": value, "timestamp": time.time()}))
        print(f"💧 Soil Moisture Change: {value:.2f}% {' LEAK' if value > SOIL_MOISTURE_CHANGE_THRESHOLD_PERCENT else '✅ Normal'}")
        time.sleep(2)
except KeyboardInterrupt:
    client.loop_stop()