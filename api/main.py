# api/main.py
"""
FastAPI Backend for Nebius AI Cloud.
Central orchestrator for 11-modal telemetry, Dynamic Risk Scoring, 
Multi-Agent SCADA logs, and Prescriptive Mitigation Planning (SAP/Maximo).
"""

import os
import json
import logging
import httpx
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn

# ==============================================================================
# 1. Configuration & Logging
# ==============================================================================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [API] - %(levelname)s - %(message)s")
logger = logging.getLogger("NebiusCloudAPI")

app = FastAPI(
    title="Nebius AI Cloud - Enterprise Pipeline Integrity Platform", 
    description="Pipeline Leak Risk Management Physical AI Platform with Multi-Agent SCADA, Risk Engine, and EAM Integration",
    version="5.0.0"
)

os.makedirs("data", exist_ok=True)
ALERTS_LOG_FILE = "data/alerts.json"
SCADA_LOG_FILE = "data/scada_logs.json"
RISK_LOG_FILE = "data/risk_assessments.json"

# ==============================================================================
# 2. Data Models (Pydantic)
# ==============================================================================
class FusionResultPayload(BaseModel):
    event_id: str
    timestamp: str
    node_id: str
    scores: Dict[str, float] = Field(..., description="Dictionary of 11 modality scores")
    final_confidence: float = Field(..., ge=0.0, le=1.0)
    decision: str
    action_required: str

class SCADACommandLog(BaseModel):
    command_id: str
    timestamp: str
    action: str
    target_device: str
    safety_override: bool
    reasoning: str
    execution_status: str

class PHMSAReport(BaseModel):
    event_id: str
    generated_at: str
    report_text: str
    compliance_status: str

class WorkOrderResponse(BaseModel):
    notification_id: str
    work_order_id: str
    status: str

# ==============================================================================
# 3. Enterprise Integrations (Risk Engine & Mitigation Planner)
# ==============================================================================
# We use try/except to ensure the API runs even if the cloud modules are in different paths
try:
    from cloud.risk.risk_engine import DynamicRiskScoringEngine, SensorMetrics, GISContext
    from cloud.planner.mitigation_planner import PrescriptiveMitigationPlanner
    
    risk_engine = DynamicRiskScoringEngine()
    mitigation_planner = PrescriptiveMitigationPlanner(
        eam_api_url="https://sap-gateway.exxonmobil.com/sap/opu/odata/sap/PM_WORKORDER",
        auth_token="mock-sap-oauth-token",
        auto_approve_critical=True
    )
    ENTERPRISE_MODULES_LOADED = True
except ImportError:
    ENTERPRISE_MODULES_LOADED = False
    logger.warning("Enterprise Risk/Planner modules not found. Running in core telemetry mode.")

# ==============================================================================
# 4. Helper Functions
# ==============================================================================
def append_to_json(filepath: str, record: dict):
    records = []
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            try: records = json.load(f)
            except json.JSONDecodeError: records = []
    records.append(record)
    with open(filepath, "w") as f:
        json.dump(records, f, indent=2, default=str)

async def generate_phmsa_report_real(payload: FusionResultPayload) -> PHMSAReport:
    """Generates a highly detailed PHMSA report using Nebius Nemotron."""
    logger.info(f"Querying Nebius Nemotron for Event {payload.event_id}...")
    
    NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY", "your-nebius-api-key-here")
    NEBIUS_ENDPOINT = "https://api.nebius.com/v1/inference/completions"
    
    scores_str = ", ".join([f"{k.replace('_', ' ').capitalize()}: {v}" for k, v in payload.scores.items()])
    prompt = (
        "You are an AI Pipeline Integrity Officer for ExxonMobil. "
        "Generate a formal, concise PHMSA initial incident report based on this 11-modal sensor fusion data. "
        f"Data: Node {payload.node_id}. Scores: {scores_str}. "
        f"Final AI Confidence: {payload.final_confidence * 100:.1f}%. Decision: {payload.decision}."
    )
    
    headers = {"Authorization": f"Bearer {NEBIUS_API_KEY}", "Content-Type": "application/json"}
    payload_json = {"model": "nemotron-3-super", "messages": [{"role": "user", "content": prompt}], "temperature": 0.2}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(NEBIUS_ENDPOINT, json=payload_json, headers=headers)
            response.raise_for_status()
            report_text = response.json()["choices"][0]["message"]["content"]
            return PHMSAReport(event_id=payload.event_id, generated_at=datetime.utcnow().isoformat(), report_text=report_text, compliance_status="PENDING_VERIFICATION")
    except Exception as e:
        logger.error(f"Nebius API call failed: {e}")
        return PHMSAReport(event_id=payload.event_id, generated_at=datetime.utcnow().isoformat(), report_text=f"ERROR: API Failed. Raw Scores: {payload.scores}", compliance_status="API_ERROR")

