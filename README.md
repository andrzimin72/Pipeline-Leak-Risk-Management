## Pipeline-Leak-Risk-Management
This is an autonomous, multi-modal Physical AI platform designed for real-time oil pipeline integrity monitoring, predictive risk assessment, and autonomous leak mitigation. The system integrates 11 heterogeneous sensor modalities with Physics-Informed Neural Networks (PINNs), Multi-Agent Reinforcement Learning (MARL), Graph Neural Networks (GNNs) for swarm intelligence, and Federated Learning for privacy-preserving model training. 

### 1. What exactly is the software product we have created?
We have created an Autonomous Physical AI Platform for Critical Infrastructure Integrity Management. Think of it as a "central nervous system" for a pipeline. It combines the "eyes and ears" of 11 physical sensors, the "reflexes" of a deterministic safety interlock, the "brain" of a multi-agent AI system, and the "business logic" of enterprise cloud integration. It is a closed-loop system that perceives physical anomalies, reasons about them, takes autonomous physical action to mitigate them, and automates the resulting regulatory and maintenance paperwork.

### 2. What is the platform's primary goal?
The primary goal is to prevent catastrophic pipeline failures (leaks, ruptures, and environmental disasters) by shifting from reactive human monitoring to proactive, autonomous AI intervention.
Secondary goals include minimizing financial loss, ensuring strict regulatory compliance (PHMSA), and optimizing maintenance spending through predictive risk analysis.

### 3. What key tasks does it address?
a) Real-time Anomaly Detection: Identifying leaks, corrosion, third-party interference, and mechanical failures instantly.

b) Autonomous Physical Mitigation: Safely isolating a damaged pipeline segment (closing valves) without waiting for human intervention.

c) Predictive Risk Assessment: Calculating the Probability of Failure (PoF) and Consequence of Failure (CoF) to predict where the next failure will occur.

d) Regulatory and Maintenance Automation: Automatically generating legally compliant incident reports (PHMSA) and dispatching maintenance crews via enterprise systems (SAP/Maximo).

### 4. What are its main functions?
a) 11-Modal Sensor Fusion: Combining Acoustic, Pressure, Coriolis, Fiber DTS, Temperature, Soil Moisture, Capacitance, Vibration, Corrosion, Flow, and Physics Residual data.

b) Physics-Informed AI (PhysicsNeMo): Using fluid dynamics equations to detect anomalies that pure data-driven AI might miss.

c) Multi-Agent Reasoning: A Swarm of AI agents (Sentinel for perception, Commander for reasoning, Operator for execution).

d) Deterministic Safety Interlock: A hard-coded, non-AI rule engine (IEC 61508 compliant) that overrides the AI if a physical action would be dangerous.

e) Swarm Intelligence: Edge-to-edge communication via ZeroMQ and Graph Neural Networks (GNN) to predict cascading failures.

f) Federated Learning: Training global AI models across thousands of edge nodes without ever exposing proprietary sensor data to the cloud.

### 5. In which areas of the oil and gas industry can this software be used?
a) Midstream: Long-distance transmission pipelines (crude oil, natural gas, NGLs), pumping stations, and compressor stations. (This is the primary use case).

b) Upstream: Flowlines connecting wellheads to gathering stations, especially in remote or harsh environments.

c) Downstream: Refinery piping networks, tank farms, and loading/unloading terminals.

d) Emerging Energy: Hydrogen pipelines, Carbon Capture and Storage (CCUS) transport networks, and ammonia transport.

### 6. For which tasks is it best suited, and for which is it NOT recommended?
#### 6.1. Best Suited For:
a) High Consequence Areas (HCAs): Pipelines crossing rivers, near population centers, or in environmentally sensitive zones.

b) Remote/Unmanned Assets: Locations where human response time is measured in hours, not seconds.

c) Hazardous Materials: Transporting heavy crude, sour gas (H2S), or high-pressure natural gas where a rupture is catastrophic.

#### 6.2. Not Recommended For:
a) Low-Risk/Low-Pressure Systems: Municipal water lines or low-pressure irrigation. The cost of the hardware (Jetson, 11 sensors) vastly outweighs the risk of a leak.

b) Highly Dynamic Multiphase Flow: If a pipeline has extreme "slugging" (rapid, chaotic alternations of gas and liquid), the PhysicsNeMo fluid dynamics model would require massive, highly specific retraining before deployment.

c) Legacy Infrastructure without Upgrades: If the physical pipeline lacks the basic sensors (like fiber optics or Coriolis meters) or automated valves, the software cannot perform its physical mitigation functions.

### 7. What are the limitations regarding its use?
a) Sensor Dependency (Garbage In, Garbage Out): The AI is only as good as the physical sensors. If a pressure transmitter is poorly calibrated or a fiber optic cable is cut by a backhoe, the system's perception is blinded.

b) Regulatory Certification Lag: While the software is ready, getting autonomous SCADA control legally approved by local regulators (like PHMSA in the US) requires a lengthy, rigorous Safety Integrity Level (SIL 2/3) certification process. It cannot be turned on "live" on day one.

c) High Initial CapEx: Deploying 11 sensors and an NVIDIA Jetson Orin at every node is expensive. It requires a strong ROI justification (which the Risk Engine provides).

