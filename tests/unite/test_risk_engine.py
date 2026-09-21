# tests/unit/test_risk_engine.py
"""
Unit tests for the Dynamic Risk Scoring Engine.
Validates Probability of Failure (PoF), Consequence of Failure (CoF),
and Dynamic Risk Index (DRI) calculations per API 581 standards.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from cloud.risk.risk_engine import DynamicRiskScoringEngine

@pytest.fixture
def engine():
    return DynamicRiskScoringEngine()

class TestProbabilityOfFailure:
    """Tests for the PoF calculation."""

    def test_normal_operations_low_pof(self, engine, normal_sensor_metrics):
        """Normal operations should produce a low PoF (< 25)."""
        pof = engine.calculate_pof(normal_sensor_metrics, "NODE-042")
        assert 0 <= pof < 25, f"Expected low PoF, got {pof}"

    def test_critical_anomaly_high_pof(self, engine, critical_sensor_metrics):
        """Critical anomalies should produce a high PoF (> 75)."""
        pof = engine.calculate_pof(critical_sensor_metrics, "NODE-042")
        assert pof > 75, f"Expected high PoF, got {pof}"

    def test_pof_bounded_0_to_100(self, engine, critical_sensor_metrics):
        """PoF must never exceed 100 or drop below 0."""
        pof = engine.calculate_pof(critical_sensor_metrics, "NODE-042")
        assert 0 <= pof <= 100, f"PoF out of bounds: {pof}"

    def test_degradation_index_accumulates(self, engine, critical_sensor_metrics):
        """Repeated high corrosion should increase the degradation index over time."""
        for _ in range(10):
            engine.calculate_pof(critical_sensor_metrics, "NODE-042")
        final_degradation = engine.historical_degradation.get("NODE-042", 0)
        assert final_degradation > 0.3, "Degradation index should accumulate"

class TestConsequenceOfFailure:
    """Tests for the CoF calculation."""

    def test_high_consequence_area(self, engine, high_consequence_gis_context):
        """HCA should produce high CoF (> 75)."""
        cof = engine.calculate_cof(high_consequence_gis_context)
        assert cof > 75, f"Expected high CoF for HCA, got {cof}"

    def test_remote_area_low_cof(self, engine, low_consequence_gis_context):
        """Remote area should produce low CoF (< 40)."""
        cof = engine.calculate_cof(low_consequence_gis_context)
        assert cof < 40, f"Expected low CoF for remote area, got {cof}"

class TestDynamicRiskIndex:
    """Tests for the final DRI calculation and tier assignment."""

    def test_critical_tier_assignment(self, engine, critical_sensor_metrics, high_consequence_gis_context):
        """Critical metrics + HCA should produce CRITICAL tier."""
        assessment = engine.assess_risk("NODE-042", critical_sensor_metrics, high_consequence_gis_context)
        assert assessment.risk_tier == "CRITICAL", f"Expected CRITICAL, got {assessment.risk_tier}"
        assert assessment.dynamic_risk_index >= 75

    def test_low_tier_assignment(self, engine, normal_sensor_metrics, low_consequence_gis_context):
        """Normal metrics + remote area should produce LOW tier."""
        assessment = engine.assess_risk("NODE-045", normal_sensor_metrics, low_consequence_gis_context)
        assert assessment.risk_tier == "LOW", f"Expected LOW, got {assessment.risk_tier}"
        assert assessment.dynamic_risk_index < 25

    def test_mitigation_plan_generated_for_critical(self, engine, critical_sensor_metrics, high_consequence_gis_context):
        """CRITICAL tier must generate an IMMEDIATE mitigation action."""
        assessment = engine.assess_risk("NODE-042", critical_sensor_metrics, high_consequence_gis_context)
        assert any("IMMEDIATE" in action for action in assessment.mitigation_plan), \
            "CRITICAL tier must include IMMEDIATE actions"