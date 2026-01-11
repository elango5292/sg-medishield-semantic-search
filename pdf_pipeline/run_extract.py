"""
Run ONLY the extraction step (no LLM/embeddings required).

This is useful for running on a remote server, then downloading
the raw output to continue processing locally.

Usage:
    python -m pdf_pipeline.run_extract data/medishield.pdf

Output:
    - output/raw/tables/{filename}.json
    - output/raw/text/{filename}.json
    - output/images/tables/
    - output/images/figures/
"""
import sys
from pathlib import Path

from pdf_pipeline import config
from pdf_pipeline.extractors import TableExtractor, TextExtractor


def run_extract(pdf_path_str: str):
    """Run only extraction (no models needed)."""
    pdf_path = Path(pdf_path_str)
    
    print(f"Extracting: {pdf_path}")
    config.create_output_dirs()
    
    # Extract tables
    print("\n[1/2] Extracting tables (pdfplumber)...")
    table_extractor = TableExtractor()
    raw_tables_path = table_extractor.run(pdf_path)
    print(f"  -> {raw_tables_path}")
    
    # Extract text
    print("\n[2/2] Extracting text (unstructured)...")
    text_extractor = TextExtractor()
    raw_text_path = text_extractor.run(pdf_path)
    print(f"  -> {raw_text_path}")
    
    print("\n✓ Extraction complete!")
    print("\nDownload these to continue locally:")
    print(f"  - {config.RAW_DIR}/")
    print(f"  - {config.IMAGES_DIR}/")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    run_extract(sys.argv[1])
