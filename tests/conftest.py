# tests/conftest.py
"""
Shared pytest fixtures for the Pipeline Leak Risk Management Physical AI Platform test suite.
"""

import os
import sys
import json
import pytest
import tempfile
import shutil
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

# ==============================================================================
# 1. Temporary Data Directory Fixture
# ==============================================================================
@pytest.fixture
def temp_data_dir():
    """Creates a temporary directory for test data files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

# ==============================================================================
# 2. Mock Sensor Data Fixtures
# ==============================================================================
@pytest.fixture
def normal_sensor_metrics():
    """Returns metrics representing normal pipeline operations."""
    from cloud.risk.risk_engine import SensorMetrics
    return SensorMetrics(
        anomaly_score=0.05,
        physics_residual=0.02,
        corrosion_rate=0.1,
        vibration_level=0.1,
        cascade_threat=0.0
    )

@pytest.fixture
def critical_sensor_metrics():
    """Returns metrics representing a critical pipeline failure."""
    from cloud.risk.risk_engine import SensorMetrics
    return SensorMetrics(
        anomaly_score=0.92,
        physics_residual=0.85,
        corrosion_rate=0.7,
        vibration_level=0.8,
        cascade_threat=0.95
    )

@pytest.fixture
def high_consequence_gis_context():
    """Returns GIS context for a High Consequence Area (HCA)."""
    from cloud.risk.risk_engine import GISContext
    return GISContext(
        population_density_score=0.9,
        environmental_sensitivity=0.95,
        economic_value_score=0.8
    )

@pytest.fixture
def low_consequence_gis_context():
    """Returns GIS context for a remote, low-risk area."""
    from cloud.risk.risk_engine import GISContext
    return GISContext(
        population_density_score=0.1,
        environmental_sensitivity=0.2,
        economic_value_score=0.5
    )

# ==============================================================================
# 3. Mock Fusion Payload Fixture
# ==============================================================================
@pytest.fixture
def mock_fusion_payload():
    """Returns a mock 11-modal fusion payload for API testing."""
    return {
        "event_id": "test-event-001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "node_id": "NODE-042",
        "scores": {
            "acoustic": 0.85, "pressure": 0.90, "coriolis_mass": 0.75,
            "fiber_dts": 0.60, "point_temp": 0.50, "soil_moisture": 0.40,
            "capacitance": 0.30, "vibration": 0.20, "corrosion": 0.65,
            "standard_flow": 0.10, "physics_residual": 0.88
        },
        "final_confidence": 0.91,
        "decision": "CRITICAL_FAILURE",
        "action_required": "EXECUTE_SCADA"
    }

# ==============================================================================
# 4. Mock Enterprise API Fixtures
# ==============================================================================
@pytest.fixture
def mock_sap_api():
    """Mocks the SAP/Maximo Enterprise Asset Management API."""
    with patch('cloud.planner.mitigation_planner.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "status": "success",
            "sap_notification_id": "10009999",
            "sap_work_order_id": "40009999",
            "message": "Notification created and converted to Work Order."
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        yield mock_post

@pytest.fixture
def mock_nebius_api():
    """Mocks the Nebius Nemotron LLM API."""
    with patch('api.main.httpx.AsyncClient') as mock_client:
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "MOCK PHMSA REPORT: Critical leak detected at NODE-042."}}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_instance.post.return_value = mock_response
        mock_instance.__aenter__.return_value = mock_instance
        mock_client.return_value = mock_instance
        yield mock_client
