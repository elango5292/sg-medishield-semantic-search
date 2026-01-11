"""
Base class for all extractors.
"""
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseExtractor(ABC):
    """
    Base class for PDF extractors.
    
    Extractors take a PDF file and produce raw JSON output.
    """
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def extract(self, pdf_path: Path) -> dict[str, Any]:
        """
        Extract data from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing extracted data
        """
        pass
    
    def save_output(self, data: dict[str, Any], filename: str) -> Path:
        """
        Save extracted data to JSON file.
        
        Args:
            data: Extracted data dictionary
            filename: Output filename (without extension)
            
        Returns:
            Path to saved file
        """
        output_path = self.output_dir / f"{filename}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return output_path
    
    def run(self, pdf_path: Path) -> Path:
        """
        Run extraction and save output.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Path to saved JSON file
        """
        pdf_path = Path(pdf_path)
        data = self.extract(pdf_path)
        filename = pdf_path.stem
        return self.save_output(data, filename)
