# cloud/planner/mitigation_planner.py
"""
Prescriptive Mitigation Planner.
Translates AI Risk Assessments into structured SAP PM / IBM Maximo 
Notifications and Work Orders. Closes the loop between AI and the human workforce.
"""

import time
import uuid
import logging
import requests
from dataclasses import dataclass
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [PLANNER] - %(levelname)s - %(message)s")
logger = logging.getLogger("MitigationPlanner")

# ==============================================================================
# 1. Enterprise Asset Management (EAM) Mappings
# ==============================================================================
# Maps Edge Node IDs to SAP Functional Locations and Equipment IDs
ASSET_REGISTRY = {
    "NODE-042": {"func_loc": "FL-PIPE-SEC4-042", "equip_id": "EQ-PIPE-042", "work_center": "WC-MAINT-04"},
    "NODE-045": {"func_loc": "FL-PIPE-SEC5-045", "equip_id": "EQ-PIPE-045", "work_center": "WC-MAINT-05"},
}

# Maps AI Mitigation Keywords to Standard EAM Task List Codes
TASK_LIST_MAPPING = {
    "visual inspection": "TL-INSP-01",
    "drone": "TL-DRONE-02",
    "smart pig": "TL-ILI-03", # In-Line Inspection
    "flow rate": "TL-OPS-04", # Operations adjustment
    "isolation": "TL-EMRG-05", # Emergency isolation
    "replacement": "TL-REPL-06"
}

@dataclass
class EAMWorkOrder:
    """Standardized payload for SAP PM / Maximo REST API."""
    notification_id: str
    work_order_id: str
    functional_location: str
    equipment_id: str
    priority: str  # 1=Emergency, 2=High, 3=Medium, 4=Low
    short_text: str
    task_list: str
    status: str
    created_at: float

# ==============================================================================
# 2. The Prescriptive Mitigation Planner
# ==============================================================================
class PrescriptiveMitigationPlanner:
    def __init__(self, eam_api_url: str, auth_token: str, auto_approve_critical: bool = True):
        self.eam_api_url = eam_api_url
        self.headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        self.auto_approve_critical = auto_approve_critical
        
        logger.info("Prescriptive Mitigation Planner initialized.")
        logger.info(f"Target EAM Endpoint: {self.eam_api_url}")

    def _map_ai_to_eam(self, ai_actions: List[str]) -> str:
        """Translates AI text recommendations into a primary EAM Task List Code."""
        combined_text = " ".join(ai_actions).lower()
        for keyword, task_code in TASK_LIST_MAPPING.items():
            if keyword in combined_text:
                return task_code
        return "TL-GEN-00" # General inspection fallback

    def _calculate_eam_priority(self, dri: float, risk_tier: str) -> str:
        """Maps Dynamic Risk Index to SAP/Maximo Priority Codes."""
        if dri >= 75 or risk_tier == "CRITICAL":
            return "1" # Emergency (Break the glass)
        elif dri >= 50 or risk_tier == "HIGH":
            return "2" # High
        elif dri >= 25 or risk_tier == "MEDIUM":
            return "3" # Medium
        else:
            return "4" # Low / Routine

    def _push_to_eam_api(self, payload: dict) -> dict:
        """
        Simulates the REST API call to SAP Gateway (OData) or IBM Maximo.
        In production, replace this with actual requests.post() to the corporate ESB.
        """
        logger.info(f"📡 Transmitting payload to EAM API: {payload['short_text']}")
        
        # MOCK API RESPONSE (Simulating SAP/Maximo success)
        time.sleep(0.5) 
        mock_response = {
            "status": "success",
            "sap_notification_id": f"1000{uuid.uuid4().int % 10000}",
            "sap_work_order_id": f"4000{uuid.uuid4().int % 10000}",
            "message": "Notification created and converted to Work Order."
        }
        
        # In production:
        # response = requests.post(f"{self.eam_api_url}/api/maintenance/notifications", json=payload, headers=self.headers)
        # response.raise_for_status()
        # return response.json()
        
        return mock_response

    def generate_work_order(self, node_id: str, dri: float, risk_tier: str, mitigation_plan: List[str]) -> EAMWorkOrder:
        """
        Main orchestrator: Translates Risk Assessment into an EAM Work Order.
        """
        if node_id not in ASSET_REGISTRY:
            logger.error(f"Node {node_id} not found in Asset Registry. Cannot generate Work Order.")
            return None

        asset_info = ASSET_REGISTRY[node_id]
        priority = self._calculate_eam_priority(dri, risk_tier)
        primary_task = self._map_ai_to_eam(mitigation_plan)
        
        # Construct the Short Text (Max 40 chars for SAP standard)
        short_text = f"AI RISK {risk_tier}: {mitigation_plan[0].split(':')[0].strip()[:30]}"

        # 1. Create the EAM Payload
        eam_payload = {
            "functional_location": asset_info["func_loc"],
            "equipment": asset_info["equip_id"],
            "work_center": asset_info["work_center"],
            "priority": priority,
            "short_text": short_text,
            "task_list": primary_task,
            "long_text": " | ".join(mitigation_plan),
            "reporter": "NEBIUS_AI_AGENT",
            "auto_approve": self.auto_approve_critical and priority == "1"
        }

        # 2. Push to EAM System
        api_response = self._push_to_eam_api(eam_payload)

        # 3. Construct Final Work Order Object
        work_order = EAMWorkOrder(
            notification_id=api_response["sap_notification_id"],
            work_order_id=api_response["sap_work_order_id"],
            functional_location=asset_info["func_loc"],
            equipment_id=asset_info["equip_id"],
            priority=priority,
            short_text=short_text,
            task_list=primary_task,
            status="APPROVED" if eam_payload["auto_approve"] else "PENDING_PLANNER_APPROVAL",
            created_at=time.time()
        )

        logger.info(f"✅ EAM Integration Successful. Notification: {work_order.notification_id} | WO: {work_order.work_order_id} | Status: {work_order.status}")
        return work_order

# ==============================================================================
# 3. Execution & Testing
# ==============================================================================
if __name__ == "__main__":
    # Initialize Planner (Mocking SAP API URL and Auth Token)
    planner = PrescriptiveMitigationPlanner(
        eam_api_url="https://sap-gateway.exxonmobil.com/sap/opu/odata/sap/PM_WORKORDER",
        auth_token="mock-sap-oauth-token-12345",
        auto_approve_critical=True
    )

    # Scenario 1: Critical Risk (Auto-Approved Work Order)
    logger.info("--- SCENARIO 1: Critical Risk (Auto-Approve) ---")
    wo_1 = planner.generate_work_order(
        node_id="NODE-042",
        dri=82.5,
        risk_tier="CRITICAL",
        mitigation_plan=[
            "IMMEDIATE: Trigger autonomous SCADA isolation (ESDV).",
            "IMMEDIATE: Dispatch emergency response team.",
            "SHORT-TERM: Conduct emergency In-Line Inspection (Smart Pig)."
        ]
    )
    
    # Scenario 2: Medium Risk (Requires Human Planner Approval)
    logger.info("\n--- SCENARIO 2: Medium Risk (Pending Approval) ---")
    wo_2 = planner.generate_work_order(
        node_id="NODE-045",
        dri=35.0,
        risk_tier="MEDIUM",
        mitigation_plan=[
            "SHORT-TERM: Increase sensor polling rate to 1Hz.",
            "LONG-TERM: Add to next quarterly Risk-Based Inspection (RBI) schedule."
        ]
    )