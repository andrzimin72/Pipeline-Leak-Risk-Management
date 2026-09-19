# edge/inference/fusion_model.py
"""
Edge Multi-Agent Pipeline Orchestrator with Swarm Intelligence.
Ingests 10 raw MQTT sensor streams + Cosmos Context, calculates the 11th PhysicsNeMo residual,
normalizes the data, feeds the Multi-Agent Pipeline, and utilizes Edge-to-Edge Mesh GNNs 
for pre-emptive cascading failure prediction.
"""

import time
import json
import uuid
import sys
import os
import ssl
import logging
import requests
import numpy as np
import paho.mqtt.client as mqtt
from dataclasses import dataclass
from datetime import datetime, timezone

# Ensure project root is in path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.constants import (
    ALERT_THRESHOLD_DB, PRESSURE_DROP_THRESHOLD_PSI, MASS_IMBALANCE_THRESHOLD_PERCENT,
    FIBER_THERMAL_ANOMALY_THRESHOLD_C, TEMP_DROP_THRESHOLD_CELSIUS,
    SOIL_MOISTURE_CHANGE_THRESHOLD_PERCENT, CAPACITANCE_CHANGE_THRESHOLD_PERCENT,
    VIBRATION_THRESHOLD_G, CORROSION_RATE_THRESHOLD_MPY, STANDARD_FLOW_THRESHOLD_PERCENT,
    MQTT_BROKER, MQTT_PORT, MQTT_TOPIC_PREFIX, DATA_FRESHNESS_SEC, FUSION_INTERVAL_SEC
)

# Import Multi-Agent Pipeline
from edge.agents.sentinel_agent import SentinelAgent
from edge.agents.commander_agent import CommanderAgent
from edge.agents.operator_agent import OperatorAgent

# Import Horizon 1: Swarm Intelligence
from edge.mesh.swarm_mesh import SwarmMesh
from edge.ai.cascade_gnn import SwarmIntelligenceOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [ORCHESTRATOR] - %(levelname)s - %(message)s")
logger = logging.getLogger("EdgeOrchestrator")

# ==============================================================================
# 1. PhysicsNeMo Predictive Module (Embedded)
# ==============================================================================
@dataclass
class PhysicsState:
    inlet_pressure_psi: float
    flow_rate_bbl_hr: float
    fluid_temperature_c: float
    pipe_length_m: float

class PhysicsNeMoSurrogate:
    def __init__(self, pipe_length_m: float):
        self.pipe_length_m = pipe_length_m
        
    def predict_next_state(self, current_state: PhysicsState) -> dict:
        friction_factor = 0.015; density_kg_m3 = 850.0; velocity_m_s = current_state.flow_rate_bbl_hr * 0.000044 
        theoretical_pressure_drop = friction_factor * (self.pipe_length_m / 0.914) * (density_kg_m3 * velocity_m_s**2) / 2000
        predicted_outlet_pressure = current_state.inlet_pressure_psi - theoretical_pressure_drop + ((current_state.fluid_temperature_c - 20.0) * 0.05)
        return {"predicted_pressure_psi": predicted_outlet_pressure}

class PhysicsResidualCalculator:
    def __init__(self):
        self.predictor = PhysicsNeMoSurrogate(pipe_length_m=5000.0) 
        
    def calculate_residual(self, actual_pressure: float, actual_flow: float, actual_temp: float) -> float:
        current_state = PhysicsState(inlet_pressure_psi=actual_pressure + 10.0, flow_rate_bbl_hr=actual_flow, fluid_temperature_c=actual_temp, pipe_length_m=5000.0)
        prediction = self.predictor.predict_next_state(current_state)
        pressure_error = abs(actual_pressure - prediction["predicted_pressure_psi"])
        return min(1.0, max(0.0, (pressure_error - 2.0) / 20.0))

# ==============================================================================
# 2. Data Normalization (Feeding the Sentinel)
# ==============================================================================
class DataNormalizer:
    def _score(self, value: float, threshold: float, max_scale: float) -> float:
        if value <= threshold: return 0.0
        return min(1.0, (value - threshold) / max_scale)

    def normalize(self, raw_values: dict) -> dict:
        return {
            "acoustic": self._score(raw_values["acoustic"], ALERT_THRESHOLD_DB, 0.5),
            "pressure": self._score(raw_values["pressure"], PRESSURE_DROP_THRESHOLD_PSI, 30.0),
            "coriolis_mass": self._score(raw_values["coriolis_mass"], MASS_IMBALANCE_THRESHOLD_PERCENT, 2.0),
            "fiber_dts": self._score(raw_values["fiber_dts"], FIBER_THERMAL_ANOMALY_THRESHOLD_C, 3.0),
            "point_temp": self._score(raw_values["point_temp"], TEMP_DROP_THRESHOLD_CELSIUS, 5.0),
            "soil_moisture": self._score(raw_values["soil_moisture"], SOIL_MOISTURE_CHANGE_THRESHOLD_PERCENT, 10.0),
            "capacitance": self._score(raw_values["capacitance"], CAPACITANCE_CHANGE_THRESHOLD_PERCENT, 10.0),
            "vibration": self._score(raw_values["vibration"], VIBRATION_THRESHOLD_G, 1.0),
            "corrosion": self._score(raw_values["corrosion"], CORROSION_RATE_THRESHOLD_MPY, 10.0),
            "standard_flow": self._score(0.0, STANDARD_FLOW_THRESHOLD_PERCENT, 4.0),
            "physics_residual": raw_values["physics_residual"]
        }

