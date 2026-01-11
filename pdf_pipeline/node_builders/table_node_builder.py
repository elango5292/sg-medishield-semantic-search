"""Table node builder - creates nodes from LLM-extracted table data."""
from pathlib import Path
from typing import Any
import json

from pdf_pipeline.base import BaseNodeBuilder
from pdf_pipeline import config


class TableNodeBuilder(BaseNodeBuilder):
    """Build table nodes with coordinates for highlighting."""

    def __init__(self, granular_output_dir: Path = None, full_output_dir: Path = None):
        granular_output_dir = granular_output_dir or config.NODES_TABLES_GRANULAR_DIR
        super().__init__(granular_output_dir)
        self.full_output_dir = full_output_dir or config.NODES_TABLES_FULL_DIR
        self.full_output_dir.mkdir(parents=True, exist_ok=True)

    def build_nodes(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Build nodes from enriched table data."""
        granular_nodes = []
        full_nodes = []
        source = data.get("source", "unknown")

        for table in data.get("tables", []):
            if not table.get("rows"):
                continue

            granular_nodes.extend(self._build_row_nodes(table, source))
            full_node = self._build_full_node(table, source)
            if full_node:
                full_nodes.append(full_node)

        print(f"  Created {len(granular_nodes)} row nodes, {len(full_nodes)} full table nodes")
        self._save_full_nodes(full_nodes, Path(source).stem)
        return granular_nodes

    def _build_row_nodes(self, table: dict[str, Any], source: str) -> list[dict[str, Any]]:
        """Build one node per row with coordinates."""
        nodes = []
        title = table.get("title", "")
        headers = table.get("column_headers", [])
        page = table.get("page", 0)
        table_idx = table.get("table_index", 0)
        bbox = table.get("bbox")

        for row_idx, row in enumerate(table.get("rows", [])):
            parts = [title] if title else []
            for header in headers:
                value = row.get(header, "")
                if value:
                    parts.append(f"{header}: {value}")

            if len(parts) <= 1:
                continue

            nodes.append({
                "id": f"table_p{page}_t{table_idx}_r{row_idx}",
                "text": " | ".join(parts),
                "metadata": {
                    "source": source,
                    "page": page,
                    "table_index": table_idx,
                    "row_index": row_idx,
                    "table_title": title,
                    "node_type": "table_row",
                    "bbox": bbox,
                },
            })

        return nodes

    def _build_full_node(self, table: dict[str, Any], source: str) -> dict[str, Any] | None:
        """Build full table node with coordinates."""
        title = table.get("title", "")
        headers = table.get("column_headers", [])
        rows = table.get("rows", [])
        page = table.get("page", 0)
        table_idx = table.get("table_index", 0)
        bbox = table.get("bbox")

        if not rows:
            return None

        lines = []
        if title:
            lines.append(f"## {title}")
            lines.append("")

        if headers:
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("|" + "|".join(["---"] * len(headers)) + "|")

            for row in rows:
                cells = [str(row.get(h, "")) for h in headers]
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
                "bbox": bbox,
            },
        }

    def _save_full_nodes(self, nodes: list[dict[str, Any]], filename: str):
        output_path = self.full_output_dir / f"{filename}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(nodes, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m pdf_pipeline.node_builders.table_node_builder <input_json>")
        sys.exit(1)
    config.create_output_dirs()
    builder = TableNodeBuilder()
    output_path = builder.run(Path(sys.argv[1]))
    print(f"Table nodes saved to: {output_path}")
