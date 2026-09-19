#!/usr/bin/env python3
"""
Pipeline Leak Risk Management Physical AI Platform - Executive Demonstration Script
Scenario: ExxonMobil and Enbridge Mustang Oil Pipeline (346 km) - "The 30-Second Save"

Three Interactive Scenarios:
  A: AI Success (Safe Pressure < 1200 PSI)
  B: Safety Interlock Override (Unsafe Pressure > 1200 PSI)
  C: Swarm Intelligence Cascade Prevention (Multi-Node Protection)

Features: Interactive scenarios, live telemetry stream, LLM typewriter effect,
and enhanced PDF technical appendix.
"""

import time
import sys
import os
import random
from datetime import datetime, timezone

# ==============================================================================
# 1. Dependency Check
# ==============================================================================
try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️  Warning: 'fpdf2' not found. PDF report will be skipped.")
    print("   Install via: pip install fpdf2\n")

# ==============================================================================
# 2. Terminal Styling & Utilities
# ==============================================================================
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}\n  {text}\n{'='*70}{Colors.END}\n")

def print_log(component, message, color=Colors.END):
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"  [{timestamp}] {Colors.BOLD}[{component}]{Colors.END} {color}{message}{Colors.END}")

def stream_text(text, delay=0.015, color=Colors.END):
    """Typewriter effect for LLM output."""
    print(f"  {color}", end="")
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print(Colors.END)

def wait(seconds, message=""):
    if message:
        print(f"\n  ⏳ {message} ({seconds}s)...")
    time.sleep(seconds)

def print_box(title, content, color=Colors.BLUE):
    width = 62
    print(f"\n  {color}┌{'─'*(width-2)}┐{Colors.END}")
    print(f"  {color}│ {title:<{width-4}} │{Colors.END}")
    print(f"  {color}├{'─'*(width-2)}{Colors.END}")
    for line in content.split('\n'):
        print(f"  {color}│ {line:<{width-4}} │{Colors.END}")
    print(f"  {color}└{'─'*(width-2)}┘{Colors.END}\n")

# ==============================================================================
# 3. Simulation Data
# ==============================================================================
NODE_ID = "EMPCO-MUSTANG-SEG4-NODE042"
PIPELINE = "EMPCO Mustang Heavy Crude Line (346 km)"
REPORT_FILENAME = "ExxonMobil_PhysicalAI_Demo_Report_v3.pdf"

NORMAL_SENSORS = {
    "Acoustic RMS": 0.12, "Pressure Drop": 4.2, "Coriolis Mass": 0.08,
    "Fiber DTS": 0.15, "Point Temp": 0.4, "Soil Moisture": 1.2,
    "Capacitance": 0.8, "Vibration": 0.25, "Corrosion": 1.5,
    "Std Flow": 0.5, "Physics Residual": 0.05
}

LEAK_SENSORS = {
    "Acoustic RMS": 0.85, "Pressure Drop": 42.0, "Coriolis Mass": 3.2,
    "Fiber DTS": 3.8, "Point Temp": 4.5, "Soil Moisture": 15.0,
    "Capacitance": 9.5, "Vibration": 0.30, "Corrosion": 12.5,
    "Std Flow": 2.8, "Physics Residual": 0.92
}

