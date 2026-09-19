# edge/federated_client.py
"""
NVIDIA Jetson Federated Learning Client.
Trains the local PhysicsNeMo model on proprietary sensor data 
and sends only encrypted weight updates to the Nebius Cloud via mTLS.
"""

import time
import json
import uuid
import os
import ssl
import requests
import numpy as np
from dataclasses import dataclass

@dataclass
class LocalTrainingConfig:
    node_id: str
    learning_rate: float = 0.01
    local_epochs: int = 5
    batch_size: int = 32

class FederatedPhysicsNeMoClient:
    def __init__(self, config: LocalTrainingConfig):
        self.node_id = config.node_id
        self.learning_rate = config.learning_rate
        self.local_weights = np.array([0.015, 0.05, 10.0], dtype=np.float32)
        
        # --- mTLS Security Configuration for HTTP ---
        self.cert_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../security/certs'))
        self.client_cert = (os.path.join(self.cert_dir, "client.crt"), os.path.join(self.cert_dir, "client.key"))
        self.ca_cert = os.path.join(self.cert_dir, "ca.crt")
        
        print(f"🧠 Initialized Secure Federated Client for Node {self.node_id}")
        print(f"🔒 mTLS Certificates loaded from {self.cert_dir}")

    def simulate_local_training(self, local_sensor_data: list) -> np.ndarray:
        print(f"🔄 Starting local training on {len(local_sensor_data)} private samples...")
        mock_gradients = np.random.normal(0, 0.001, size=self.local_weights.shape)
        self.local_weights = self.local_weights - (self.learning_rate * mock_gradients)
        weight_delta = self.local_weights - self.get_global_weights_baseline()
        return weight_delta

    def get_global_weights_baseline(self) -> np.ndarray:
        return np.array([0.015, 0.05, 10.0], dtype=np.float32)

    def send_update_to_cloud(self, weight_delta: np.ndarray):
        payload = {
            "node_id": self.node_id,
            "round_id": str(uuid.uuid4()),
            "weight_delta": weight_delta.tolist(),
            "num_samples": 100
        }
        
        print(f"📡 Sending encrypted weight delta to Nebius Cloud via mTLS...")
        
        try:
            # Secure HTTP POST using mTLS certificates
            response = requests.post(
                "https://api.nebius.com/v1/federated/update", 
                json=payload,
                cert=self.client_cert,
                verify=self.ca_cert
            )
            response.raise_for_status()
            print("✅ Secure update transmitted successfully.")
        except requests.exceptions.RequestException as e:
            print(f" Secure transmission failed: {e}")

def run_federated_client():
    config = LocalTrainingConfig(node_id="JETSON-NODE-042")
    client = FederatedPhysicsNeMoClient(config)
    local_private_data = [{"pressure": 980, "flow": 100, "temp": 25}] * 100 
    
    while True:
        print("\n--- Federated Learning Round ---")
        weight_delta = client.simulate_local_training(local_private_data)
        client.send_update_to_cloud(weight_delta)
        print("✅ Local training complete. Waiting for next aggregation round...")
        time.sleep(10)

if __name__ == "__main__":
    run_federated_client()