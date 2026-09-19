# edge/agents/commander_agent.py
"""
Nemotron Commander Agent & Deterministic Safety Interlock.
Translates AI SitReps into safe, validated SCADA commands and 
executes them via the Operator Agent (SCADA Translator).
Compliant with IEC 61508 functional safety and IEC 62443 cybersecurity standards.
"""

import time
import json
import uuid
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Tuple, Optional
from datetime import datetime, timezone

# Import the Operator Agent for execution
from edge.agents.operator_agent import OperatorAgent

# Configure logging for audit trails
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [COMMANDER] - %(levelname)s - %(message)s")
logger = logging.getLogger("CommanderAgent")

# ==============================================================================
# 1. Data Structures
# ==============================================================================
@dataclass
class SitRep:
    """Situation Report from the Sentinel (Fusion Engine)."""
    event_id: str
    timestamp: str
    node_id: str
    decision: str
    final_confidence: float
    scores: Dict[str, float]

@dataclass
class SCADACommand:
    """Final validated command sent to the physical PLCs via the Operator Agent."""
    command_id: str
    timestamp: str
    target_device: str
    action: str
    parameters: Dict[str, float]
    safety_override: bool
    llm_proposal: str
    final_reasoning: str
    execution_status: str = "PENDING"

# ==============================================================================
# 2. The Deterministic Safety Interlock (NO AI ALLOWED HERE)
# ==============================================================================
class SafetyInterlock:
    """
    Hard-coded, deterministic rule engine. 
    Compliant with IEC 61508 / IEC 61511 functional safety standards.
    """
    MAX_SAFE_PRESSURE_PSI = 1200.0
    MIN_SAFE_TEMPERATURE_C = -10.0

    def validate_command(self, proposed_action: str, current_pressure: float, current_temp: float) -> Tuple[bool, str]:
        """
        Evaluates the AI's proposed action against hard physics limits.
        Returns (is_safe: bool, override_reason: str)
        """
        if proposed_action == "CLOSE_UPSTREAM_VALVE":
            if current_pressure > self.MAX_SAFE_PRESSURE_PSI:
                return False, f"CRITICAL: Upstream pressure ({current_pressure:.1f} PSI) exceeds safe limit ({self.MAX_SAFE_PRESSURE_PSI} PSI). AI command rejected. Triggering Mechanical ESDV."
        
        if proposed_action == "DEPRESSURIZE_SEGMENT":
            if current_temp < self.MIN_SAFE_TEMPERATURE_C:
                return False, f"CRITICAL: Temperature ({current_temp:.1f}°C) too low for rapid depressurization (Hydrate risk). AI command rejected."

        return True, "Validated by Deterministic Safety Interlock."