d) Edge Compute Limits: The Jetson Orin is powerful, but it is not a cloud GPU. Extremely massive global models must be distilled or quantized (via TensorRT) to run locally.

e) Cloud Dependency for Enterprise Features: While the edge can survive 72 hours offline for safety, features like SAP work order generation, Federated Learning aggregation, and Nemotron LLM reasoning require cloud connectivity.

### 8. Project demonstration
This project accompany with a Python demonstration script. The ExxonMobil/Enbridge Mustang Oil Pipeline is a major oil pipeline jointly operated by ExxonMobil and Enbridge. It plays an important role in oil transportation in the United States.

The total length of the Mustang Oil Pipeline is 215 miles (346 kilometers). This oil pipeline became a vital link in the logistics chain transporting oil from the western United States to refineries and export terminals. Together with other projects by ExxonMobil and Enbridge (such as Pegasus), it formed an extensive pipeline network connecting the United States and Canada.

Key Characteristics Mustang Oil Pipeline: The pipeline begins in Lockport, Illinois, where it connects to the Enbridge Lakehead system, and extends to the Patoka terminal, also in Illinois. It is primarily designed to transport heavy crude oil. Pipe diameter is 18 inches. The initial design capacity was approximately 91,000 barrels per day (bpd), with 88,000 bpd committed to specific shipments. 

File: /demo_mustang_oil_pipeline.py.

### 9. Installation
#### Scenario A: Local Development (Docker Compose)
This is the fastest way to spin up the entire stack (API, Dashboard, MQTT, Database, and Edge Simulator) on a single machine.

A.1. Clone the Repository:
bash
   git clone https://github.com/pipeline-ai-platform.git
   cd pipeline-ai-platform

A.2. Configure Environment Variables:
Copy the example environment file and update it with your local or mock credentials:
bash
   cp .env.example .env
   #Edit .env with your preferred text editor

A.3. Start the Platform:
Use the provided Makefile to build and start all services in the background:
bash
   make up
Alternatively, run docker-compose up --build -d directly.

A.4. Verify Services:
bash
   docker-compose ps
Ensure all containers (api, dashboard, postgres, mosquitto) show a healthy or running status.

#### Scenario B: Production Deployment (Kubernetes via Helm)
For deploying to the Nebius AI Cloud or an on-premise K8s cluster.

B.1. Initialize Terraform (Infrastructure):
bash
   cd terraform
   terraform init
   terraform plan -var-file=environments/prod.tfvars
   terraform apply -var-file=environments/prod.tfvars

B.2. Deploy via Helm
bash
   cd ../helm/pipeline-ai-platform
   helm dependency build
   
   helm install pipeline-ai . \
     --namespace pipeline-ai \
     --create-namespace \
     --values values-prod.yaml \
     --set global.secrets.nebiusApiKey=$NEBIUS_API_KEY \
     --set global.secrets.sapAuthToken=$SAP_AUTH_TOKEN
#### Scenario C: Edge Node Deployment (Jetson Orin)
Deploying the Multi-Agent system to a physical pipeline node.

C.1. Build the Edge Image:
bash
   docker build -t nebiusai/pipeline-edge:latest -f Dockerfile.edge .

C.2. Run the Edge Container:
bash
   docker run -d \
     --name pipeline-edge-042 \
     --runtime nvidia \
     --gpus all \
     --network host \
     --restart unless-stopped \
     -v $(pwd)/config.yaml:/app/config.yaml:ro \
     -v $(pwd)/security/certs:/app/security/certs:ro \
     -e NODE_ID=JETSON-NODE-042 \
     nebiusai/pipeline-edge:latest

### 10. Quick Start & Validation
Once the platform is running, follow these steps to validate the installation and see the system in action.

#### Step 1: Access the Dashboards
Open your web browser and navigate to the following URLs (if running locally):
a) Executive Dashboard (Streamlit): http://localhost:8501
Check: Verify the "System Status" sidebar shows active nodes and the Risk Heatmap is rendering.
b) Monitoring (Grafana): http://localhost:3000
Credentials: admin / (your GRAFANA_ADMIN_PASSWORD).
Check: Open the "Pipeline API Metrics" dashboard. You should see live request rates and latency graphs.
c) Cloud API (FastAPI Docs): http://localhost:8000/docs
Check: The Swagger UI should load, showing all available endpoints (/api/v1/alerts, /api/v1/risk/nodes, etc.).

#### Step 2: Run the Executive Demonstration
To validate the core logic without needing physical hardware, run the interactive demo script:
bash
# Ensure dependencies are installed
pip install fpdf2

# Run the demo
python demo_mustang_oil_pipeline.py
Select Option 1 for a standard AI success scenario. Watch the terminal output simulate the 30-second save, and verify that a PDF report is generated in your root directory.

##### Step 3: Inject a Live Test Event (Optional)
To test the live Docker Compose stack with synthetic data:
a) Open a new terminal.
b) Run the Cosmos Black Swan Generator:
bash
   python cloud/cosmos_black_swan_generator.py
c) Watch the Streamlit Dashboard (localhost: 8501). You should see:
- The 11-Modal Radar Chart spike;
- The Risk Heatmap node turn Red;
- A new SAP Work Order appear in the "Autonomous Actions" tab.
