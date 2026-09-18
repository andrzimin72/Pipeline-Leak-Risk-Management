# cloud/risk/risk_engine.py
"""
Dynamic Risk Scoring Engine.
Calculates real-time Probability of Failure (PoF) and Consequence of Failure (CoF)
to generate a Dynamic Risk Index (DRI) for pipeline segments.
Aligned with API 581 and ASME B31.8S Risk-Based Inspection (RBI) standards.
"""

import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [RISK_ENGINE] - %(levelname)s - %(message)s")
logger = logging.getLogger("RiskEngine")

# ==============================================================================
# 1. Data Structures
# ==============================================================================
@dataclass
class SensorMetrics:
    """Real-time AI metrics from the Edge Swarm."""
    anomaly_score: float          # 0.0 to 1.0 (from Sentinel Transformer)
    physics_residual: float       # 0.0 to 1.0 (from PhysicsNeMo)
    corrosion_rate: float         # 0.0 to 1.0 (normalized)
    vibration_level: float        # 0.0 to 1.0 (normalized)
    cascade_threat: float         # 0.0 to 1.0 (from Swarm GNN)

@dataclass
class GISContext:
    """Static geographic and operational context for the pipeline segment."""
    population_density_score: float  # 0.0 to 1.0 (1.0 = dense urban/HCA)
    environmental_sensitivity: float # 0.0 to 1.0 (1.0 = river/wetland)
    economic_value_score: float      # 0.0 to 1.0 (1.0 = critical trunkline)

@dataclass
class RiskAssessment:
    """The final output of the Risk Engine."""
    timestamp: float
    node_id: str
    pof_score: float
    cof_score: float
    dynamic_risk_index: float
    risk_tier: str
    mitigation_plan: List[str]