# ==============================================================================
# 3. The Nemotron Commander Agent
# ==============================================================================
class CommanderAgent:
    def __init__(self, node_id: str, operator_agent: OperatorAgent):
        self.node_id = node_id
        self.interlock = SafetyInterlock()
        self.operator = operator_agent # Dependency Injection
        
        logger.info(f"Commander Agent initialized for Node {self.node_id}")
        logger.info("Deterministic Safety Interlock armed.")

    def _mock_nemotron_reasoning(self, sitrep: SitRep) -> Dict:
        """
        MOCK: Simulates calling NVIDIA Nemotron NIM via FastAPI.
        In production, this sends the SitRep to the LLM to generate a JSON action plan.
        """
        # Simulating LLM inference latency
        time.sleep(0.2) 
        
        if sitrep.decision == "CRITICAL_LEAK":
            return {
                "proposed_action": "CLOSE_UPSTREAM_VALVE",
                "target_device": "ESDV_041",
                "parameters": {"closure_time_sec": 5.0},
                "llm_reasoning": "High confidence leak detected. Isolating segment to minimize environmental impact."
            }
        elif sitrep.decision == "SUSPICIOUS":
            return {
                "proposed_action": "REDUCE_FLOW_RATE",
                "target_device": "PUMP_STATION_04",
                "parameters": {"flow_reduction_pct": 20.0},
                "llm_reasoning": "Anomaly detected but not critical. Reducing flow to lower stress on pipe while dispatching inspection drone."
            }
        else:
            return {
                "proposed_action": "NO_ACTION",
                "target_device": "NONE",
                "parameters": {},
                "llm_reasoning": "System nominal. No action required."
            }

    def process_sitrep(self, sitrep: SitRep, current_pressure: float, current_temp: float) -> SCADACommand:
        """Main execution loop for the Commander Agent."""
        logger.info(f"Received SitRep: {sitrep.decision} (Confidence: {sitrep.final_confidence:.2f})")
        
        # 1. Get AI Action Plan from Nemotron
        ai_plan = self._mock_nemotron_reasoning(sitrep)
        logger.info(f"Nemotron proposed: {ai_plan['proposed_action']} -> {ai_plan['llm_reasoning']}")
        
        # 2. Pass through Deterministic Safety Interlock
        is_safe, interlock_message = self.interlock.validate_command(
            ai_plan["proposed_action"], current_pressure, current_temp
        )
        
        safety_override = False
        final_action = ai_plan["proposed_action"]
        final_target = ai_plan["target_device"]
        
        if not is_safe:
            logger.critical(f"SAFETY INTERLOCK TRIGGERED: {interlock_message}")
            safety_override = True
            final_action = "TRIGGER_MECHANICAL_ESDV" # Hard-coded deterministic fallback
            final_target = "MECHANICAL_ESDV_BACKUP"
            interlock_message = f"OVERRIDE: {interlock_message}"

        # 3. Construct Final SCADA Command
        command = SCADACommand(
            command_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            target_device=final_target,
            action=final_action,
            parameters=ai_plan["parameters"],
            safety_override=safety_override,
            llm_proposal=ai_plan["llm_reasoning"],
            final_reasoning=interlock_message
        )

        # 4. Execute via Operator Agent (SCADA Translator)
        logger.info(f"Dispatching command to Operator Agent: {command.action} -> {command.target_device}")
        success = self.operator.execute_command(command)
        
        command.execution_status = "SUCCESS" if success else "FAILED"
        logger.info(f"Command execution status: {command.execution_status}")
        
        return command

# ==============================================================================
# 4. Execution & Stress Testing
# ==============================================================================
def run_commander_stress_test():
    logger.info("Starting Commander Agent Stress Test Sequence...\n")
    
    # Initialize Operator Agent in Shadow Mode for safe testing
    operator = OperatorAgent(plc_ip="192.168.1.100", shadow_mode=True)
    agent = CommanderAgent(node_id="JETSON-NODE-042", operator_agent=operator)
    
    # Scenario 1: Normal Suspicious Event (Safe)
    logger.info("--- SCENARIO 1: Minor Anomaly ---")
    sitrep_1 = SitRep(
        event_id="evt_001", timestamp=datetime.now(timezone.utc).isoformat(),
        node_id="JETSON-NODE-042", decision="SUSPICIOUS", final_confidence=0.45, scores={}
    )
    agent.process_sitrep(sitrep_1, current_pressure=980.0, current_temp=25.0)

    # Scenario 2: Critical Leak (Safe to close valve)
    logger.info("\n--- SCENARIO 2: Critical Leak (Safe Conditions) ---")
    sitrep_2 = SitRep(
        event_id="evt_002", timestamp=datetime.now(timezone.utc).isoformat(),
        node_id="JETSON-NODE-042", decision="CRITICAL_LEAK", final_confidence=0.95, scores={}
    )
    agent.process_sitrep(sitrep_2, current_pressure=990.0, current_temp=25.0)

    # Scenario 3: Critical Leak (UNSAFE - Interlock MUST trigger!)
    logger.info("\n--- SCENARIO 3: Critical Leak (UNSAFE Pressure - Interlock Override) ---")
    sitrep_3 = SitRep(
        event_id="evt_003", timestamp=datetime.now(timezone.utc).isoformat(),
        node_id="JETSON-NODE-042", decision="CRITICAL_LEAK", final_confidence=0.95, scores={}
    )
    agent.process_sitrep(sitrep_3, current_pressure=1250.0, current_temp=25.0)

if __name__ == "__main__":
    run_commander_stress_test()