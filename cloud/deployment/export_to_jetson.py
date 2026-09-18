# cloud/deployment/export_to_jetson.py
"""
Exports the trained PyTorch Sentinel Transformer to ONNX and compiles it 
into a TensorRT Engine optimized for NVIDIA Jetson Orin.
"""

import os
import sys
import json
import torch
import numpy as np

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from edge.agents.sentinel_agent import TimeSeriesTransformerAE

# ==============================================================================
# 1. Configuration & Loading
# ==============================================================================
ARTIFACTS_DIR = "cloud/training/artifacts"
OUTPUT_DIR = "cloud/deployment/jetson_artifacts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_trained_model():
    with open(os.path.join(ARTIFACTS_DIR, "model_metadata.json"), "r") as f:
        metadata = json.load(f)
        
    model = TimeSeriesTransformerAE(
        num_features=metadata["num_features"],
        d_model=metadata["d_model"],
        n_heads=metadata["n_heads"],
        num_layers=metadata["num_layers"]
    )
    
    model.load_state_dict(torch.load(os.path.join(ARTIFACTS_DIR, "sentinel_transformer.pth"), map_location="cpu"))
    model.eval()
    print("✅ Loaded trained PyTorch model.")
    return model, metadata

# ==============================================================================
# 2. Export to ONNX
# ==============================================================================
def export_to_onnx(model, metadata):
    onnx_path = os.path.join(OUTPUT_DIR, "sentinel_transformer.onnx")
    
    # Dummy input matching the expected shape: (batch_size, seq_len, num_features)
    dummy_input = torch.randn(1, metadata["seq_len"], metadata["num_features"])
    
    print("🔄 Exporting to ONNX...")
    torch.onnx.export(
        model,
        dummy_input,
        onnx_path,
        export_params=True,
        opset_version=13, # TensorRT prefers opset 13+
        do_constant_folding=True,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}
    )
    print(f"💾 ONNX model saved to {onnx_path}")
    return onnx_path

# ==============================================================================
# 3. Compile to TensorRT Engine (Jetson Orin Optimized)
# ==============================================================================
def compile_to_tensorrt(onnx_path):
    try:
        import tensorrt as trt
    except ImportError:
        print("❌ Error: TensorRT is not installed. Please install tensorrt on your GPU machine.")
        print("   Alternatively, use the command line tool: trtexec --onnx=... --fp16 --saveEngine=...")
        return None

    engine_path = os.path.join(OUTPUT_DIR, "sentinel_transformer.engine")
    TRT_LOGGER = trt.Logger(trt.Logger.WARNING)

    print("🚀 Compiling TensorRT Engine (FP16 Optimization for Jetson Orin)...")
    
    builder = trt.Builder(TRT_LOGGER)
    network = builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH))
    parser = trt.OnnxParser(network, TRT_LOGGER)

    # Parse ONNX model
    with open(onnx_path, 'rb') as model_file:
        if not parser.parse(model_file.read()):
            for error in range(parser.num_errors):
                print(f"TRT Parse Error: {parser.get_error(error)}")
            return None

    # Configure Builder for Jetson Orin
    config = builder.create_builder_config()
    config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, 1 << 28) # 256MB workspace
    config.set_flag(trt.BuilderFlag.FP16) # CRITICAL: Enables FP16 for massive speedup on Jetson

    # Build Engine
    print("   (This may take a few minutes depending on the GPU)...")
    engine_bytes = builder.build_serialized_network(network, config)
    
    with open(engine_path, 'wb') as f:
        f.write(engine_bytes)
        
    print(f" TensorRT Engine saved to {engine_path}")
    print("✅ Ready for deployment to NVIDIA Jetson Orin!")
    return engine_path

# ==============================================================================
# Main Execution
# ==============================================================================
if __name__ == "__main__":
    model, metadata = load_trained_model()
    onnx_file = export_to_onnx(model, metadata)
    if onnx_file:
        compile_to_tensorrt(onnx_file)