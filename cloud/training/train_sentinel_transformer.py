# cloud/training/train_sentinel_transformer.py
"""
PyTorch Training Script for the Sentinel Transformer Autoencoder.
Trains exclusively on NORMAL pipeline data to learn physical correlations.
"""

import os
import sys
import json
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from edge.agents.sentinel_agent import TimeSeriesTransformerAE

# ==============================================================================
# 1. Synthetic Normal Data Generation
# ==============================================================================
def generate_normal_data(num_sequences=1000, seq_len=10, num_features=11):
    """
    Generates correlated normal sensor data. 
    In a real scenario, this is historical data from a healthy pipeline.
    """
    data = []
    for _ in range(num_sequences):
        # Base state with slight random drift
        base_state = np.random.uniform(0.05, 0.15, num_features)
        sequence = []
        for t in range(seq_len):
            # Add temporal noise, but keep features correlated
            noise = np.random.normal(0, 0.02, num_features)
            step = base_state + noise
            sequence.append(step)
        data.append(sequence)
    return np.array(data, dtype=np.float32)

# ==============================================================================
# 2. Training Loop
# ==============================================================================
def train_model():
    print(" Starting Sentinel Transformer Training...")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Hyperparameters
    SEQ_LEN = 10
    NUM_FEATURES = 11
    BATCH_SIZE = 64
    EPOCHS = 50
    LEARNING_RATE = 0.001

    # Initialize Model
    model = TimeSeriesTransformerAE(num_features=NUM_FEATURES, d_model=32, n_heads=2, num_layers=2).to(device)
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    criterion = nn.MSELoss()

    # Generate Data
    train_data = generate_normal_data(num_sequences=800, seq_len=SEQ_LEN, num_features=NUM_FEATURES)
    val_data = generate_normal_data(num_sequences=200, seq_len=SEQ_LEN, num_features=NUM_FEATURES)

    train_tensor = torch.tensor(train_data).to(device)
    val_tensor = torch.tensor(val_data).to(device)

    print(f"Training on {train_tensor.shape[0]} sequences...")

    # Training Loop
    for epoch in range(EPOCHS):
        model.train()
        optimizer.zero_grad()
        
        # Forward pass
        reconstructed = model(train_tensor)
        
        # Calculate Loss (MSE)
        loss = criterion(reconstructed, train_tensor)
        
        # Backward pass
        loss.backward()
        optimizer.step()

        if (epoch + 1) % 10 == 0:
            print(f"Epoch [{epoch+1}/{EPOCHS}], Loss: {loss.item():.6f}")

    # ==============================================================================
    # 3. Calculate Anomaly Threshold
    # ==============================================================================
    print("\n📊 Calculating Anomaly Threshold on Validation Data...")
    model.eval()
    with torch.no_grad():
        val_reconstructed = model(val_tensor)
        # Calculate MSE per sequence
        val_mse = torch.mean((val_tensor - val_reconstructed) ** 2, dim=(1, 2)).cpu().numpy()
        
        # Set threshold at the 99th percentile of normal reconstruction error
        threshold = np.percentile(val_mse, 99)
        print(f"✅ Calculated Anomaly Threshold (99th percentile): {threshold:.6f}")

    # ==============================================================================
    # 4. Save Artifacts
    # ==============================================================================
    save_dir = "cloud/training/artifacts"
    os.makedirs(save_dir, exist_ok=True)
    
    # Save PyTorch weights
    torch.save(model.state_dict(), os.path.join(save_dir, "sentinel_transformer.pth"))
    
    # Save threshold and metadata
    metadata = {
        "anomaly_threshold": float(threshold),
        "seq_len": SEQ_LEN,
        "num_features": NUM_FEATURES,
        "d_model": 32,
        "n_heads": 2,
        "num_layers": 2
    }
    with open(os.path.join(save_dir, "model_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=4)
        
    print(f"💾 Model and metadata saved to {save_dir}")

if __name__ == "__main__":
    train_model()