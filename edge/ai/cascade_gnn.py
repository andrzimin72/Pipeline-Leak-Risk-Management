# edge/ai/cascade_gnn.py
"""
Cascade Graph Neural Network (GNN).
Models the pipeline as a mathematical graph to predict spatial-temporal cascading failures.
Implemented in pure PyTorch for seamless NVIDIA Jetson Orin deployment.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import logging

logger = logging.getLogger("CascadeGNN")

class GraphAttentionLayer(nn.Module):
    """Single layer of Graph Attention. Computes attention coefficients between connected nodes."""
    def __init__(self, in_features, out_features, dropout=0.2, alpha=0.2):
        super().__init__()
        self.dropout = dropout
        self.in_features = in_features
        self.out_features = out_features
        self.alpha = alpha

        self.W = nn.Parameter(torch.empty(size=(in_features, out_features)))
        nn.init.xavier_uniform_(self.W.data, gain=1.414)
        
        self.a = nn.Parameter(torch.empty(size=(2 * out_features, 1)))
        nn.init.xavier_uniform_(self.a.data, gain=1.414)

        self.leakyrelu = nn.LeakyReLU(self.alpha)

    def forward(self, h, adj):
        """
        h: Node feature matrix (N, in_features)
        adj: Adjacency matrix (N, N) - 1 if nodes are connected, 0 otherwise
        """
        Wh = torch.mm(h, self.W) # (N, out_features)
        N = Wh.size()[0]

        # Calculate attention coefficients
        a_input = torch.cat([Wh.repeat(1, N).view(N * N, -1), Wh.repeat(N, 1)], dim=1)
        e = self.leakyrelu(torch.matmul(a_input, self.a).squeeze(1))
        e = e.view(N, N)

        # Masked softmax (only attend to connected neighbors)
        zero_vec = -9e15 * torch.ones_like(e)
        attention = torch.where(adj > 0, e, zero_vec)
        attention = F.softmax(attention, dim=1)
        attention = F.dropout(attention, self.dropout, training=self.training)

        # Message passing: Weighted sum of neighbor features
        h_prime = torch.matmul(attention, Wh)
        return F.elu(h_prime)

class CascadeGNN(nn.Module):
    """
    Multi-layer Graph Neural Network for Pipeline Cascade Prediction.
    Input: 11-modal sensor scores from all nodes in the mesh.
    Output: Predicted anomaly propagation to neighboring nodes.
    """
    def __init__(self, num_features=11, hidden_dim=16, num_nodes=3):
        super().__init__()
        self.num_nodes = num_nodes
        self.gat1 = GraphAttentionLayer(num_features, hidden_dim)
        self.gat2 = GraphAttentionLayer(hidden_dim, num_features) # Output same dimension as input
        self.dropout = 0.2

    def forward(self, x, adj):
        """
        x: (num_nodes, num_features)
        adj: (num_nodes, num_nodes)
        """
        x = F.dropout(x, self.dropout, training=self.training)
        x = self.gat1(x, adj)
        x = F.dropout(x, self.dropout, training=self.training)
        x = self.gat2(x, adj)
        return F.elu(x)

# ==============================================================================
# Swarm Intelligence Orchestrator
# ==============================================================================
class SwarmIntelligenceOrchestrator:
    def __init__(self, node_id: str, num_nodes: int = 3):
        self.node_id = node_id
        self.num_nodes = num_nodes
        
        # Define the pipeline topology (Adjacency Matrix)
        # Example: 3 nodes in a line (041 - 042 - 043)
        # 1 means connected, 0 means not connected. Diagonal is 1 (self-loop).
        self.adjacency_matrix = torch.tensor([
            [1, 1, 0],
            [1, 1, 1],
            [0, 1, 1]
        ], dtype=torch.float32)

        # Initialize the GNN
        self.gnn = CascadeGNN(num_features=11, hidden_dim=16, num_nodes=num_nodes)
        self.gnn.eval() # Set to inference mode
        
        logger.info(f"Swarm Intelligence Orchestrator initialized for {node_id} with {num_nodes} nodes.")

    def predict_cascade(self, local_features: list, neighbor_features: dict, node_mapping: list) -> dict:
        """
        Predicts how the local anomaly will cascade through the mesh.
        """
        # Construct the global feature matrix for the GNN
        # node_mapping defines the order of nodes in the matrix (e.g., ['041', '042', '043'])
        global_features = torch.zeros((self.num_nodes, 11), dtype=torch.float32)
        
        for i, nid in enumerate(node_mapping):
            if nid == self.node_id:
                global_features[i] = torch.tensor(local_features, dtype=torch.float32)
            elif nid in neighbor_features:
                # Extract the 11 scores from the neighbor's SitRep
                scores = neighbor_features[nid]['sitrep'].get('scores', {})
                # Ensure we have all 11 features in the correct order
                feature_names = ["acoustic", "pressure", "coriolis_mass", "fiber_dts", "point_temp",
                                 "soil_moisture", "capacitance", "vibration", "corrosion", "standard_flow", "physics_residual"]
                global_features[i] = torch.tensor([scores.get(f, 0.0) for f in feature_names], dtype=torch.float32)

        # Run GNN Inference
        with torch.no_grad():
            predicted_states = self.gnn(global_features, self.adjacency_matrix)

        # Extract the prediction for the CURRENT node (how neighbors affect it)
        my_index = node_mapping.index(self.node_id)
        my_predicted_state = predicted_states[my_index].numpy()
        
        # Calculate the "Cascade Threat Score" (difference between local state and GNN prediction)
        cascade_threat = float(torch.mean((global_features[my_index] - predicted_states[my_index]) ** 2).item())

        return {
            "cascade_threat_score": round(cascade_threat, 4),
            "predicted_neighbor_states": predicted_states.numpy().tolist()
        }