# edge/sensors/vibration_listener.py
import paho.mqtt.client as mqtt
import time, json, numpy as np, sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from shared.constants import VIBRATION_THRESHOLD_G

client = mqtt.Client()
client.connect("localhost", 1883, 60)
client.loop_start()

print("📳 Starting Vibration MQTT Publisher...")
try:
    while True:
        # Simulate excavator interference 15% of the time
        is_excavator = np.random.choice([True, False], p=[0.15, 0.85])
        value = np.random.uniform(0.9, 1.5) if is_excavator else np.random.uniform(0.1, 0.4)
        
        client.publish("exxonmobil/pipeline/node042/vibration", json.dumps({"value": value, "timestamp": time.time()}))
        print(f"📳 Vibration: {value:.2f}g {'️ EXCAVATOR' if value > VIBRATION_THRESHOLD_G else '✅ Normal'}")
        time.sleep(2)
except KeyboardInterrupt:
    client.loop_stop()