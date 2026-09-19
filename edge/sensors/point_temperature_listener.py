# edge/sensors/point_temperature_listener.py
import paho.mqtt.client as mqtt
import time, json, numpy as np, sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from shared.constants import TEMP_DROP_THRESHOLD_CELSIUS

client = mqtt.Client()
client.connect("localhost", 1883, 60)
client.loop_start()

print("🌡️  Starting Point Temperature MQTT Publisher...")
try:
    while True:
        is_leak = np.random.choice([True, False], p=[0.1, 0.9])
        value = np.random.uniform(3.0, 6.0) if is_leak else np.random.uniform(0.1, 1.0)
        
        client.publish("exxonmobil/pipeline/node042/point_temp", json.dumps({"value": value, "timestamp": time.time()}))
        print(f"🌡️  Point Temp Drop: {value:.2f}°C {'🚨 LEAK' if value > TEMP_DROP_THRESHOLD_CELSIUS else '✅ Normal'}")
        time.sleep(2)
except KeyboardInterrupt:
    client.loop_stop()