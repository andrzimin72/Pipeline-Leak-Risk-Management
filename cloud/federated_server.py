# cloud/federated_server.py
"""
Nebius Cloud Federated Aggregation Server.
Receives weight updates from edge nodes and computes the new Global Model.
"""

import numpy as np
from typing import List, Dict

class FederatedAggregationServer:
    def __init__(self):
        # The Global Model weights (initialized to baseline)
        self.global_weights = np.array([0.015, 0.05, 10.0], dtype=np.float32)
        self.received_updates: List[Dict] = []
        
        print("☁️ Initialized Nebius Federated Aggregation Server")

    def receive_update(self, node_id: str, weight_delta: list, num_samples: int):
        """Receives an encrypted update from an edge node."""
        print(f"📥 Received update from Node {node_id} ({num_samples} samples)")
        self.received_updates.append({
            "node_id": node_id,
            "delta": np.array(weight_delta, dtype=np.float32),
            "weight": num_samples # Weight the update by the amount of data the node has
        })

    def aggregate_global_model(self):
        """
        Performs Federated Averaging (FedAvg).
        Combines all local updates into a new global model.
        """
        if not self.received_updates:
            print("⚠️ No updates received this round.")
            return

        print("\n🌍 Aggregating Global PhysicsNeMo Model...")
        
        total_weight = sum(update["weight"] for update in self.received_updates)
        weighted_delta_sum = np.zeros_like(self.global_weights)
        
        for update in self.received_updates:
            # Weighted average of the deltas
            weighted_delta_sum += update["delta"] * (update["weight"] / total_weight)
            
        # Update the global model
        self.global_weights += weighted_delta_sum
        
        print(f"✅ New Global Weights: {self.global_weights}")
        
        # Clear updates for the next round
        self.received_updates.clear()
        
        # In production: Push self.global_weights back to all Edge Clients via secure channel
        return self.global_weights

# ==============================================================================
# Simulation
# ==============================================================================
def run_federated_server():
    server = FederatedAggregationServer()
    
    # Simulate receiving updates from 3 different pipeline nodes
    print("--- Simulating Federated Round ---")
    server.receive_update("JETSON-NODE-042", [0.001, -0.002, 0.5], 100)
    server.receive_update("JETSON-NODE-043", [-0.001, 0.001, 0.2], 150)
    server.receive_update("JETSON-NODE-044", [0.002, -0.001, 0.8], 80)
    
    # Aggregate
    server.aggregate_global_model()

if __name__ == "__main__":
    run_federated_server()