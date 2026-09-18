# cloud/cosmos_black_swan_generator.py
"""
Cosmos Synthetic Data Generator (Black Swan Scenarios).
Feeds the PyTorch Transformer Sentinel with uncorrelated anomalies 
and injects synthetic context flags via MQTT.
"""

import time
import json
import paho.mqtt.client as mqtt

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TOPIC_PREFIX = "exxonmobil/pipeline/node042/"

class CosmosBlackSwanGenerator:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
        self.client.loop_start()
        print("🌌 Cosmos Black Swan Generator initialized. Connecting to MQTT...")

    def publish_sensor(self, sensor_name: str, value: float):
        payload = json.dumps({"value": value, "timestamp": time.time()})
        self.client.publish(f"{TOPIC_PREFIX}{sensor_name}", payload)

    def inject_context(self, context_flag: str):
        """Sends a control flag to the Sentinel to adjust sensitivity/tagging."""
        self.client.publish(f"{TOPIC_PREFIX}cosmos_context", context_flag)
        print(f"📡 Injected Cosmos Context: {context_flag}")

    def run_cascading_failure_scenario(self):
        """
        Scenario: Uncorrelated Multimodal Spike.
        Designed to maximize the Transformer's reconstruction error (MSE).
        """
        print("\n🌌  STARTING COSMOS SCENARIO: Uncorrelated Black Swan Spike")
        
        # Phase 1: Warmup (Fill the Transformer's seq_len=10 buffer with normal data)
        print(" T+0s: Filling Transformer buffer with normal correlations...")
        for _ in range(12):
            for sensor in ["acoustic", "pressure", "coriolis_mass", "fiber_dts", "point_temp", 
                           "soil_moisture", "capacitance", "vibration", "corrosion", "standard_flow", "physics_residual"]:
                self.publish_sensor(sensor, 0.05) # Uniform normal state
            time.sleep(0.3)

        # Phase 2: Inject Black Swan Context
        print("⏳ T+3.6s: Injecting BLACK_SWAN context flag to Sentinel...")
        self.inject_context("BLACK_SWAN_CASCADING_FAILURE")
        time.sleep(1)

        # Phase 3: The Uncorrelated Spike (The "Black Swan")
        # We spike Pressure and Acoustic, but keep Vibration and Corrosion near zero.
        # The Transformer, expecting correlated physics, will fail to reconstruct this.
        print("💥 T+4.6s: Injecting Uncorrelated Anomaly Spike...")
        for _ in range(15):
            self.publish_sensor("acoustic", 0.85)      # SPIKE
            self.publish_sensor("pressure", 0.90)      # SPIKE
            self.publish_sensor("physics_residual", 0.80) # SPIKE
            
            # Keep these deliberately low to break physical correlation
            self.publish_sensor("vibration", 0.05)     
            self.publish_sensor("corrosion", 0.05)     
            self.publish_sensor("fiber_dts", 0.10)     
            self.publish_sensor("point_temp", 0.10)
            self.publish_sensor("coriolis_mass", 0.10)
            self.publish_sensor("soil_moisture", 0.05)
            self.publish_sensor("capacitance", 0.05)
            self.publish_sensor("standard_flow", 0.05)
            
            time.sleep(0.3)

        print("✅ Cosmos Scenario Complete. Awaiting Sentinel Transformer reaction...\n")
        self.client.loop_stop()

if __name__ == "__main__":
    cosmos = CosmosBlackSwanGenerator()
    cosmos.run_cascading_failure_scenario()