# edge/mesh/swarm_mesh.py
"""
Edge-to-Edge Mesh Communication Layer.
Enables decentralized, ultra-low-latency "whispering" between Jetson nodes 
using ZeroMQ (ZMQ) to share SitReps and Physics States.
"""

import json
import time
import logging
import threading
import zmq

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [MESH] - %(levelname)s - %(message)s")
logger = logging.getLogger("SwarmMesh")

class SwarmMesh:
    def __init__(self, node_id: str, bind_port: int, neighbor_ports: list):
        self.node_id = node_id
        self.context = zmq.Context()
        
        # PUB socket: Broadcasts this node's state to neighbors
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.bind(f"tcp://*:{bind_port}")
        
        # SUB socket: Listens to neighbors' states
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "") # Subscribe to all topics
        
        for port in neighbor_ports:
            self.subscriber.connect(f"tcp://localhost:{port}") # Use localhost for local simulation
            
        self.received_states = {}
        self.running = True
        
        logger.info(f"Node {self.node_id} Mesh initialized. Binding to {bind_port}, listening to {neighbor_ports}")

    def start_listening(self):
        """Runs in a background thread to continuously ingest neighbor data."""
        def listen():
            poller = zmq.Poller()
            poller.register(self.subscriber, zmq.POLLIN)
            
            while self.running:
                socks = dict(poller.poll(timeout=1000))
                if self.subscriber in socks and socks[self.subscriber] == zmq.POLLIN:
                    message = self.subscriber.recv_string()
                    try:
                        data = json.loads(message)
                        self.received_states[data['node_id']] = data
                    except json.JSONDecodeError:
                        pass
        threading.Thread(target=listen, daemon=True).start()

    def broadcast_state(self, sitrep: dict, physics_state: dict):
        """Broadcasts the local node's Situation Report and Physics State to the mesh."""
        payload = {
            "node_id": self.node_id,
            "timestamp": time.time(),
            "sitrep": sitrep,
            "physics_state": physics_state
        }
        self.publisher.send_string(json.dumps(payload))

    def get_neighbor_states(self) -> dict:
        """Returns the latest received states from neighboring nodes."""
        # Filter out states older than 2 seconds to prevent stale data
        current_time = time.time()
        return {
            nid: data for nid, data in self.received_states.items() 
            if (current_time - data['timestamp']) < 2.0
        }

    def stop(self):
        self.running = False
        self.publisher.close()
        self.subscriber.close()
        self.context.term()