# ==============================================================================
# 2. The Dynamic Risk Scoring Engine
# ==============================================================================
class DynamicRiskScoringEngine:
    def __init__(self):
        # Weights for Probability of Failure (PoF) - Must sum to 1.0
        self.pof_weights = {
            "anomaly": 0.25,
            "physics": 0.25,
            "degradation": 0.20,
            "cascade": 0.30  # High weight for swarm intelligence
        }
        
        # Weights for Consequence of Failure (CoF) - Must sum to 1.0
        self.cof_weights = {
            "environmental": 0.40,
            "human": 0.40,
            "economic": 0.20
        }
        
        # Historical degradation buffer (simulated moving average)
        self.historical_degradation = {}

        logger.info("Dynamic Risk Scoring Engine initialized.")

    def _calculate_degradation_index(self, node_id: str, corrosion: float, vibration: float) -> float:
        """
        Calculates a time-decayed moving average of physical degradation.
        A sudden spike is less risky than a 30-day trend of rising corrosion.
        """
        current_degradation = (corrosion * 0.7) + (vibration * 0.3)
        
        if node_id not in self.historical_degradation:
            self.historical_degradation[node_id] = current_degradation
        else:
            # Exponential moving average (EMA) with alpha = 0.1
            prev = self.historical_degradation[node_id]
            self.historical_degradation[node_id] = (0.1 * current_degradation) + (0.9 * prev)
            
        return self.historical_degradation[node_id]

    def calculate_pof(self, metrics: SensorMetrics, node_id: str) -> float:
        """Calculates the Probability of Failure (0 to 100)."""
        degradation_idx = self._calculate_degradation_index(node_id, metrics.corrosion_rate, metrics.vibration_level)
        
        pof = (
            (self.pof_weights["anomaly"] * (metrics.anomaly_score * 100)) +
            (self.pof_weights["physics"] * (metrics.physics_residual * 100)) +
            (self.pof_weights["degradation"] * (degradation_idx * 100)) +
            (self.pof_weights["cascade"] * (metrics.cascade_threat * 100))
        )
        return min(100.0, max(0.0, pof))

    def calculate_cof(self, context: GISContext) -> float:
        """Calculates the Consequence of Failure (0 to 100)."""
        cof = (
            (self.cof_weights["environmental"] * (context.environmental_sensitivity * 100)) +
            (self.cof_weights["human"] * (context.population_density_score * 100)) +
            (self.cof_weights["economic"] * (context.economic_value_score * 100))
        )
        return min(100.0, max(0.0, cof))

    def _determine_risk_tier_and_actions(self, dri: float) -> tuple:
        """Maps the Dynamic Risk Index to a tier and prescriptive mitigation plan."""
        if dri >= 75:
            tier = "CRITICAL"
            actions = [
                "IMMEDIATE: Trigger autonomous SCADA isolation (ESDV).",
                "IMMEDIATE: Dispatch emergency response team.",
                "SHORT-TERM: Conduct emergency In-Line Inspection (Smart Pig).",
                "LONG-TERM: Schedule immediate pipe replacement."
            ]
        elif dri >= 50:
            tier = "HIGH"
            actions = [
                "IMMEDIATE: Reduce flow rate by 20% to lower pipe stress.",
                "SHORT-TERM: Dispatch drone for targeted visual/thermal inspection.",
                "LONG-TERM: Schedule maintenance crew for non-destructive testing (NDT)."
            ]
        elif dri >= 25:
            tier = "MEDIUM"
            actions = [
                "SHORT-TERM: Increase sensor polling rate to 1Hz.",
                "LONG-TERM: Add to next quarterly Risk-Based Inspection (RBI) schedule."
            ]
        else:
            tier = "LOW"
            actions = ["CONTINUE: Standard autonomous monitoring protocols."]
            
        return tier, actions

    def assess_risk(self, node_id: str, metrics: SensorMetrics, context: GISContext) -> RiskAssessment:
        """Main execution method for the Risk Engine."""
        pof = self.calculate_pof(metrics, node_id)
        cof = self.calculate_cof(context)
        
        # Dynamic Risk Index (0 to 10,000, normalized to 0-100 for simplicity)
        # Standard formula: RI = PoF * CoF. We divide by 100 to keep it on a 0-100 scale.
        dri = (pof * cof) / 100.0 
        
        tier, actions = self._determine_risk_tier_and_actions(dri)
        
        if tier in ["CRITICAL", "HIGH"]:
            logger.warning(f"Node {node_id} Risk Tier: {tier} | DRI: {dri:.2f} | PoF: {pof:.1f} | CoF: {cof:.1f}")

        return RiskAssessment(
            timestamp=time.time(),
            node_id=node_id,
            pof_score=round(pof, 2),
            cof_score=round(cof, 2),
            dynamic_risk_index=round(dri, 2),
            risk_tier=tier,
            mitigation_plan=actions
        )

# ==============================================================================
# 3. Execution & Testing
# ==============================================================================
if __name__ == "__main__":
    engine = DynamicRiskScoringEngine()
    
    # Scenario 1: Low Risk (Normal operations in a remote desert)
    logger.info("--- SCENARIO 1: Low Risk ---")
    metrics_1 = SensorMetrics(anomaly_score=0.05, physics_residual=0.02, corrosion_rate=0.1, vibration_level=0.1, cascade_threat=0.0)
    context_1 = GISContext(population_density_score=0.1, environmental_sensitivity=0.2, economic_value_score=0.5)
    assessment_1 = engine.assess_risk("NODE-045", metrics_1, context_1)
    logger.info(f"Result: {assessment_1.risk_tier} (DRI: {assessment_1.dynamic_risk_index})")

    # Scenario 2: Critical Risk (High anomaly near a river and city)
    logger.info("\n--- SCENARIO 2: Critical Risk ---")
    metrics_2 = SensorMetrics(anomaly_score=0.85, physics_residual=0.70, corrosion_rate=0.6, vibration_level=0.8, cascade_threat=0.9)
    context_2 = GISContext(population_density_score=0.9, environmental_sensitivity=0.95, economic_value_score=0.8)
    assessment_2 = engine.assess_risk("NODE-042", metrics_2, context_2)
    logger.info(f"Result: {assessment_2.risk_tier} (DRI: {assessment_2.dynamic_risk_index})")
    logger.info(f"Mitigation Plan: {assessment_2.mitigation_plan}")