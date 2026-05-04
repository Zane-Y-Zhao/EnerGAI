import torch
from torch_geometric.data import Data, Dataset
from torch_geometric.loader import DataLoader
from graph_rag.gnn_model import GraphRAGModel
from typing import List, Tuple
import pickle


class TrainingPipeline:
    def __init__(self, model: GraphRAGModel, learning_rate: float = 0.001):
        self.model = model
        self.optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        self.criterion = torch.nn.CrossEntropyLoss()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def train_epoch(self, loader: DataLoader) -> float:
        """训练一个epoch"""
        self.model.train()
        total_loss = 0
        for batch in loader:
            batch = batch.to(self.device)
            self.optimizer.zero_grad()
            out = self.model(batch)
            loss = self.criterion(out, batch.y)
            loss.backward()
            self.optimizer.step()
            total_loss += loss.item()
        return total_loss / len(loader)

    def evaluate(self, loader: DataLoader) -> float:
        """评估模型"""
        self.model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for batch in loader:
                batch = batch.to(self.device)
                out = self.model(batch)
                pred = out.argmax(dim=1)
                correct += (pred == batch.y).sum().item()
                total += batch.y.size(0)
        return correct / total if total > 0 else 0

    def train(self, train_loader: DataLoader, val_loader: DataLoader, epochs: int = 100):
        """完整训练流程"""
        best_val_acc = 0
        for epoch in range(epochs):
            train_loss = self.train_epoch(train_loader)
            val_acc = self.evaluate(val_loader)
            print(f"Epoch {epoch+1}/{epochs}, Loss: {train_loss:.4f}, Val Acc: {val_acc:.4f}")
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                self.save_model("best_model.pt")
        return best_val_acc

    def save_model(self, path: str):
        """保存模型"""
        torch.save({
            "model_state": self.model.state_dict(),
            "optimizer_state": self.optimizer.state_dict()
        }, path)

    def load_model(self, path: str):
        """加载模型"""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint["model_state"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state"])


def generate_node_embeddings(model: GraphRAGModel, data: Data) -> torch.Tensor:
    """生成节点嵌入"""
    model.eval()
    with torch.no_grad():
        embeddings = model(data)
    return embeddings
