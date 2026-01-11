"""Table node builder - creates nodes from enriched table data."""
from pathlib import Path
from typing import Any
import json

from pdf_pipeline.base import BaseNodeBuilder
from pdf_pipeline import config


class TableNodeBuilder(BaseNodeBuilder):
    """Build table nodes from enriched table data."""

    def __init__(self, granular_output_dir: Path = None, full_output_dir: Path = None):
        granular_output_dir = granular_output_dir or config.NODES_TABLES_GRANULAR_DIR
        super().__init__(granular_output_dir)
        self.granular_output_dir = granular_output_dir
        self.full_output_dir = full_output_dir or config.NODES_TABLES_FULL_DIR
        self.full_output_dir.mkdir(parents=True, exist_ok=True)

    def build_nodes(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Build all table nodes."""
        granular_nodes = []
        full_nodes = []
        source = data.get("source", "unknown")

        for table in data.get("tables", []):
            granular_nodes.extend(self._build_granular_nodes(table, source))
            full_node = self._build_full_node(table, source)
            if full_node:
                full_nodes.append(full_node)

        self._save_full_nodes(full_nodes, Path(source).stem)
        return granular_nodes

    def _build_granular_nodes(self, table: dict[str, Any], source: str) -> list[dict[str, Any]]:
        """Build one node per table row."""
        nodes = []
        enriched = table.get("enriched", {})
        # Support both "data" (new) and "raw_data" (old) keys
        raw_data = table.get("data") or table.get("raw_data") or []

        title = enriched.get("title", "")
        column_headers = enriched.get("column_headers", [])
        page = table.get("page", 0)
        table_idx = table.get("table_index", 0)

        # Skip header row (index 0), process data rows
        for row_idx, row in enumerate(raw_data[1:], start=1):
            if all(not cell for cell in row):
                continue

            # Build text: "Title | Col1: Val1 | Col2: Val2 | ..."
            text_parts = [title] if title else []
            for col_idx, cell in enumerate(row):
                header = column_headers[col_idx] if col_idx < len(column_headers) else f"Column_{col_idx}"
                text_parts.append(f"{header}: {cell or ''}")

            nodes.append({
                "id": f"table_p{page}_t{table_idx}_r{row_idx}",
                "text": " | ".join(text_parts),
                "metadata": {
                    "source": source,
                    "page": page,
                    "table_index": table_idx,
                    "row_index": row_idx,
                    "table_title": title,
                    "column_headers": column_headers,
                    "node_type": "table_row",
                    "bbox": table.get("bbox"),
                },
            })

        return nodes

    def _build_full_node(self, table: dict[str, Any], source: str) -> dict[str, Any] | None:
        """Build a single node for the full table (markdown format)."""
        enriched = table.get("enriched", {})
        raw_data = table.get("data") or table.get("raw_data") or []

        if not raw_data:
            return None

        title = enriched.get("title", "")
        column_headers = enriched.get("column_headers", [])
        page = table.get("page", 0)
        table_idx = table.get("table_index", 0)

        lines = []
        if title:
            lines.append(f"## {title}")
            lines.append("")

        if column_headers:
            lines.append("| " + " | ".join(column_headers) + " |")
            lines.append("|" + "|".join(["---"] * len(column_headers)) + "|")

        for row in raw_data[1:]:
            if all(not cell for cell in row):
                continue
            cells = [str(cell or "") for cell in row]
            lines.append("| " + " | ".join(cells) + " |")

        return {
            "id": f"table_p{page}_t{table_idx}_full",
            "text": "\n".join(lines),
            "metadata": {
                "source": source,
                "page": page,
                "table_index": table_idx,
                "table_title": title,
                "node_type": "table_full",
                "bbox": table.get("bbox"),
            },
        }

    def _save_full_nodes(self, nodes: list[dict[str, Any]], filename: str) -> Path:
        """Save full table nodes to separate file."""
        output_path = self.full_output_dir / f"{filename}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(nodes, f, indent=2, ensure_ascii=False)
        return output_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m pdf_pipeline.node_builders.table_node_builder <input_json>")
        sys.exit(1)

    config.create_output_dirs()
    builder = TableNodeBuilder()
    output_path = builder.run(Path(sys.argv[1]))
    print(f"Table nodes saved to: {output_path}")
