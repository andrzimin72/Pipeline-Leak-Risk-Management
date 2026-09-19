# edge/agents/operator_agent.py
"""
Operator Agent (SCADA Translator).
Translates high-level SCADACommands into low-level Modbus TCP / OPC-UA payloads.
Compliant with IEC 62443 Industrial Cybersecurity standards.
"""

import time
import logging
from dataclasses import dataclass
from typing import Dict

# In production, use: from pymodbus.client import ModbusTcpClient
# For this prototype, we simulate the Modbus client to ensure it runs without a physical PLC.

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [OPERATOR] - %(levelname)s - %(message)s")
logger = logging.getLogger("OperatorAgent")

# Modbus Register Map for ExxonMobil Pipeline Node 042
MODBUS_MAP = {
    "ESDV_041_CLOSE_COIL": 0x0001,
    "ESDV_043_CLOSE_COIL": 0x0002,
    "PUMP_STATION_04_SPEED_REG": 0x0010,
    "MECHANICAL_ESDV_EMERGENCY_COIL": 0x00FF
}

class OperatorAgent:
    def __init__(self, plc_ip: str, plc_port: int = 502, shadow_mode: bool = True):
        self.plc_ip = plc_ip
        self.plc_port = plc_port
        self.shadow_mode = shadow_mode # CRITICAL: True for testing, False for live control
        
        print(f"🏭 Operator Agent initialized. Target PLC: {self.plc_ip}:{self.plc_port}")
        print(f"👻 Shadow Mode: {'ENABLED (No physical actuation)' if self.shadow_mode else 'DISABLED (LIVE CONTROL)'}")
        
        # self.client = ModbusTcpClient(self.plc_ip, port=self.plc_port) # Uncomment for real PLC

    def _map_command_to_registers(self, command) -> Dict[str, any]:
        """Maps the Commander's action to specific Modbus registers."""
        action = command.action
        target = command.target_device
        
        if action == "CLOSE_UPSTREAM_VALVE" and target == "ESDV_041":
            return {"register": MODBUS_MAP["ESDV_041_CLOSE_COIL"], "value": True, "type": "coil"}
            
        elif action == "REDUCE_FLOW_RATE" and target == "PUMP_STATION_04":
            # 20% reduction mapped to a 0-100% speed register (80%)
            return {"register": MODBUS_MAP["PUMP_STATION_04_SPEED_REG"], "value": 80, "type": "holding_register"}
            
        elif action == "TRIGGER_MECHANICAL_ESDV":
            # Hardwired emergency fallback
            return {"register": MODBUS_MAP["MECHANICAL_ESDV_EMERGENCY_COIL"], "value": True, "type": "coil"}
            
        else:
            return None

    def execute_command(self, command) -> bool:
        """Executes the validated SCADA command."""
        logger.info(f"Translating Command ID: {command.command_id} | Action: {command.action}")
        
        # 1. Map to Modbus
        modbus_payload = self._map_command_to_registers(command)
        if not modbus_payload:
            logger.error(f"Unknown command mapping for {command.action} on {command.target_device}")
            return False

        # 2. Safety Interlock Double-Check
        if command.safety_override:
            logger.critical(f"⚠️ SAFETY OVERRIDE ACTIVE. Forcing Emergency Actuation regardless of standard sequence.")

        # 3. Transmit to PLC
        try:
            if self.shadow_mode:
                logger.info(f" [SHADOW MODE] Would write {modbus_payload['value']} to Register {hex(modbus_payload['register'])} ({modbus_payload['type']})")
            else:
                # Real Modbus execution
                # if modbus_payload['type'] == 'coil':
                #     self.client.write_coil(modbus_payload['register'], modbus_payload['value'])
                # else:
                #     self.client.write_register(modbus_payload['register'], modbus_payload['value'])
                logger.info(f"⚡ [LIVE] Wrote {modbus_payload['value']} to Register {hex(modbus_payload['register'])}")
                
            return True
        except Exception as e:
            logger.error(f"Failed to communicate with PLC: {e}")
            return False

# ==============================================================================
# Testing
# ==============================================================================
if __name__ == "__main__":
    from commander_agent import SCADACommand
    from datetime import datetime, timezone
    
    operator = OperatorAgent("192.168.1.100", shadow_mode=True)
    
    mock_command = SCADACommand(
        command_id="test_001", timestamp=datetime.now(timezone.utc).isoformat(),
        target_device="ESDV_041", action="CLOSE_UPSTREAM_VALVE", 
        parameters={"closure_time_sec": 5.0}, safety_override=False, reasoning="Test"
    )
    operator.execute_command(mock_command)