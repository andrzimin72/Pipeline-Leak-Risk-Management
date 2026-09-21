# tests/unit/test_sentinel_agent.py
"""
Unit tests for Agent 1: The Sentinel (Perception & Anomaly Detection).
Validates the PyTorch Time-Series Transformer Autoencoder behavior,
buffer management, Cosmos context injection, and threshold-based decisions.
"""

import pytest
import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from edge.agents.sentinel_agent import SentinelAgent, TimeSeriesTransformerAE


@pytest.fixture
def sentinel():
    """Returns a fresh SentinelAgent instance for testing."""
    return SentinelAgent(node_id="TEST-NODE-001", seq_len=5)


@pytest.fixture
def normal_scores():
    """Returns normalized scores representing normal pipeline operations."""
    return {k: np.random.uniform(0.02, 0.08) for k in [
        "acoustic", "pressure", "coriolis_mass", "fiber_dts", "point_temp",
        "soil_moisture", "capacitance", "vibration", "corrosion", 
        "standard_flow", "physics_residual"
    ]}


@pytest.fixture
def anomalous_scores():
    """Returns normalized scores representing a multimodal anomaly."""
    scores = {k: 0.05 for k in [
        "acoustic", "pressure", "coriolis_mass", "fiber_dts", "point_temp",
        "soil_moisture", "capacitance", "vibration", "corrosion", 
        "standard_flow", "physics_residual"
    ]}
    # Inject anomaly in pressure, acoustic, and physics_residual
    scores["pressure"] = 0.92
    scores["acoustic"] = 0.88
    scores["physics_residual"] = 0.85
    return scores


class TestTransformerArchitecture:
    """Tests for the underlying PyTorch Transformer Autoencoder."""

    def test_model_initialization(self):
        """Transformer should initialize with correct dimensions."""
        model = TimeSeriesTransformerAE(num_features=11, d_model=32, n_heads=2, num_layers=2)
        assert model.input_projection.in_features == 11
        assert model.input_projection.out_features == 32

    def test_forward_pass_shape(self):
        """Forward pass should preserve input shape (batch, seq_len, features)."""
        model = TimeSeriesTransformerAE(num_features=11)
        import torch
        x = torch.randn(2, 10, 11)  # batch=2, seq_len=10, features=11
        output = model(x)
        assert output.shape == x.shape, f"Expected shape {x.shape}, got {output.shape}"

    def test_reconstruction_quality_on_normal_data(self):
        """Model should reconstruct normal correlated data with low error."""
        import torch
        model = TimeSeriesTransformerAE(num_features=11)
        model.eval()
        
        # Generate correlated normal data (all features similar)
        normal_data = torch.full((1, 10, 11), 0.1)
        with torch.no_grad():
            reconstructed = model(normal_data)
        
        # Reconstruction should be close to input for uniform data
        mse = torch.mean((normal_data - reconstructed) ** 2).item()
        assert mse < 1.0, f"Reconstruction error too high for normal data: {mse}"


class TestBufferManagement:
    """Tests for the sliding window buffer."""

    def test_buffer_starts_empty(self, sentinel):
        """Buffer should be empty on initialization."""
        assert len(sentinel.sequence_buffer) == 0

    def test_buffer_fills_correctly(self, sentinel, normal_scores):
        """Buffer should fill up to seq_len with incoming data."""
        for _ in range(5):
            sentinel.update_buffer(normal_scores)
        assert len(sentinel.sequence_buffer) == 5

    def test_buffer_maintains_max_size(self, sentinel, normal_scores):
        """Buffer should never exceed seq_len (sliding window behavior)."""
        for _ in range(20):
            sentinel.update_buffer(normal_scores)
        assert len(sentinel.sequence_buffer) == sentinel.seq_len

    def test_buffer_drops_oldest_data(self, sentinel):
        """Buffer should drop oldest entries when full (FIFO behavior)."""
        for i in range(7):  # seq_len=5, so 2 should be dropped
            scores = {k: float(i) for k in sentinel.feature_names}
            sentinel.update_buffer(scores)
        
        # First entry should be 2.0 (0 and 1 were dropped)
        first_entry = list(sentinel.sequence_buffer)[0]
        assert first_entry[0] == 2.0, "Oldest entries should be dropped"


