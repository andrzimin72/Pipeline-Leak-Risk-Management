# edge/agents/sentinel_agent.py
"""
Agent 1: The Sentinel (Perception & Anomaly Detection).
Production-ready Edge Agent supporting both PyTorch and TensorRT inference.
Optimized for NVIDIA Jetson Orin (Edge Deployment).
"""

import os
import sys
import time
import json
import uuid
import math
import logging
import collections
from typing import Dict, List, Tuple

import numpy as np
import torch
import torch.nn as nn

# TensorRT & PyCUDA imports for Jetson deployment
try:
    import tensorrt as trt
    import pycuda.driver as cuda
    import pycuda.autoinit
    TRT_AVAILABLE = True
except ImportError:
    TRT_AVAILABLE = False
    print("⚠️ TensorRT/PyCUDA not found. Falling back to PyTorch inference.")

from edge.agents.schemas import SitRep

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [SENTINEL] - %(levelname)s - %(message)s")
logger = logging.getLogger("SentinelAgent")

# ==============================================================================
# 1. PyTorch Transformer Architecture (Kept for training & fallback)
# ==============================================================================
class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 100):
        super().__init__()
        pe = torch.zeros(max_len, 1, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0, 0::2] = torch.sin(position * div_term)
        pe[:, 0, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:x.size(0), :]

class TimeSeriesTransformerAE(nn.Module):
    def __init__(self, num_features=11, d_model=32, n_heads=2, num_layers=2, max_seq_len=50, dropout=0.1):
        super().__init__()
        self.input_projection = nn.Linear(num_features, d_model)
        self.pos_encoder = PositionalEncoding(d_model, max_seq_len)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=n_heads, dim_feedforward=d_model*4, 
            dropout=dropout, batch_first=False, activation='gelu'
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.output_projection = nn.Linear(d_model, num_features)

    def forward(self, src: torch.Tensor) -> torch.Tensor:
        x = self.input_projection(src).permute(1, 0, 2) 
        x = self.pos_encoder(x)
        x = self.transformer_encoder(x)
        x = x.permute(1, 0, 2) 
        return self.output_projection(x)

# ==============================================================================
# 2. TensorRT Helper Functions
# ==============================================================================
def allocate_buffers(engine):
    """Allocates host and device buffers for TensorRT inference."""
    inputs, outputs, bindings, stream = [], [], [], cuda.Stream()
    for binding in engine:
        size = trt.volume(engine.get_binding_shape(binding)) * engine.max_batch_size
        dtype = trt.nptype(engine.get_binding_dtype(binding))
        host_mem = cuda.pagelocked_empty(size, dtype)
        device_mem = cuda.mem_alloc(host_mem.nbytes)
        bindings.append(int(device_mem))
        if engine.binding_is_input(binding):
            inputs.append({'host': host_mem, 'device': device_mem})
        else:
            outputs.append({'host': host_mem, 'device': device_mem})
    return inputs, outputs, bindings, stream

def do_inference(context, bindings, inputs, outputs, stream):
    """Executes TensorRT inference."""
    [cuda.memcpy_htod_async(inp['device'], inp['host'], stream) for inp in inputs]
    context.execute_async_v2(bindings=bindings, stream_handle=stream.handle)
    [cuda.memcpy_dtoh_async(out['host'], out['device'], stream) for out in outputs]
    stream.synchronize()
    return [out['host'] for out in outputs]

