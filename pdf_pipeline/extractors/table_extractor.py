"""
Table extractor using pdfplumber.
"""
from pathlib import Path
from typing import Any

import pdfplumber
from PIL import Image

from pdf_pipeline.base import BaseExtractor
from pdf_pipeline import config


class TableExtractor(BaseExtractor):
    """
    Extract tables from PDF using pdfplumber.
    
    Outputs raw table data and cropped table images.
    """
    
    def __init__(
        self,
        output_dir: Path = None,
        images_dir: Path = None,
    ):
        output_dir = output_dir or config.RAW_TABLES_DIR
        super().__init__(output_dir)
        self.images_dir = images_dir or config.IMAGES_TABLES_DIR
        self.images_dir.mkdir(parents=True, exist_ok=True)
    
    def extract(self, pdf_path: Path) -> dict[str, Any]:
        """
        Extract all tables from a PDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with source and list of tables
        """
        pdf_path = Path(pdf_path)
        tables = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_tables = page.find_tables()
                
                for table_idx, table in enumerate(page_tables):
                    table_data = self._extract_table(
                        page=page,
                        table=table,
                        page_num=page_num,
                        table_idx=table_idx,
                        pdf_stem=pdf_path.stem,
                    )
                    tables.append(table_data)
        
        return {
            "source": pdf_path.name,
            "tables": tables,
        }
    
    def _extract_table(
        self,
        page: pdfplumber.page.Page,
        table: pdfplumber.table.Table,
        page_num: int,
        table_idx: int,
        pdf_stem: str,
    ) -> dict[str, Any]:
        """
        Extract data from a single table.
        """
        # Get bounding box
        bbox = table.bbox  # (x0, y0, x1, y1)
        
        # Extract raw data
        raw_data = table.extract()
        
        # Extract cells with positions
        cells = []
        for row_idx, row in enumerate(raw_data):
            for col_idx, cell_text in enumerate(row):
                cells.append({
                    "row": row_idx,
                    "col": col_idx,
                    "text": cell_text or "",
                })
        
        # Crop and save table image
        image_path = self._save_table_image(
            page=page,
            bbox=bbox,
            page_num=page_num,
            table_idx=table_idx,
            pdf_stem=pdf_stem,
        )
        
        return {
            "page": page_num,
            "table_index": table_idx,
            "table_bbox": list(bbox),
            "cells": cells,
            "raw_data": raw_data,
            "image_path": str(image_path) if image_path else None,
        }
    
    def _save_table_image(
        self,
        page: pdfplumber.page.Page,
        bbox: tuple,
        page_num: int,
        table_idx: int,
        pdf_stem: str,
    ) -> Path | None:
        """
        Crop and save table as image.
        """
        try:
            # Crop the page to table area
            cropped = page.crop(bbox)
            
            # Convert to image
            img = cropped.to_image(resolution=150)
            
            # Save image
            image_filename = f"{pdf_stem}_p{page_num}_t{table_idx}.png"
            image_path = self.images_dir / image_filename
            img.save(image_path)
            
            return image_path
        except Exception as e:
            print(f"Warning: Could not save table image: {e}")
            return None


# CLI entry point
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m pdf_pipeline.extractors.table_extractor <pdf_path>")
        sys.exit(1)
    
    config.create_output_dirs()
    
    pdf_path = Path(sys.argv[1])
    extractor = TableExtractor()
    output_path = extractor.run(pdf_path)
    print(f"Tables extracted to: {output_path}")
