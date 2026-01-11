"""Table enricher - extracts structured table data from images using LLM."""
import base64
import json
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage

from pdf_pipeline.base import BaseEnricher
from pdf_pipeline import config
from pdf_pipeline.models import get_default_provider


class TableEnricher(BaseEnricher):
    """Extract structured table data from images using LLM."""

    def __init__(self, output_dir: Path = None):
        output_dir = output_dir or config.ENRICHED_TABLES_DIR
        super().__init__(output_dir)
        self.provider = get_default_provider()

    def enrich(self, data: dict[str, Any]) -> dict[str, Any]:
        """Process only tables that have existing image files."""
        enriched_tables = []
        skipped = 0
        source = data.get("source", "unknown")
        pdf_stem = Path(source).stem

        for table in data.get("tables", []):
            page = table.get("page", 0)
            table_idx = table.get("table_index", 0)
            image_path = config.IMAGES_TABLES_DIR / f"{pdf_stem}_p{page}_t{table_idx}.png"

            if not image_path.exists():
                skipped += 1
                continue

            enriched = self._extract_table_data(image_path, table)
            enriched_tables.append(enriched)

        if skipped > 0:
            print(f"  Skipped {skipped} tables (no image)")
        print(f"  Processed {len(enriched_tables)} tables")

        return {"source": source, "tables": enriched_tables}

    def _extract_table_data(self, image_path: Path, raw_table: dict) -> dict[str, Any]:
        """Extract structured table data from image using LLM."""
        try:
            llm = self.provider.get_llm()

            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            prompt = """Extract the complete table data from this image. This will be used for semantic search embeddings.

Return a JSON object with:
1. "title": The table title/caption (if visible, otherwise describe what the table is about)
2. "column_headers": Array of column header names
3. "rows": Array of row objects, where each row has the column header as key and cell value as value

Rules:
- Skip completely empty rows
- For merged cells spanning multiple rows, repeat the value in each row
- Clean up any OCR artifacts or formatting issues
- Make values searchable and meaningful

Example output format:
{
  "title": "MediShield Life Claim Limits",
  "column_headers": ["Category", "Type", "Claim Limit"],
  "rows": [
    {"Category": "Ward Charges", "Type": "Normal Ward", "Claim Limit": "$800/day"},
    {"Category": "Ward Charges", "Type": "ICU", "Claim Limit": "$1,800/day"}
  ]
}

Return ONLY valid JSON, no other text."""

            message = HumanMessage(content=[
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
            ])

            response = llm.invoke([message])
            content = response.content

            # Extract JSON
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                extracted = json.loads(content[start:end])
                return {
                    "page": raw_table.get("page"),
                    "table_index": raw_table.get("table_index"),
                    "bbox": raw_table.get("bbox"),
                    "image_path": str(image_path),
                    "title": extracted.get("title", ""),
                    "column_headers": extracted.get("column_headers", []),
                    "rows": extracted.get("rows", []),
                }

        except Exception as e:
            print(f"  LLM failed for {image_path.name}: {e}")

        # Fallback - return raw data
        return {
            "page": raw_table.get("page"),
            "table_index": raw_table.get("table_index"),
            "bbox": raw_table.get("bbox"),
            "image_path": str(image_path),
            "title": f"Table on page {raw_table.get('page')}",
            "column_headers": [],
            "rows": [],
        }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m pdf_pipeline.enrichers.table_enricher <input_json>")
        sys.exit(1)
    config.create_output_dirs()
    enricher = TableEnricher()
    output_path = enricher.run(Path(sys.argv[1]))
    print(f"Tables enriched to: {output_path}")
