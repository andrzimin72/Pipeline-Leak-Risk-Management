# edge/sensors/corrosion_listener.py
import paho.mqtt.client as mqtt
import time, json, numpy as np, sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from shared.constants import CORROSION_RATE_THRESHOLD_MPY

client = mqtt.Client()
client.connect("localhost", 1883, 60)
client.loop_start()

print("🧪 Starting Corrosion Rate MQTT Publisher...")
try:
    while True:
        is_failure = np.random.choice([True, False], p=[0.1, 0.9])
        value = np.random.uniform(8.0, 15.0) if is_failure else np.random.uniform(1.0, 2.5)
        
        client.publish("exxonmobil/pipeline/node042/corrosion", json.dumps({"value": value, "timestamp": time.time()}))
        print(f"🧪 Corrosion Rate: {value:.2f} MPY {'🚨 FAILURE' if value > CORROSION_RATE_THRESHOLD_MPY else '✅ Normal'}")
        time.sleep(2)
except KeyboardInterrupt:
    client.loop_stop()