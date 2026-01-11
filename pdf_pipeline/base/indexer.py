"""
Base class for indexers.
"""
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseIndexer(ABC):
    """
    Base class for vector database indexers.
    
    Indexers upsert nodes with embeddings to a vector database.
    """
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
    
    @abstractmethod
    def upsert(self, nodes: list[dict[str, Any]], namespace: str = None) -> int:
        """
        Upsert nodes to the vector database.
        
        Args:
            nodes: List of node dictionaries with embeddings
            namespace: Optional namespace for the vectors
            
        Returns:
            Number of vectors upserted
        """
        pass
    
    def load_nodes(self, input_path: Path) -> list[dict[str, Any]]:
        """
        Load nodes from JSON file.
        
        Args:
            input_path: Path to input JSON file
            
        Returns:
            List of node dictionaries
        """
        with open(input_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def run(self, input_path: Path, namespace: str = None) -> int:
        """
        Load nodes and upsert to database.
        
        Args:
            input_path: Path to input JSON file
            namespace: Optional namespace for the vectors
            
        Returns:
            Number of vectors upserted
        """
        input_path = Path(input_path)
        nodes = self.load_nodes(input_path)
        return self.upsert(nodes, namespace)