# ==============================================================================
# 3. Secure MQTT Subscriber & Aggregator (Cosmos Context Aware)
# ==============================================================================
class EdgeMQTTAggregator:
    def __init__(self, node_id: str, sentinel_agent: SentinelAgent):
        self.node_id = node_id
        self.sentinel = sentinel_agent
        
        self.client = mqtt.Client(client_id=f"fusion_engine_{node_id}", protocol=mqtt.MQTTv311)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        # --- mTLS Security Configuration ---
        cert_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../security/certs'))
        self.client.tls_set(
            ca_certs=os.path.join(cert_dir, "ca.crt"),
            certfile=os.path.join(cert_dir, "client.crt"),
            keyfile=os.path.join(cert_dir, "client.key"),
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLSv1_2
        )
        self.client.tls_insecure_set(False)
        logger.info("mTLS Security Enabled for MQTT Connection")

        self.sensor_topics = [
            "acoustic", "pressure", "coriolis_mass", "fiber_dts", "point_temp",
            "soil_moisture", "capacitance", "vibration", "corrosion", "standard_flow"
        ]
        self.control_topics = ["cosmos_context"]
        
        self.latest_data = {topic: {"value": 0.0, "time": 0.0} for topic in self.sensor_topics}
        self.physics_calculator = PhysicsResidualCalculator()
        
        self.baseline_pressure = 1000.0
        self.baseline_temp = 25.0

    def on_connect(self, client, userdata, flags, rc):
        logger.info(f"Connected to Secure MQTT Broker (Code: {rc})")
        for topic in self.sensor_topics:
            client.subscribe(f"{MQTT_TOPIC_PREFIX}{topic}")
        client.subscribe(f"{MQTT_TOPIC_PREFIX}cosmos_context")

    def on_message(self, client, userdata, msg):
        topic_suffix = msg.topic.split("/")[-1]
        
        if topic_suffix == "cosmos_context":
            context_flag = msg.payload.decode()
            logger.info(f"Received Cosmos Context Injection: {context_flag}")
            self.sentinel.inject_cosmos_context(context_flag)
            return

        if topic_suffix in self.sensor_topics:
            try:
                payload = json.loads(msg.payload.decode())
                self.latest_data[topic_suffix] = {"value": float(payload["value"]), "time": time.time()}
            except Exception as e:
                logger.error(f"Error parsing MQTT message for {topic_suffix}: {e}")

    def start(self):
        logger.info(f"Starting 11-Modal Secure MQTT Listener on {MQTT_BROKER}:{MQTT_PORT}...")
        self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
        self.client.loop_start()

    def get_fresh_features(self) -> tuple:
        now = time.time()
        values = {}
        for topic in self.sensor_topics:
            data = self.latest_data[topic]
            if (now - data["time"]) > DATA_FRESHNESS_SEC: 
                return None
            values[topic] = data["value"]

        values["physics_residual"] = self.physics_calculator.calculate_residual(
            actual_pressure=values["pressure"], 
            actual_flow=values["coriolis_mass"], 
            actual_temp=values["point_temp"]
        )

        abs_pressure = self.baseline_pressure - values["pressure"]
        abs_temp = self.baseline_temp - values["point_temp"]

        return values, abs_pressure, abs_temp

