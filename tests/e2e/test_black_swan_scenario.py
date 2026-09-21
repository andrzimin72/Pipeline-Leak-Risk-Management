# tests/e2e/test_black_swan_scenario.py
"""
End-to-end scenario test: "Black Swan" cascading failure.
Simulates the full pipeline:
  Sensor Anomaly → Sentinel → Commander → Safety Interlock → Risk Engine → SAP Work Order

Validates that the entire chain reacts correctly to a critical event.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from edge.agents.sentinel_agent import SentinelAgent
from edge.agents.commander_agent import CommanderAgent, SitRep
from edge.agents.operator_agent import OperatorAgent
from cloud.risk.risk_engine import DynamicRiskScoringEngine, SensorMetrics, GISContext
from cloud.planner.mitigation_planner import PrescriptiveMitigationPlanner


class TestBlackSwanScenario:
    """
    Simulates a catastrophic cascading failure at NODE-042
    (High Consequence Area near a river and city).
    """

    @pytest.fixture
    def full_pipeline(self):
        """Sets up the complete multi-agent + enterprise pipeline."""
        sentinel = SentinelAgent(node_id="NODE-042", seq_len=10)
        operator = OperatorAgent(plc_ip="192.168.1.100", shadow_mode=True)
        commander = CommanderAgent(node_id="NODE-042", operator_agent=operator)
        risk_engine = DynamicRiskScoringEngine()
        planner = PrescriptiveMitigationPlanner(
            eam_api_url="https://mock-sap.example.com/api",
            auth_token="test-token",
            auto_approve_critical=True
        )
        return {
            "sentinel": sentinel,
            "commander": commander,
            "operator": operator,
            "risk_engine": risk_engine,
            "planner": planner
        }

    def test_black_swan_triggers_full_chain(self, full_pipeline):
        """
        Given: A Black Swan event with extreme sensor readings at NODE-042 (HCA)
        When: The full pipeline processes the event
        Then: 
          - Sentinel detects CRITICAL_FAILURE
          - Commander proposes valve closure
          - Safety Interlock allows it (pressure within limits)
          - Risk Engine calculates CRITICAL tier
          - Mitigation Planner auto-generates SAP Work Order with Priority 1
        """
        pipeline = full_pipeline

        # 1. Simulate extreme sensor readings (Black Swan)
        black_swan_scores = {
            "acoustic": 0.95, "pressure": 0.98, "coriolis_mass": 0.90,
            "fiber_dts": 0.85, "point_temp": 0.70, "soil_moisture": 0.60,
            "capacitance": 0.50, "vibration": 0.30, "corrosion": 0.80,
            "standard_flow": 0.20, "physics_residual": 0.92
        }

        # 2. Sentinel perceives the anomaly
        sitrep = pipeline["sentinel"].process_sensor_stream(black_swan_scores)
        assert sitrep.decision in ["CRITICAL_FAILURE", "ANOMALY_DETECTED"], \
            f"Sentinel should detect critical anomaly, got {sitrep.decision}"

        # 3. Commander reasons and executes (with safe pressure)
        scada_command = pipeline["commander"].process_sitrep(
            sitrep, current_pressure=950.0, current_temp=25.0
        )
        assert scada_command.safety_override is False, \
            "Safe pressure should NOT trigger safety override"
        assert scada_command.execution_status == "SUCCESS", \
            "Operator should successfully execute command"

        # 4. Risk Engine calculates Dynamic Risk Index
        metrics = SensorMetrics(
            anomaly_score=sitrep.anomaly_score,
            physics_residual=black_swan_scores["physics_residual"],
            corrosion_rate=black_swan_scores["corrosion"],
            vibration_level=black_swan_scores["vibration"],
            cascade_threat=0.0
        )
        context = GISContext(
            population_density_score=0.9,
            environmental_sensitivity=0.95,
            economic_value_score=0.8
        )
        assessment = pipeline["risk_engine"].assess_risk("NODE-042", metrics, context)
        assert assessment.risk_tier == "CRITICAL", \
            f"Expected CRITICAL tier, got {assessment.risk_tier}"
        assert assessment.dynamic_risk_index >= 75

        # 5. Mitigation Planner generates SAP Work Order
        work_order = pipeline["planner"].generate_work_order(
            node_id="NODE-042",
            dri=assessment.dynamic_risk_index,
            risk_tier=assessment.risk_tier,
            mitigation_plan=assessment.mitigation_plan
        )
        assert work_order is not None, "Work order must be generated"
        assert work_order.priority == "1", "CRITICAL risk must be Priority 1"
        assert work_order.status == "APPROVED", "CRITICAL must auto-approve"
        assert work_order.functional_location == "FL-PIPE-SEC4-042"

    def test_unsafe_pressure_triggers_safety_override(self, full_pipeline):
        """
        Given: A Black Swan event with UNSAFE upstream pressure (1250 PSI)
        When: Commander proposes valve closure
        Then: Safety Interlock MUST override and trigger Mechanical ESDV
        """
        pipeline = full_pipeline

        black_swan_scores = {
            "acoustic": 0.95, "pressure": 0.98, "coriolis_mass": 0.90,
            "fiber_dts": 0.85, "point_temp": 0.70, "soil_moisture": 0.60,
            "capacitance": 0.50, "vibration": 0.30, "corrosion": 0.80,
            "standard_flow": 0.20, "physics_residual": 0.92
        }

        sitrep = pipeline["sentinel"].process_sensor_stream(black_swan_scores)

        # UNSAFE pressure: 1250 PSI exceeds MAX_SAFE_PRESSURE_PSI (1200)
        scada_command = pipeline["commander"].process_sitrep(
            sitrep, current_pressure=1250.0, current_temp=25.0
        )

        assert scada_command.safety_override is True, \
            "Unsafe pressure MUST trigger safety override"
        assert scada_command.action == "TRIGGER_MECHANICAL_ESDV", \
            "Override must fallback to Mechanical ESDV"
        assert scada_command.target_device == "MECHANICAL_ESDV_BACKUP"