# ==============================================================================
# 4. PDF Report Generation
# ==============================================================================
def generate_pdf_report(scenario_name, interlock_overridden, is_cascade=False):
    if not PDF_AVAILABLE:
        return

    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 15, "Executive Summary: Physical AI Platform", ln=True, align="C")
    pdf.set_font("Helvetica", "", 14)
    pdf.cell(0, 10, "EMPCO Mustang Segment Demonstration", ln=True, align="C")
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 5, f"Date: {datetime.now().strftime('%B %d, %Y')} | {scenario_name}", ln=True)
    pdf.cell(0, 5, f"Asset: {PIPELINE} | Node: {NODE_ID}", ln=True)
    pdf.ln(10)

    # Executive Summary
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 10, "1. Executive Summary", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(0, 0, 0)
    
    if is_cascade:
        summary = (
            f"This demonstration simulated a catastrophic multi-segment cascade event on the EMPCO Mustang pipeline. "
            f"The Physical AI platform's Swarm Intelligence (Graph Neural Network) predicted the cascade 6.2 seconds before impact. "
            f"Through ZeroMQ mesh communication, neighboring nodes (043, 044) executed pre-emptive isolation, "
            f"preventing a network-wide failure and saving an estimated $48M in damages."
        )
    else:
        summary = (
            f"This demonstration simulated a catastrophic event on the EMPCO Mustang pipeline. "
            f"The Physical AI platform detected a micro-fracture and autonomously isolated the segment. "
            f"{'The Safety Interlock successfully overrode the AI to trigger a mechanical emergency shutdown.' if interlock_overridden else 'The AI command was validated and executed successfully.'} "
            "The entire process took under 30 seconds."
        )
    
    pdf.multi_cell(0, 6, summary)
    pdf.ln(5)

    # Key Metrics
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 10, "2. Key Performance Metrics", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(0, 0, 0)
    
    if is_cascade:
        metrics = [
            "Cascade Prediction Time: 6.2 seconds before impact",
            "Time to Multi-Node Isolation: 3.8 seconds",
            "Nodes Protected: 3 (042, 043, 044)",
            "Estimated Damage Prevented: $48,000,000",
            "Spill Prevented: 450 barrels",
            "Swarm Mesh Latency: < 50ms between nodes"
        ]
    else:
        metrics = [
            "Time to Detect: 12 seconds",
            "Time to Physical Isolation: 18 seconds",
            "Estimated Spill Volume: < 2 Barrels (Contained)",
            "Dynamic Risk Index (DRI) Peak: 88 (Critical)",
            "Safety Interlock Overrides: " + ("1 (AI rejected)" if interlock_overridden else "0 (AI validated)")
        ]
    
    for metric in metrics:
        pdf.cell(10, 7, chr(8226), ln=False)
        pdf.cell(0, 7, metric, ln=True)

    pdf.ln(5)

    # Technical Appendix: Sensor Data
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 10, "3. Technical Appendix: 11-Modal Sensor Telemetry", ln=True)
    
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(50, 7, "Sensor Modality", 1, 0, 'C', True)
    pdf.cell(40, 7, "Baseline Value", 1, 0, 'C', True)
    pdf.cell(40, 7, "Incident Value", 1, 0, 'C', True)
    pdf.cell(40, 7, "Deviation (%)", 1, 1, 'C', True)
    
    pdf.set_font("Helvetica", "", 9)
    for sensor in NORMAL_SENSORS:
        normal = NORMAL_SENSORS[sensor]
        leak = LEAK_SENSORS[sensor]
        dev = ((leak - normal) / normal) * 100 if normal > 0 else 0
        pdf.cell(50, 6, sensor, 1)
        pdf.cell(40, 6, f"{normal:.3f}", 1, 0, 'C')
        pdf.cell(40, 6, f"{leak:.3f}", 1, 0, 'C')
        pdf.cell(40, 6, f"+{dev:.0f}%", 1, 1, 'C')

    # Footer
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, "CONFIDENTIAL - For Internal ExxonMobil Use Only", ln=True, align="C")

    pdf.output(REPORT_FILENAME)
    print(f"\n{Colors.GREEN}✅ PDF Report generated: {REPORT_FILENAME}{Colors.END}")

