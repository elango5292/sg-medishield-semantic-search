"""Table extractor using pdfplumber."""
from pathlib import Path
from typing import Any

import pdfplumber

from pdf_pipeline.base import BaseExtractor
from pdf_pipeline import config


class TableExtractor(BaseExtractor):
    """Extract tables from PDF using pdfplumber."""

    def __init__(self, output_dir: Path = None, images_dir: Path = None):
        output_dir = output_dir or config.RAW_TABLES_DIR
        super().__init__(output_dir)
        self.images_dir = images_dir or config.IMAGES_TABLES_DIR
        self.images_dir.mkdir(parents=True, exist_ok=True)

    def extract(self, pdf_path: Path) -> dict[str, Any]:
        """Extract all tables from a PDF."""
        pdf_path = Path(pdf_path)
        tables = []
        saved_pages = set()  # Track which pages we've already saved

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_tables = page.find_tables()
                
                # Save full page image once if there are tables on this page
                page_image_path = None
                if page_tables and page_num not in saved_pages:
                    page_image_path = self._save_page_image(page, page_num, pdf_path.stem)
                    saved_pages.add(page_num)

                for table_idx, table in enumerate(page_tables):
                    tables.append({
                        "page": page_num,
                        "table_index": table_idx,
                        "bbox": list(table.bbox),
                        "data": table.extract(),
                        "image_path": str(page_image_path) if page_image_path else None,
                    })

        return {"source": pdf_path.name, "tables": tables}

    def _save_page_image(self, page, page_num, pdf_stem) -> Path | None:
        """Save full page as image."""
        try:
            img = page.to_image(resolution=150)
            image_path = self.images_dir / f"{pdf_stem}_p{page_num}.png"
            img.save(image_path)
            return image_path
        except Exception as e:
            print(f"Warning: Could not save page image: {e}")
            return None


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m pdf_pipeline.extractors.table_extractor <pdf_path>")
        sys.exit(1)

    config.create_output_dirs()
    extractor = TableExtractor()
    output_path = extractor.run(Path(sys.argv[1]))
    print(f"Tables extracted to: {output_path}")
