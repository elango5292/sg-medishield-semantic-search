"""
Text extractor using Unstructured.
"""
from pathlib import Path
from typing import Any

from unstructured.partition.pdf import partition_pdf

from pdf_pipeline.base import BaseExtractor
from pdf_pipeline import config


class TextExtractor(BaseExtractor):
    """
    Extract text, sections, and images from PDF using Unstructured.
    
    Outputs raw element data and cropped figure images.
    """
    
    def __init__(
        self,
        output_dir: Path = None,
        images_dir: Path = None,
    ):
        output_dir = output_dir or config.RAW_TEXT_DIR
        super().__init__(output_dir)
        self.images_dir = images_dir or config.IMAGES_FIGURES_DIR
        self.images_dir.mkdir(parents=True, exist_ok=True)
    
    def extract(self, pdf_path: Path) -> dict[str, Any]:
        """
        Extract all text elements from a PDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with source and list of elements
        """
        pdf_path = Path(pdf_path)
        
        # Partition PDF using Unstructured
        elements = partition_pdf(
            filename=str(pdf_path),
            strategy="hi_res",
            extract_images_in_pdf=True,
            extract_image_block_output_dir=str(self.images_dir),
            infer_table_structure=False,  # We use pdfplumber for tables
        )
        
        # Convert elements to dictionaries
        extracted_elements = []
        for element in elements:
            element_data = self._element_to_dict(element)
            extracted_elements.append(element_data)
        
        return {
            "source": pdf_path.name,
            "elements": extracted_elements,
        }
    
    def _element_to_dict(self, element) -> dict[str, Any]:
        """
        Convert an Unstructured element to a dictionary.
        """
        metadata = element.metadata.to_dict() if hasattr(element.metadata, 'to_dict') else {}
        
        # Extract coordinates if available
        coordinates = None
        if hasattr(element.metadata, 'coordinates') and element.metadata.coordinates:
            coords = element.metadata.coordinates
            if hasattr(coords, 'points'):
                coordinates = {
                    "points": coords.points,
                    "system": str(coords.system) if hasattr(coords, 'system') else None,
                }
        
        return {
            "type": element.category,
            "element_id": element.id,
            "text": str(element),
            "metadata": {
                "page_number": getattr(element.metadata, 'page_number', None),
                "coordinates": coordinates,
                "parent_id": getattr(element.metadata, 'parent_id', None),
                "filename": getattr(element.metadata, 'filename', None),
            },
        }


# CLI entry point
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m pdf_pipeline.extractors.text_extractor <pdf_path>")
        sys.exit(1)
    
    config.create_output_dirs()
    
    pdf_path = Path(sys.argv[1])
    extractor = TextExtractor()
    output_path = extractor.run(pdf_path)
    print(f"Text extracted to: {output_path}")