# ==============================================================================
# 4. Main Execution Loop (Swarm-Enabled Multi-Agent Orchestrator)
# ==============================================================================
def run_edge_pipeline():
    logger.info("Starting Swarm-Enabled Multi-Agent Edge Pipeline...")
    node_id = "JETSON-NODE-042"
    
    # 1. Initialize Agent 1: Sentinel (Perception & PyTorch Transformer)
    sentinel = SentinelAgent(node_id=node_id, seq_len=10)
    
    # 2. Initialize Agent 3: Operator (Executes physical commands via Modbus)
    operator = OperatorAgent(plc_ip="192.168.1.100", shadow_mode=True)
    
    # 3. Initialize Agent 2: Commander (Reasoning & Safety Interlock)
    commander = CommanderAgent(node_id=node_id, operator_agent=operator)
    
    # 4. Initialize Data Ingestion
    aggregator = EdgeMQTTAggregator(node_id, sentinel_agent=sentinel)
    aggregator.start()
    normalizer = DataNormalizer()

    # 5. Initialize Horizon 1: Swarm Intelligence (Mesh + GNN)
    # Node 042 binds to 5555, listens to 041 (5554) and 043 (5556)
    mesh = SwarmMesh(node_id=node_id, bind_port=5555, neighbor_ports=[5554, 5556])
    mesh.start_listening()
    
    swarm_orchestrator = SwarmIntelligenceOrchestrator(node_id=node_id, num_nodes=3)
    node_mapping = ["JETSON-NODE-041", "JETSON-NODE-042", "JETSON-NODE-043"]
    
    api_url = "https://localhost:8000/api/v1/alerts"
    scada_log_url = "https://localhost:8000/api/v1/scada_shadow_log" 
    last_fusion_time = 0

    try:
        while True:
            now = time.time()
            if (now - last_fusion_time) >= FUSION_INTERVAL_SEC:
                features = aggregator.get_fresh_features()
                
                if features:
                    raw_values, abs_pressure, abs_temp = features
                    normalized_scores = normalizer.normalize(raw_values)
                    
                    # --- STEP A: Agent 1 (Sentinel) Perceives the World ---
                    sitrep = sentinel.process_sensor_stream(normalized_scores)
                    
                    # --- STEP B: Swarm Intelligence (Mesh Broadcast & GNN Prediction) ---
                    mesh.broadcast_state(
                        sitrep={"decision": sitrep.decision, "anomaly_score": sitrep.anomaly_score, "scores": normalized_scores},
                        physics_state={"pressure": abs_pressure, "temp": abs_temp}
                    )
                    
                    neighbor_states = mesh.get_neighbor_states()
                    cascade_prediction = swarm_orchestrator.predict_cascade(
                        local_features=[normalized_scores.get(k, 0.0) for k in sentinel.feature_names],
                        neighbor_features=neighbor_states,
                        node_mapping=node_mapping
                    )
                    
                    cascade_threat = cascade_prediction["cascade_threat_score"]
                    
                    # Pre-emptive Strike Logic: If GNN predicts massive cascade, override local safe state
                    if cascade_threat > 0.5:
                        logger.warning(f"SWARM ALERT: Cascading failure predicted! Threat Score: {cascade_threat}")
                        if sitrep.decision != "CRITICAL_FAILURE":
                            sitrep.decision = "CRITICAL_FAILURE"
                            sitrep.anomaly_score = max(sitrep.anomaly_score, cascade_threat)

                    logger.info(f"Cycle: {sitrep.decision} | Anomaly: {sitrep.anomaly_score:.4f} | Cascade Threat: {cascade_threat:.4f} | Context: {sitrep.cosmos_context}")
                    
                    # --- STEP C: Agent 2 (Commander) Reasons & Acts ---
                    if sitrep.decision != "SAFE":
                        logger.warning(f"ALERT TRIGGERED: {sitrep.decision}")
                        
                        scada_command = commander.process_sitrep(
                            sitrep, 
                            current_pressure=abs_pressure, 
                            current_temp=abs_temp
                        )
                        
                        scada_payload = {
                            "command_id": scada_command.command_id,
                            "timestamp": scada_command.timestamp,
                            "action": scada_command.action,
                            "target_device": scada_command.target_device,
                            "safety_override": scada_command.safety_override,
                            "reasoning": scada_command.final_reasoning,
                            "execution_status": scada_command.execution_status,
                            "cascade_threat_score": cascade_threat # Added Swarm context to audit log
                        }
                        try:
                            requests.post(scada_log_url, json=scada_payload, timeout=5, verify=False)
                        except Exception as e:
                            logger.debug(f"Audit logging failed: {e}")
                    else:
                        logger.debug("System Nominal.")

                    # --- STEP D: Cloud Reporting (PHMSA) ---
                    payload_dict = {
                        "event_id": sitrep.event_id, 
                        "timestamp": datetime.now(timezone.utc).isoformat(), 
                        "node_id": node_id,
                        "scores": normalized_scores, 
                        "final_confidence": sitrep.confidence,
                        "decision": sitrep.decision, 
                        "action_required": "MONITOR" if sitrep.decision == "SAFE" else "EXECUTE_SCADA"
                    }

                    try:
                        requests.post(api_url, json=payload_dict, timeout=10, verify=False) 
                    except requests.exceptions.RequestException as e:
                        logger.warning(f"API Connection Failed: {e}")
                        
                else:
                    logger.debug("Waiting for fresh data from all 11 modalities...")
                    
                last_fusion_time = now
                
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        logger.info("Shutting down Edge Pipeline...")
        aggregator.client.loop_stop()
        aggregator.client.disconnect()
        mesh.stop()

if __name__ == "__main__":
    run_edge_pipeline()