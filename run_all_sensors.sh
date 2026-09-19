#!/bin/bash
echo "🚀 Launching all 10 Edge Sensor Listeners..."

# Run each sensor in the background
python edge/sensors/acoustic_listener.py &
python edge/sensors/pressure_listener.py &
python edge/sensors/coriolis_mass_flow_listener.py &
python edge/sensors/fiber_dts_listener.py &
python edge/sensors/point_temperature_listener.py &
python edge/sensors/soil_moisture_listener.py &
python edge/sensors/capacitive_listener.py &
python edge/sensors/vibration_listener.py &
python edge/sensors/corrosion_listener.py &
python edge/sensors/standard_flow_listener.py &

echo "✅ All 10 sensors are running in the background. Press Ctrl+C to stop."
wait