# ==============================================================================
# 5. Main Demo Execution
# ==============================================================================
def run_demo():
    clear_screen()
    print_header("EXXONMOBIL PHYSICAL AI PLATFORM: INTERACTIVE DEMO v3.0")
    
    # Interactive Scenario Selection
    print("  Select Demonstration Scenario:")
    print("  [1] Scenario A: AI Success (Safe Pressure < 1200 PSI)")
    print("  [2] Scenario B: Safety Interlock Override (Unsafe Pressure > 1200 PSI)")
    print("  [3] Scenario C: Swarm Intelligence Cascade Prevention (NEW)")
    print("\n  Scenario C demonstrates edge-to-edge predictive protection")
    print("  across multiple pipeline segments.")
    
    choice = input("\n  Enter choice (1, 2, or 3): ").strip()
    
    if choice == "1":
        scenario = "A"
        is_override = False
        is_cascade = False
    elif choice == "2":
        scenario = "B"
        is_override = True
        is_cascade = False
    else:
        scenario = "C"
        is_override = False
        is_cascade = True
    
    clear_screen()
    
    if is_cascade:
        print_header(f"SCENARIO {scenario}: SWARM INTELLIGENCE CASCADE PREVENTION")
        print(f"  Asset: {PIPELINE}")
        print(f"  Nodes: {NODE_ID}, NODE-043, NODE-044")
        print(f"  Context: Multi-segment cascade risk (High Consequence Area)")
    else:
        print_header(f"SCENARIO {scenario}: {'SAFETY INTERLOCK OVERRIDE' if is_override else 'AI SUCCESS'}")
        print(f"  Asset: {PIPELINE}")
        print(f"  Node: {NODE_ID}")
    
    wait(2, "Initializing system context")

    # --- PHASE 1: Live Telemetry Stream ---
    print(f"\n{Colors.BOLD}{Colors.CYAN}▶ PHASE 1: Live Telemetry Stream (Baseline){Colors.END}")
    print("  Streaming 11-modal sensor data at 1Hz...\n")
    
    if is_cascade:
        for i in range(3):
            node_ids = ["NODE-042", "NODE-043", "NODE-044"]
            for node in node_ids:
                pressure = 4.0 + random.uniform(-0.5, 0.5)
                print(f"  [T-{3-i}s] {node}: Pressure Drop: {pressure:.2f} PSI | Status: NOMINAL")
            time.sleep(0.5)
    else:
        for i in range(5):
            pressure = 4.0 + random.uniform(-0.5, 0.5)
            acoustic = 0.10 + random.uniform(-0.02, 0.02)
            print(f"  [T-{5-i}s] Pressure Drop: {pressure:.2f} PSI | Acoustic RMS: {acoustic:.3f} | Status: NOMINAL")
            time.sleep(0.5)
    
    wait(2, "Establishing baseline")

    # --- PHASE 2: The Incident ---
    print(f"\n{Colors.BOLD}{Colors.RED}▶ PHASE 2: Black Swan Event (T+0s){Colors.END}")
    
    if is_cascade:
        print_log("Cosmos Generator", "INJECTING: Multi-segment pressure surge + frost heave.", Colors.RED)
        print_log("Physical World", "Catastrophic failure at Node 042. Cascade risk detected...", Colors.RED)
        print("\n   ⚠️  SWARM ALERT: GNN predicts cascade to Nodes 043 & 044 in < 8 seconds")
    else:
        print_log("Cosmos Generator", "INJECTING: Frost heave + unauthorized excavation.", Colors.RED)
        print_log("Physical World", "Micro-fracture detected. Sensor spikes incoming...", Colors.RED)
    
    print("\n   Sensor Spike Injection (Node 042):")
    for sensor, val in LEAK_SENSORS.items():
        normal_val = NORMAL_SENSORS[sensor]
        change = ((val - normal_val) / normal_val) * 100
        print(f"     {sensor:<20} {normal_val:.2f} ➔ {val:.2f} ({Colors.RED}+{change:.0f}%{Colors.END})")
    wait(2, "Propagating anomaly")

    # --- PHASE 3: AI Perception & Swarm Intelligence ---
    print(f"\n{Colors.BOLD}{Colors.CYAN}▶ PHASE 3: Edge Perception & Swarm Intelligence (T+12s){Colors.END}")
    
    if is_cascade:
        print_log("Sentinel Agent (042)", "Transformer MSE spikes. Anomaly Score: 0.94", Colors.YELLOW)
        print_log("Swarm GNN", "️ CASCADE PREDICTION: Nodes 043 & 044 at risk in 6.2 seconds", Colors.RED)
        print_log("ZeroMQ Mesh", "Broadcasting pre-emptive warning to mesh...", Colors.CYAN)
        print_log("Node 043", "Received cascade warning. Pre-emptive isolation initiated.", Colors.GREEN)
        print_log("Node 044", "Received cascade warning. Flow reduction activated.", Colors.GREEN)
    else:
        print_log("Sentinel Agent", "Transformer MSE spikes. Anomaly Score: 0.88", Colors.YELLOW)
        print_log("Swarm GNN", "Cascade threat predicted for Node 043.", Colors.RED)
    
    wait(2, "Processing handoff")

    # --- PHASE 4: Commander & Safety Interlock ---
    print(f"\n{Colors.BOLD}{Colors.CYAN}▶ PHASE 4: Commander Agent & Safety Interlock (T+15s){Colors.END}")
    
    if is_cascade:
        print_log("Commander (042)", "Nemotron proposes: EMERGENCY ISOLATION + MESH ALERT", Colors.BLUE)
        print_log("Safety Interlock", "Validating multi-node isolation sequence...", Colors.BOLD)
        print_log("Safety Interlock", "✅ Cascade prevention protocol approved.", Colors.GREEN)
        action_taken = "Multi-Node Pre-emptive Isolation"
    else:
        print_log("Commander", "Nemotron proposes: CLOSE_UPSTREAM_VALVE (ESDV_041)", Colors.BLUE)
        mock_pressure = 1250.0 if is_override else 980.0
        print_log("Safety Interlock", f"Checking absolute pressure: {mock_pressure} PSI...", Colors.BOLD)
        
        if is_override:
            print_log("Safety Interlock", f"️ CRITICAL: {mock_pressure} PSI > 1200 PSI limit.", Colors.RED)
            print_log("Safety Interlock", "AI COMMAND REJECTED. Triggering Mechanical ESDV.", Colors.RED)
            action_taken = "Mechanical ESDV (Override)"
        else:
            print_log("Safety Interlock", f"Limit: 1200 PSI. {mock_pressure} < 1200. ✅ COMMAND VALIDATED.", Colors.GREEN)
            action_taken = "AI-Validated Valve Closure"
    
    wait(2, "Executing safety logic")

    # --- PHASE 5: SCADA Execution ---
    print(f"\n{Colors.BOLD}{Colors.CYAN}▶ PHASE 5: Autonomous SCADA Execution (T+18s){Colors.END}")
    
    if is_cascade:
        print_log("Operator Agent (042)", "Executing: Emergency isolation", Colors.GREEN)
        print_log("Operator Agent (043)", "Executing: Pre-emptive isolation (cascade prevention)", Colors.GREEN)
        print_log("Operator Agent (044)", "Executing: Flow reduction (cascade mitigation)", Colors.GREEN)
        print_log("SCADA Network", "Multi-node isolation complete in 3.8 seconds.", Colors.GREEN)
        print_log("Swarm Mesh", "✅ CASCADE PREVENTED. Network stability maintained.", Colors.GREEN)
    else:
        print_log("Operator Agent", f"Executing: {action_taken}", Colors.GREEN)
        print_log("SCADA PLC", "Flow isolated in 4.2 seconds.", Colors.GREEN)
    
    wait(2, "Syncing enterprise systems")

    # --- PHASE 6: Enterprise Integration ---
    print(f"\n{Colors.BOLD}{Colors.CYAN}▶ PHASE 6: Enterprise Integration (T+25s){Colors.END}")
    
    if is_cascade:
        print_log("Risk Engine", "Network-wide DRI recalculated: 92 (CRITICAL).", Colors.RED)
        print_log("Risk Engine", "Cascade prevention saved estimated $48M in multi-segment damage.", Colors.GREEN)
        print_log("SAP/Maximo", "WO #40009999 (Node 042), #40010001 (Node 043) created.", Colors.GREEN)
        print(f"\n  {Colors.BOLD}Nemotron LLM Drafting PHMSA Report:{Colors.END}")
        phmsa_text = (
            "CRITICAL INCIDENT: Multi-segment cascade event prevented by autonomous swarm intelligence. "
            "Pre-emptive isolation at Nodes 042, 043, and 044 prevented network-wide failure. "
            "Estimated prevention of 450-barrel spill across 12 km river crossing."
        )
        stream_text(f"  \"{phmsa_text}\"", delay=0.02, color=Colors.CYAN)
    else:
        print_log("Risk Engine", "DRI recalculated: 88 (CRITICAL).", Colors.RED)
        print_log("SAP/Maximo", "WO #40009999 created. Priority: 1.", Colors.GREEN)
        print(f"\n  {Colors.BOLD}Nemotron LLM Drafting PHMSA Report:{Colors.END}")
        phmsa_text = (
            "INITIAL INCIDENT REPORT: Critical leak detected at Milepost 112.4. "
            "Autonomous isolation successful. Environmental impact contained. "
            "Dispatching HAZMAT team for verification."
        )
        stream_text(f"  \"{phmsa_text}\"", delay=0.02, color=Colors.CYAN)
    
    wait(2, "Finalizing")

    # --- CONCLUSION ---
    clear_screen()
    print_header("DEMONSTRATION COMPLETE")
    
    if is_cascade:
        print_box("MISSION SUCCESS: CASCADE PREVENTED", 
            f"Scenario: {scenario}\n"
            f"Action: {action_taken}\n"
            f"Nodes Protected: 3 (042, 043, 044)\n"
            f"Time to Isolation: 3.8 seconds\n"
            f"Estimated Damage Prevented: $48M\n"
            f"Spill Prevented: 450 barrels", Colors.GREEN)
    else:
        print_box("MISSION SUCCESS", 
            f"Scenario: {scenario}\n"
            f"Action: {action_taken}\n"
            f"Time to Isolate: 4.2 seconds\n"
            f"Estimated Spill: < 2 Barrels", Colors.GREEN)

    print("  ✅ 11-modal AI fusion detected the anomaly.")
    if is_cascade:
        print("  ✅ Swarm GNN predicted cascade 6.2 seconds before impact.")
        print("  ✅ ZeroMQ mesh enabled pre-emptive multi-node protection.")
    else:
        print("  ✅ Deterministic Safety Interlock ensured physical safety.")
    print("  ✅ Enterprise systems (SAP/PHMSA) automated instantly.")
    print(f"{'='*70}\n")

    # Generate PDF
    scenario_desc = f"Scenario {scenario} ({'Cascade Prevention' if is_cascade else ('Override' if is_override else 'Success')})"
    generate_pdf_report(scenario_desc, is_override, is_cascade)

if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        print("\n\nDemo aborted.")
        sys.exit(0)
