import torch
from torch_geometric.nn import GCNConv, GATConv
from torch_geometric.data import Data


class GraphRAGModel(torch.nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, num_heads=4):
        super(GraphRAGModel, self).__init__()
        self.conv1 = GATConv(input_dim, hidden_dim, heads=num_heads)
        self.conv2 = GATConv(hidden_dim * num_heads, output_dim, heads=1)
        self.dropout = torch.nn.Dropout(0.3)

    def forward(self, data):
        x, edge_index = data.x, data.edge_index
        x = self.conv1(x, edge_index)
        x = torch.nn.functional.elu(x)
        x = self.dropout(x)
        x = self.conv2(x, edge_index)
        return x
