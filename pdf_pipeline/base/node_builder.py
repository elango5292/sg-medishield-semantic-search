"""
Base class for all node builders.
"""
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseNodeBuilder(ABC):
    """
    Base class for node builders.
    
    Node builders create LlamaIndex-compatible nodes from enriched data.
    """
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def build_nodes(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Build nodes from enriched data.
        
        Args:
            data: Enriched data dictionary
            
        Returns:
            List of node dictionaries
        """
        pass
    
    def load_input(self, input_path: Path) -> dict[str, Any]:
        """
        Load input JSON file.
        
        Args:
            input_path: Path to input JSON file
            
        Returns:
            Loaded data dictionary
        """
        with open(input_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def save_nodes(self, nodes: list[dict[str, Any]], filename: str) -> Path:
        """
        Save nodes to JSON file.
        
        Args:
            nodes: List of node dictionaries
            filename: Output filename (without extension)
            
        Returns:
            Path to saved file
        """
        output_path = self.output_dir / f"{filename}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(nodes, f, indent=2, ensure_ascii=False)
        return output_path
    
    def run(self, input_path: Path) -> Path:
        """
        Run node building and save output.
        
        Args:
            input_path: Path to input JSON file
            
        Returns:
            Path to saved JSON file
        """
        input_path = Path(input_path)
        data = self.load_input(input_path)
        nodes = self.build_nodes(data)
        filename = input_path.stem
        return self.save_nodes(nodes, filename)