class TestAnomalyDetection:
    """Tests for anomaly score calculation and decision logic."""

    def test_returns_waiting_when_buffer_empty(self, sentinel):
        """Should return 0.0 anomaly score when buffer is not full."""
        score, modality = sentinel.calculate_anomaly()
        assert score == 0.0
        assert modality == "WAITING_FOR_DATA"

    def test_low_anomaly_for_normal_data(self, sentinel, normal_scores):
        """Normal data should produce low anomaly scores."""
        for _ in range(sentinel.seq_len):
            sentinel.update_buffer(normal_scores)
        score, modality = sentinel.calculate_anomaly()
        assert score < 0.5, f"Normal data should have low anomaly score, got {score}"

    def test_high_anomaly_for_uncorrelated_spike(self, sentinel, anomalous_scores):
        """Uncorrelated multimodal spike should produce high anomaly score."""
        # Fill buffer with normal data first
        normal = {k: 0.05 for k in sentinel.feature_names}
        for _ in range(sentinel.seq_len - 1):
            sentinel.update_buffer(normal)
        
        # Inject anomaly
        sentinel.update_buffer(anomalous_scores)
        score, modality = sentinel.calculate_anomaly()
        
        assert score > 0.1, f"Anomalous data should have higher anomaly score, got {score}"

    def test_primary_modality_identification(self, sentinel):
        """Should correctly identify the sensor with highest reconstruction error."""
        # Create data where pressure is wildly different from others
        scores = {k: 0.1 for k in sentinel.feature_names}
        scores["pressure"] = 0.95  # Massive outlier
        
        for _ in range(sentinel.seq_len):
            sentinel.update_buffer(scores)
        
        _, primary_modality = sentinel.calculate_anomaly()
        # Pressure should be identified as the primary contributor
        assert primary_modality == "pressure", \
            f"Expected 'pressure' as primary modality, got '{primary_modality}'"


class TestCosmosContextInjection:
    """Tests for synthetic context from Cosmos Black Swan Generator."""

    def test_default_context_is_normal(self, sentinel):
        """Default context should be NORMAL."""
        assert sentinel.cosmos_context == "NORMAL"

    def test_context_injection_updates_state(self, sentinel):
        """inject_cosmos_context should update internal state."""
        sentinel.inject_cosmos_context("BLACK_SWAN_CASCADING_FAILURE")
        assert sentinel.cosmos_context == "BLACK_SWAN_CASCADING_FAILURE"

    def test_black_swan_context_amplifies_anomaly(self, sentinel, anomalous_scores):
        """BLACK_SWAN context should amplify anomaly score by 1.5x."""
        # Fill buffer with anomalous data
        for _ in range(sentinel.seq_len):
            sentinel.update_buffer(anomalous_scores)
        
        # Get baseline score
        baseline_score, _ = sentinel.calculate_anomaly()
        
        # Inject Black Swan context and recalculate
        sentinel.inject_cosmos_context("BLACK_SWAN_CASCADING_FAILURE")
        amplified_score, _ = sentinel.calculate_anomaly()
        
        # Amplified score should be higher (up to 1.5x, capped at 1.0)
        assert amplified_score >= baseline_score, \
            "Black Swan context should amplify anomaly score"


class TestDecisionLogic:
    """Tests for threshold-based decision assignment."""

    def test_safe_decision_for_low_anomaly(self, sentinel, normal_scores):
        """Low anomaly score should produce SAFE decision."""
        for _ in range(sentinel.seq_len):
            sentinel.update_buffer(normal_scores)
        sitrep = sentinel.process_sensor_stream(normal_scores)
        assert sitrep.decision == "SAFE"

    def test_sitrep_structure(self, sentinel, normal_scores):
        """SitRep should contain all required fields."""
        for _ in range(sentinel.seq_len):
            sentinel.update_buffer(normal_scores)
        sitrep = sentinel.process_sensor_stream(normal_scores)
        
        assert sitrep.event_id is not None
        assert sitrep.timestamp is not None
        assert sitrep.node_id == "TEST-NODE-001"
        assert sitrep.decision in ["SAFE", "ANOMALY_DETECTED", "CRITICAL_FAILURE"]
        assert 0.0 <= sitrep.anomaly_score <= 1.0
        assert sitrep.primary_modality in sentinel.feature_names
        assert 0.0 <= sitrep.confidence <= 1.0
        assert isinstance(sitrep.scores, dict)
        assert len(sitrep.scores) == 11

    def test_confidence_is_inverse_of_anomaly(self, sentinel, normal_scores):
        """Confidence should be approximately 1 - anomaly_score."""
        for _ in range(sentinel.seq_len):
            sentinel.update_buffer(normal_scores)
        sitrep = sentinel.process_sensor_stream(normal_scores)
        
        expected_confidence = round(1.0 - sitrep.anomaly_score, 4)
        assert sitrep.confidence == expected_confidence, \
            f"Confidence should be inverse of anomaly: expected {expected_confidence}, got {sitrep.confidence}"