def get_mock_gis_context(node_id: str) -> GISContext:
    """Mock GIS context for prototype. In production, query PostGIS database."""
    if "042" in node_id: # Simulate high consequence area
        return GISContext(population_density_score=0.9, environmental_sensitivity=0.95, economic_value_score=0.8)
    return GISContext(population_density_score=0.1, environmental_sensitivity=0.2, economic_value_score=0.5)

# ==============================================================================
# 5. API Endpoints
# ==============================================================================
@app.get("/")
def root():
    return {
        "status": "Nebius AI Cloud API is online.", 
        "system": "Pipeline Leak Risk Management 11-Modal Multi-Agent Monitor",
        "enterprise_modules_loaded": ENTERPRISE_MODULES_LOADED
    }

@app.post("/api/v1/alerts", response_model=PHMSAReport, status_code=201)
async def receive_edge_alert(payload: FusionResultPayload):
    logger.info(f"Received 11-Modal Alert from Node {payload.node_id} | Decision: {payload.decision}")

    # 1. Generate PHMSA Report
    if payload.decision == "SAFE":
        report = PHMSAReport(event_id=payload.event_id, generated_at=datetime.utcnow().isoformat(), report_text="Normal operations.", compliance_status="NOMINAL")
    else:
        report = await generate_phmsa_report_real(payload)
        
    append_to_json(ALERTS_LOG_FILE, {"payload": payload.model_dump(), "report": report.model_dump()})

    # 2. Dynamic Risk Scoring & Mitigation Planning (If Enterprise Modules are loaded)
    if ENTERPRISE_MODULES_LOADED and payload.decision != "SAFE":
        # Extract metrics for Risk Engine
        metrics = SensorMetrics(
            anomaly_score=payload.scores.get("acoustic", 0.0),
            physics_residual=payload.scores.get("physics_residual", 0.0),
            corrosion_rate=payload.scores.get("corrosion", 0.0),
            vibration_level=payload.scores.get("vibration", 0.0),
            cascade_threat=payload.scores.get("cascade_threat", 0.0) # Passed from Swarm
        )
        context = get_mock_gis_context(payload.node_id)
        
        # Calculate Risk
        assessment = risk_engine.assess_risk(payload.node_id, metrics, context)
        append_to_json(RISK_LOG_FILE, assessment.__dict__)
        
        # Trigger Mitigation Planner if HIGH or CRITICAL
        if assessment.risk_tier in ["HIGH", "CRITICAL"]:
            logger.warning(f"Risk Tier {assessment.risk_tier} detected. Triggering Prescriptive Mitigation Planner.")
            work_order = mitigation_planner.generate_work_order(
                node_id=payload.node_id,
                dri=assessment.dynamic_risk_index,
                risk_tier=assessment.risk_tier,
                mitigation_plan=assessment.mitigation_plan
            )
            if work_order:
                append_to_json(RISK_LOG_FILE, {"work_order": work_order.__dict__})

    return report

@app.post("/api/v1/scada_shadow_log", status_code=202)
async def receive_scada_log(payload: SCADACommandLog):
    logger.info(f"Received SCADA Shadow Log: Command {payload.command_id} | Action: {payload.action}")
    append_to_json(SCADA_LOG_FILE, payload.model_dump())
    return {"status": "SCADA log recorded successfully."}

@app.get("/api/v1/risk/nodes")
async def get_risk_nodes():
    """Serves risk data to the Executive Heatmap Dashboard."""
    if os.path.exists(RISK_LOG_FILE):
        with open(RISK_LOG_FILE, "r") as f:
            try: return json.load(f)
            except: return []
    return []

# ==============================================================================
# 6. Execution
# ==============================================================================
if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