# ==============================================================================
# 3. Agent 1: The Sentinel
# ==============================================================================
class SentinelAgent:
    def __init__(self, node_id: str, seq_len: int = 10, model_dir: str = "cloud/deployment/jetson_artifacts"):
        self.node_id = node_id
        self.seq_len = seq_len
        self.feature_names = [
            "acoustic", "pressure", "coriolis_mass", "fiber_dts", "point_temp",
            "soil_moisture", "capacitance", "vibration", "corrosion", 
            "standard_flow", "physics_residual"
        ]
        self.num_features = len(self.feature_names)
        self.model_dir = model_dir
        
        # Sliding window buffer
        self.sequence_buffer = collections.deque(maxlen=self.seq_len)
        self.cosmos_context = "NORMAL"
        
        # Load Metadata (Thresholds & Config)
        self.metadata = self._load_metadata()
        self.threshold_suspicious = self.metadata.get("anomaly_threshold", 0.15)
        self.threshold_critical = self.threshold_suspicious * 2.5
        
        # Initialize Inference Engine (TensorRT preferred, PyTorch fallback)
        self.inference_mode = "PYTORCH"
        self.model = None
        self.trt_context = None
        self.trt_inputs = None
        self.trt_outputs = None
        self.trt_bindings = None
        self.trt_stream = None
        
        self._initialize_engine()
        
        logger.info(f"Sentinel Agent initialized on Node {self.node_id} | Mode: {self.inference_mode}")
        logger.info(f"Anomaly Thresholds -> Suspicious: {self.threshold_suspicious:.4f} | Critical: {self.threshold_critical:.4f}")

    def _load_metadata(self) -> dict:
        meta_path = os.path.join(self.model_dir, "model_metadata.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                return json.load(f)
        logger.warning("Metadata not found. Using default thresholds.")
        return {"anomaly_threshold": 0.15, "num_features": 11, "d_model": 32, "n_heads": 2, "num_layers": 2}

    def _initialize_engine(self):
        """Attempts to load TensorRT engine, falls back to PyTorch."""
        engine_path = os.path.join(self.model_dir, "sentinel_transformer.engine")
        pth_path = os.path.join(self.model_dir, "sentinel_transformer.pth")

        # Try TensorRT first
        if TRT_AVAILABLE and os.path.exists(engine_path):
            logger.info(f"Loading TensorRT Engine from {engine_path}...")
            TRT_LOGGER = trt.Logger(trt.Logger.WARNING)
            with open(engine_path, 'rb') as f:
                runtime = trt.Runtime(TRT_LOGGER)
                engine = runtime.deserialize_cuda_engine(f.read())
            
            self.trt_context = engine.create_execution_context()
            self.trt_inputs, self.trt_outputs, self.trt_bindings, self.trt_stream = allocate_buffers(engine)
            self.inference_mode = "TENSORRT"
            return

        # Fallback to PyTorch
        if os.path.exists(pth_path):
            logger.info(f"Loading PyTorch Model from {pth_path}...")
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model = TimeSeriesTransformerAE(
                num_features=self.metadata["num_features"],
                d_model=self.metadata["d_model"],
                n_heads=self.metadata["n_heads"],
                num_layers=self.metadata["num_layers"]
            ).to(self.device)
            self.model.load_state_dict(torch.load(pth_path, map_location=self.device))
            self.model.eval()
            self.inference_mode = "PYTORCH"
            return

        logger.error("No model artifacts found! Using untrained random weights.")
        self.device = torch.device("cpu")
        self.model = TimeSeriesTransformerAE(num_features=self.num_features).to(self.device)
        self.model.eval()

    def inject_cosmos_context(self, context_flag: str):
        self.cosmos_context = context_flag
        logger.info(f"Cosmos Context Updated: {self.cosmos_context}")

    def update_buffer(self, normalized_scores: Dict[str, float]):
        ordered_values = [normalized_scores.get(k, 0.0) for k in self.feature_names]
        self.sequence_buffer.append(ordered_values)

    def calculate_anomaly(self) -> Tuple[float, str]:
        if len(self.sequence_buffer) < self.seq_len:
            return 0.0, "WAITING_FOR_DATA"

        sequence_data = np.array(list(self.sequence_buffer), dtype=np.float32)
        
        # --- TENSORRT INFERENCE PATH ---
        if self.inference_mode == "TENSORRT":
            self.trt_inputs[0]['host'] = sequence_data.flatten()
            trt_outputs = do_inference(
                self.trt_context, self.trt_bindings, 
                self.trt_inputs, self.trt_outputs, self.trt_stream
            )
            reconstructed = trt_outputs[0].reshape(self.seq_len, self.num_features)
            
        # --- PYTORCH INFERENCE PATH ---
        else:
            input_tensor = torch.tensor(sequence_data).unsqueeze(0).to(self.device)
            with torch.no_grad():
                reconstructed_tensor = self.model(input_tensor)
            reconstructed = reconstructed_tensor.squeeze(0).cpu().numpy()

        # Calculate MSE per feature (averaged over sequence length)
        mse_per_feature = np.mean((sequence_data - reconstructed) ** 2, axis=0)
        total_anomaly_score = float(np.mean(mse_per_feature))
        
        # Identify primary contributing modality
        max_error_idx = int(np.argmax(mse_per_feature))
        primary_modality = self.feature_names[max_error_idx]

        # Adjust for Cosmos Black Swan context
        if self.cosmos_context == "BLACK_SWAN_CASCADING_FAILURE":
            total_anomaly_score = min(1.0, total_anomaly_score * 1.5)

        return total_anomaly_score, primary_modality

    def process_sensor_stream(self, normalized_scores: Dict[str, float]) -> SitRep:
        self.update_buffer(normalized_scores)
        anomaly_score, primary_modality = self.calculate_anomaly()
        
        if anomaly_score >= self.threshold_critical:
            decision = "CRITICAL_FAILURE"
        elif anomaly_score >= self.threshold_suspicious:
            decision = "ANOMALY_DETECTED"
        else:
            decision = "SAFE"

        return SitRep(
            event_id=str(uuid.uuid4()),
            timestamp=time.time(),
            node_id=self.node_id,
            decision=decision,
            anomaly_score=round(anomaly_score, 4),
            primary_modality=primary_modality,
            confidence=round(1.0 - anomaly_score, 4),
            scores=normalized_scores,
            cosmos_context=self.cosmos_context
        )