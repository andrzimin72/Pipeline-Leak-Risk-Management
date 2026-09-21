# shared/constants.py
"""
Global constants for the Pipeline Leak Risk Management Physical AI Platform.
10-Modal Sensor Fusion for Pipeline Integrity Management.
"""

# ==============================================================================
# 1. PIPELINE & FLUID PROPERTIES (Crude Oil)
# ==============================================================================
SPEED_OF_SOUND_IN_OIL_MPS = 1250.0 
NORMAL_OPERATING_PRESSURE_PSI = 1000.0  
PIPE_DIAMETER_INCHES = 36.0             

# ==============================================================================
# 2. SENSOR THRESHOLDS (Edge - Jetson)
# ==============================================================================
# Primary Indicators (High Confidence)
ALERT_THRESHOLD_DB = 0.35               # Acoustic RMS amplitude threshold
PRESSURE_DROP_THRESHOLD_PSI = 15.0      # Minimum negative pressure wave
MASS_IMBALANCE_THRESHOLD_PERCENT = 0.5  # Coriolis Mass Flow (Highly precise)
FIBER_THERMAL_ANOMALY_THRESHOLD_C = 1.5 # Distributed Temperature Sensing (DTS)

# Secondary/Contextual Indicators
TEMP_DROP_THRESHOLD_CELSIUS = 2.5       # Point temperature sensor
SOIL_MOISTURE_CHANGE_THRESHOLD_PERCENT = 8.0 # Soil dielectric change
CAPACITANCE_CHANGE_THRESHOLD_PERCENT = 5.0 # Above-ground pipe insulation/pooling

# Tertiary/Integrity Indicators
VIBRATION_THRESHOLD_G = 0.8             # Third-party damage / excavator
CORROSION_RATE_THRESHOLD_MPY = 5.0      # Mils Per Year (LPR probe sudden spike)
STANDARD_FLOW_THRESHOLD_PERCENT = 2.0   # Legacy volumetric flow backup

# ==============================================================================
# 3. EDGE DEVICE & NETWORK CONFIGURATION
# ==============================================================================
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_PREFIX = "exxonmobil/pipeline/node042/"
DATA_FRESHNESS_SEC = 5.0                # Max age of sensor data for fusion
FUSION_INTERVAL_SEC = 3.0               # How often to run the fusion engine

NEBIUS_API_BASE_URL = "https://api.nebius.com/v1"
NEBIUS_NEMOTRON_ENDPOINT = f"{NEBIUS_API_BASE_URL}/inference/completions"

# ==============================================================================
# 4. REGULATORY & COMPLIANCE (PHMSA / EPA)
# ==============================================================================
MIN_REPORTABLE_SPILL_GALLONS = 42       
MAX_ALLOWED_RESPONSE_TIME_MIN = 15      

# ==============================================================================
# 5. AI MODEL CONFIGURATION
# ==============================================================================
INFERENCE_PRECISION = "FP16"            
CONFIDENCE_THRESHOLD_HIGH = 0.70        # Adjusted for 10-modal high-fidelity
CONFIDENCE_THRESHOLD_LOW = 0.35         
