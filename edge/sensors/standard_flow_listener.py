# edge/sensors/standard_flow_listener.py
import paho.mqtt.client as mqtt
import time, json, numpy as np, sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Standard flow uses a generic volumetric threshold (e.g., 2.0%)
STANDARD_FLOW_THRESHOLD = 2.0 

client = mqtt.Client()
client.connect("localhost", 1883, 60)
client.loop_start()

print(" Starting Standard Flow MQTT Publisher...")
try:
    while True:
        is_leak = np.random.choice([True, False], p=[0.1, 0.9])
        value = np.random.uniform(3.0, 6.0) if is_leak else np.random.uniform(0.5, 1.5)
        
        client.publish("exxonmobil/pipeline/node042/standard_flow", json.dumps({"value": value, "timestamp": time.time()}))
        print(f" Std Flow Imbalance: {value:.2f}% {'🚨 LEAK' if value > STANDARD_FLOW_THRESHOLD else '✅ Normal'}")
        time.sleep(2)
except KeyboardInterrupt:
    client.loop_stop()