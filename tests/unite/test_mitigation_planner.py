# tests/unit/test_mitigation_planner.py
"""
Unit tests for the Prescriptive Mitigation Planner.
Validates AI → SAP/Maximo work order translation.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from cloud.planner.mitigation_planner import PrescriptiveMitigationPlanner

@pytest.fixture
def planner():
    return PrescriptiveMitigationPlanner(
        eam_api_url="https://mock-sap.example.com/api",
        auth_token="test-token",
        auto_approve_critical=True
    )

class TestTaskListMapping:
    """Tests for AI text → EAM Task List translation."""

    def test_drone_inspection_mapping(self, planner):
        """Drone recommendation should map to TL-DRONE-02."""
        task = planner._map_ai_to_eam(["SHORT-TERM: Dispatch drone for inspection."])
        assert task == "TL-DRONE-02"

    def test_smart_pig_mapping(self, planner):
        """Smart Pig recommendation should map to TL-ILI-03."""
        task = planner._map_ai_to_eam(["Conduct In-Line Inspection (Smart Pig)."])
        assert task == "TL-ILI-03"

    def test_isolation_mapping(self, planner):
        """Isolation recommendation should map to TL-EMRG-05."""
        task = planner._map_ai_to_eam(["IMMEDIATE: Trigger autonomous SCADA isolation."])
        assert task == "TL-EMRG-05"

    def test_fallback_to_general(self, planner):
        """Unknown recommendations should fall back to TL-GEN-00."""
        task = planner._map_ai_to_eam(["Do something completely new."])
        assert task == "TL-GEN-00"

class TestPriorityMapping:
    """Tests for DRI → SAP Priority translation."""

    def test_critical_dri_maps_to_priority_1(self, planner):
        """DRI >= 75 must map to Priority 1 (Emergency)."""
        assert planner._calculate_eam_priority(82.0, "CRITICAL") == "1"

    def test_high_dri_maps_to_priority_2(self, planner):
        """DRI 50-74 must map to Priority 2 (High)."""
        assert planner._calculate_eam_priority(60.0, "HIGH") == "2"

    def test_medium_dri_maps_to_priority_3(self, planner):
        """DRI 25-49 must map to Priority 3 (Medium)."""
        assert planner._calculate_eam_priority(35.0, "MEDIUM") == "3"

    def test_low_dri_maps_to_priority_4(self, planner):
        """DRI < 25 must map to Priority 4 (Low)."""
        assert planner._calculate_eam_priority(15.0, "LOW") == "4"

class TestWorkOrderGeneration:
    """Tests for end-to-end work order generation."""

    def test_critical_auto_approves(self, planner):
        """CRITICAL risk tier must auto-approve the work order."""
        wo = planner.generate_work_order(
            node_id="NODE-042",
            dri=85.0,
            risk_tier="CRITICAL",
            mitigation_plan=["IMMEDIATE: Trigger isolation."]
        )
        assert wo is not None
        assert wo.status == "APPROVED"
        assert wo.priority == "1"

    def test_medium_requires_approval(self, planner):
        """MEDIUM risk tier must require human planner approval."""
        wo = planner.generate_work_order(
            node_id="NODE-045",
            dri=35.0,
            risk_tier="MEDIUM",
            mitigation_plan=["SHORT-TERM: Increase polling rate."]
        )
        assert wo is not None
        assert wo.status == "PENDING_PLANNER_APPROVAL"

    def test_unknown_node_returns_none(self, planner):
        """Unknown node_id should return None (no asset mapping)."""
        wo = planner.generate_work_order(
            node_id="NODE-UNKNOWN",
            dri=50.0,
            risk_tier="HIGH",
            mitigation_plan=["Inspect."]
        )
        assert wo is None