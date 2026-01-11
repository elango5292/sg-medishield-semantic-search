"""
Base class for all enrichers.
"""
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseEnricher(ABC):
    """
    Base class for data enrichers.
    
    Enrichers take raw extracted data and add metadata.
    """
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def enrich(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Enrich extracted data with metadata.
        
        Args:
            data: Raw extracted data
            
        Returns:
            Enriched data dictionary
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
    
    def save_output(self, data: dict[str, Any], filename: str) -> Path:
        """
        Save enriched data to JSON file.
        
        Args:
            data: Enriched data dictionary
            filename: Output filename (without extension)
            
        Returns:
            Path to saved file
        """
        output_path = self.output_dir / f"{filename}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return output_path
    
    def run(self, input_path: Path) -> Path:
        """
        Run enrichment and save output.
        
        Args:
            input_path: Path to input JSON file
            
        Returns:
            Path to saved JSON file
        """
        input_path = Path(input_path)
        data = self.load_input(input_path)
        enriched_data = self.enrich(data)
        filename = input_path.stem
        return self.save_output(enriched_data, filename)
