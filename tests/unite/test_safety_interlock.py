# tests/unit/test_safety_interlock.py
"""
Unit tests for the Deterministic Safety Interlock.
Validates IEC 61508 compliance: AI commands must be rejected when
physical conditions exceed safe operating limits.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from edge.agents.commander_agent import SafetyInterlock

@pytest.fixture
def interlock():
    return SafetyInterlock()

class TestSafetyInterlock:
    """Tests for the hard-coded safety rules."""

    def test_valve_closure_safe_pressure(self, interlock):
        """Valve closure should be allowed under safe pressure."""
        is_safe, reason = interlock.validate_command("CLOSE_UPSTREAM_VALVE", 900.0, 25.0)
        assert is_safe is True, "Safe pressure should allow valve closure"

    def test_valve_closure_unsafe_pressure_rejected(self, interlock):
        """Valve closure MUST be rejected when pressure exceeds MAX_SAFE_PRESSURE_PSI."""
        is_safe, reason = interlock.validate_command("CLOSE_UPSTREAM_VALVE", 1250.0, 25.0)
        assert is_safe is False, "Unsafe pressure MUST trigger interlock"
        assert "CRITICAL" in reason, "Rejection reason must be marked CRITICAL"
        assert "Mechanical ESDV" in reason, "Must fallback to Mechanical ESDV"

    def test_depressurization_safe_temperature(self, interlock):
        """Depressurization should be allowed at safe temperatures."""
        is_safe, reason = interlock.validate_command("DEPRESSURIZE_SEGMENT", 900.0, 25.0)
        assert is_safe is True, "Safe temperature should allow depressurization"

    def test_depressurization_freezing_rejected(self, interlock):
        """Depressurization MUST be rejected below MIN_SAFE_TEMPERATURE_C (hydrate risk)."""
        is_safe, reason = interlock.validate_command("DEPRESSURIZE_SEGMENT", 900.0, -15.0)
        assert is_safe is False, "Freezing temp MUST trigger interlock"
        assert "Hydrate" in reason, "Rejection must cite hydrate risk"

    def test_unknown_action_passes_interlock(self, interlock):
        """Unknown actions should pass through (no specific rule to violate)."""
        is_safe, reason = interlock.validate_command("UNKNOWN_ACTION", 900.0, 25.0)
        assert is_safe is True, "Unknown actions should not be blocked by interlock"

    def test_boundary_pressure_exactly_at_limit(self, interlock):
        """Pressure exactly at MAX_SAFE_PRESSURE_PSI should be allowed (not exceeded)."""
        is_safe, reason = interlock.validate_command("CLOSE_UPSTREAM_VALVE", 1200.0, 25.0)
        assert is_safe is True, "Pressure at exact limit should be allowed"