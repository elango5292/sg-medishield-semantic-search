"""Text extractor using Unstructured."""
from pathlib import Path
from typing import Any

from unstructured.partition.pdf import partition_pdf

from pdf_pipeline.base import BaseExtractor
from pdf_pipeline import config


class TextExtractor(BaseExtractor):
    """Extract text and images from PDF using Unstructured."""

    def __init__(self, output_dir: Path = None, images_dir: Path = None):
        output_dir = output_dir or config.RAW_TEXT_DIR
        super().__init__(output_dir)
        self.images_dir = images_dir or config.IMAGES_FIGURES_DIR
        self.images_dir.mkdir(parents=True, exist_ok=True)

    def extract(self, pdf_path: Path) -> dict[str, Any]:
        """Extract all elements from a PDF."""
        pdf_path = Path(pdf_path)

        elements = partition_pdf(
            filename=str(pdf_path),
            strategy="hi_res",
            extract_images_in_pdf=True,
            extract_image_block_output_dir=str(self.images_dir),
            infer_table_structure=False,
        )

        # Just convert elements to dicts as-is
        return {
            "source": pdf_path.name,
            "elements": [el.to_dict() for el in elements],
        }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m pdf_pipeline.extractors.text_extractor <pdf_path>")
        sys.exit(1)

    config.create_output_dirs()
    extractor = TextExtractor()
    output_path = extractor.run(Path(sys.argv[1]))
    print(f"Text extracted to: {output_path}")
