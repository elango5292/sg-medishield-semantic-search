"""Table enricher - adds title and column descriptions to tables."""
import base64
import json
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage

from pdf_pipeline.base import BaseEnricher
from pdf_pipeline import config
from pdf_pipeline.models import ModelProvider, get_default_provider, ModelConfig


class TableEnricher(BaseEnricher):
    """Enrich tables with title and column descriptions using LLM."""

    def __init__(
        self,
        output_dir: Path = None,
        model_provider: ModelProvider = None,
        llm_config: ModelConfig = None,
        use_llm: bool = True,
    ):
        output_dir = output_dir or config.ENRICHED_TABLES_DIR
        super().__init__(output_dir)
        self.use_llm = use_llm

        if model_provider:
            self.provider = model_provider
        elif llm_config:
            self.provider = ModelProvider(llm_config=llm_config)
        else:
            self.provider = get_default_provider()

    def enrich(self, data: dict[str, Any]) -> dict[str, Any]:
        """Enrich all tables in the data."""
        enriched_tables = []
        for table in data.get("tables", []):
            enriched_tables.append(self._enrich_table(table))
        return {"source": data.get("source"), "tables": enriched_tables}

    def _enrich_table(self, table: dict[str, Any]) -> dict[str, Any]:
        """Enrich a single table with metadata."""
        enriched = dict(table)
        if self.use_llm and table.get("image_path"):
            enriched["enriched"] = self._enrich_with_llm(table)
        else:
            enriched["enriched"] = self._enrich_with_heuristics(table)
        return enriched

    def _enrich_with_llm(self, table: dict[str, Any]) -> dict[str, Any]:
        """Use multimodal LLM to extract table metadata."""
        image_path = Path(table["image_path"])
        if not image_path.exists():
            return self._enrich_with_heuristics(table)

        try:
            llm = self.provider.get_llm()
            if not llm:
                return self._enrich_with_heuristics(table)

            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            message = HumanMessage(content=[
                {"type": "text", "text": """Analyze this table image and provide:
1. A descriptive title for the table
2. The column headers (list them)
3. A brief description of what each column contains

Respond in JSON format only:
{"title": "...", "column_headers": ["col1", "col2", ...], "column_descriptions": {"col1": "description", ...}}"""},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
            ])

            response = llm.invoke([message])
            content = response.content

            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(content[start:end])
                result["enrichment_method"] = "llm"
                return result

        except Exception as e:
            print(f"LLM enrichment failed: {e}")

        return self._enrich_with_heuristics(table)

    def _enrich_with_heuristics(self, table: dict[str, Any]) -> dict[str, Any]:
        """Use heuristics to extract table metadata (first row as headers)."""
        # Support both "data" (new) and "raw_data" (old) keys
        raw_data = table.get("data") or table.get("raw_data") or []

        column_headers = []
        if raw_data:
            column_headers = [str(h) if h else f"Column_{i}" for i, h in enumerate(raw_data[0])]

        return {
            "title": f"Table on page {table.get('page', '?')}",
            "column_headers": column_headers,
            "column_descriptions": {},
            "enrichment_method": "heuristics",
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
