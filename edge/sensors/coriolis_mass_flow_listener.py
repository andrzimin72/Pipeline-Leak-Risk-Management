# edge/sensors/coriolis_mass_flow_listener.py
import paho.mqtt.client as mqtt
import time, json, numpy as np, sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from shared.constants import MASS_IMBALANCE_THRESHOLD_PERCENT

client = mqtt.Client()
client.connect("localhost", 1883, 60)
client.loop_start()

print("️  Starting Coriolis Mass Flow MQTT Publisher...")
try:
    while True:
        is_leak = np.random.choice([True, False], p=[0.1, 0.9])
        value = np.random.uniform(1.5, 4.0) if is_leak else np.random.uniform(0.05, 0.2)
        
        client.publish("exxonmobil/pipeline/node042/coriolis_mass", json.dumps({"value": value, "timestamp": time.time()}))
        print(f"⚖️  Mass Imbalance: {value:.2f}% {'🚨 LEAK' if value > MASS_IMBALANCE_THRESHOLD_PERCENT else '✅ Normal'}")
        time.sleep(2)
except KeyboardInterrupt:
    client.loop_stop()