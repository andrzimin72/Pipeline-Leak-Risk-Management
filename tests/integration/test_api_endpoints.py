# tests/integration/test_api_endpoints.py
"""
Integration tests for the FastAPI Cloud Backend.
Uses FastAPI's TestClient to validate endpoint behavior.
"""

import pytest
import sys
import os
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Patch data directory to use temp location for tests
import tempfile
TEST_DATA_DIR = tempfile.mkdtemp()

# Patch the API's data directory before importing
import api.main as api_main
api_main.ALERTS_LOG_FILE = os.path.join(TEST_DATA_DIR, "alerts.json")
api_main.SCADA_LOG_FILE = os.path.join(TEST_DATA_DIR, "scada_logs.json")
api_main.RISK_LOG_FILE = os.path.join(TEST_DATA_DIR, "risk_assessments.json")

from api.main import app

@pytest.fixture
def client():
    """Provides a FastAPI TestClient."""
    return TestClient(app)

class TestRootEndpoint:
    def test_root_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "online" in data["status"].lower()

class TestAlertsEndpoint:
    def test_safe_alert_returns_nominal(self, client, mock_fusion_payload):
        """SAFE decisions should return NOMINAL compliance status."""
        mock_fusion_payload["decision"] = "SAFE"
        response = client.post("/api/v1/alerts", json=mock_fusion_payload)
        assert response.status_code == 201
        data = response.json()
        assert data["compliance_status"] == "NOMINAL"

    def test_critical_alert_triggers_phmsa(self, client, mock_fusion_payload, mock_nebius_api):
        """CRITICAL decisions should trigger Nemotron PHMSA report."""
        response = client.post("/api/v1/alerts", json=mock_fusion_payload)
        assert response.status_code == 201
        data = response.json()
        assert "MOCK PHMSA REPORT" in data["report_text"]

    def test_invalid_payload_returns_422(self, client):
        """Malformed payload should return 422 Unprocessable Entity."""
        invalid_payload = {"event_id": "test"}  # Missing required fields
        response = client.post("/api/v1/alerts", json=invalid_payload)
        assert response.status_code == 422

class TestSCADAShadowLogEndpoint:
    def test_scada_log_accepted(self, client):
        """Valid SCADA shadow log should return 202 Accepted."""
        scada_payload = {
            "command_id": "cmd-001",
            "timestamp": "2026-09-10T12:00:00Z",
            "action": "CLOSE_UPSTREAM_VALVE",
            "target_device": "ESDV_041",
            "safety_override": False,
            "reasoning": "Validated by Safety Interlock.",
            "execution_status": "SUCCESS"
        }
        response = client.post("/api/v1/scada_shadow_log", json=scada_payload)
        assert response.status_code == 202

class TestRiskNodesEndpoint:
    def test_risk_nodes_returns_list(self, client):
        """Risk nodes endpoint should return a list (empty or populated)."""
        response = client.get("/api/v1/risk/nodes")
        assert response.status_code == 200
        assert isinstance(response.json(), list)