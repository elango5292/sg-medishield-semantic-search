"""
Table node builder - creates nodes from enriched table data.
"""
from pathlib import Path
from typing import Any

from pdf_pipeline.base import BaseNodeBuilder
from pdf_pipeline import config


class TableNodeBuilder(BaseNodeBuilder):
    """
    Build table nodes from enriched table data.
    
    Creates both granular (per-row) and full table nodes.
    """
    
    def __init__(
        self,
        granular_output_dir: Path = None,
        full_output_dir: Path = None,
    ):
        # Use granular dir as default output
        granular_output_dir = granular_output_dir or config.NODES_TABLES_GRANULAR_DIR
        super().__init__(granular_output_dir)
        
        self.granular_output_dir = granular_output_dir
        self.full_output_dir = full_output_dir or config.NODES_TABLES_FULL_DIR
        self.full_output_dir.mkdir(parents=True, exist_ok=True)
    
    def build_nodes(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Build all table nodes (granular only, full saved separately).
        
        Args:
            data: Enriched table data
            
        Returns:
            List of granular node dictionaries
        """
        granular_nodes = []
        full_nodes = []
        source = data.get("source", "unknown")
        
        for table in data.get("tables", []):
            # Build granular nodes (per row)
            table_granular = self._build_granular_nodes(table, source)
            granular_nodes.extend(table_granular)
            
            # Build full table node
            full_node = self._build_full_node(table, source)
            if full_node:
                full_nodes.append(full_node)
        
        # Save full nodes separately
        self._save_full_nodes(full_nodes, Path(source).stem)
        
        return granular_nodes
    
    def _build_granular_nodes(
        self,
        table: dict[str, Any],
        source: str,
    ) -> list[dict[str, Any]]:
        """
        Build one node per table row.
        """
        nodes = []
        enriched = table.get("enriched", {})
        raw_data = table.get("raw_data", [])
        
        title = enriched.get("title", "")
        column_headers = enriched.get("column_headers", [])
        page = table.get("page", 0)
        table_idx = table.get("table_index", 0)
        
        # Skip header row (index 0), process data rows
        for row_idx, row in enumerate(raw_data[1:], start=1):
            # Skip empty rows
            if all(not cell for cell in row):
                continue
            
            # Build text: "Title | Col1: Val1 | Col2: Val2 | ..."
            text_parts = [title] if title else []
            for col_idx, cell in enumerate(row):
                if col_idx < len(column_headers):
                    header = column_headers[col_idx]
                else:
                    header = f"Column_{col_idx}"
                text_parts.append(f"{header}: {cell or ''}")
            
            text = " | ".join(text_parts)
            
            node = {
                "id": f"table_p{page}_t{table_idx}_r{row_idx}",
                "text": text,
                "metadata": {
                    "source": source,
                    "page": page,
                    "table_index": table_idx,
                    "row_index": row_idx,
                    "table_title": title,
                    "column_headers": column_headers,
                    "node_type": "table_row",
                    "bbox": table.get("table_bbox"),
                },
            }
            nodes.append(node)
        
        return nodes
    
    def _build_full_node(
        self,
        table: dict[str, Any],
        source: str,
    ) -> dict[str, Any] | None:
        """
        Build a single node for the full table (markdown format).
        """
        enriched = table.get("enriched", {})
        raw_data = table.get("raw_data", [])
        
        if not raw_data:
            return None
        
        title = enriched.get("title", "")
        column_headers = enriched.get("column_headers", [])
        page = table.get("page", 0)
        table_idx = table.get("table_index", 0)
        
        # Build markdown table
        lines = []
        
        # Title
        if title:
            lines.append(f"## {title}")
            lines.append("")
        
        # Header row
        if column_headers:
            lines.append("| " + " | ".join(column_headers) + " |")
            lines.append("|" + "|".join(["---"] * len(column_headers)) + "|")
        
        # Data rows
        for row in raw_data[1:]:  # Skip header row
            if all(not cell for cell in row):
                continue
            cells = [str(cell or "") for cell in row]
            lines.append("| " + " | ".join(cells) + " |")
        
        text = "\n".join(lines)
        
        return {
            "id": f"table_p{page}_t{table_idx}_full",
            "text": text,
            "metadata": {
                "source": source,
                "page": page,
                "table_index": table_idx,
                "table_title": title,
                "node_type": "table_full",
                "bbox": table.get("table_bbox"),
            },
        }
    
    def _save_full_nodes(self, nodes: list[dict[str, Any]], filename: str) -> Path:
        """
        Save full table nodes to separate file.
        """
        import json
        output_path = self.full_output_dir / f"{filename}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(nodes, f, indent=2, ensure_ascii=False)
        return output_path


# CLI entry point
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m pdf_pipeline.node_builders.table_node_builder <input_json>")
        sys.exit(1)
    
    config.create_output_dirs()
    
    input_path = Path(sys.argv[1])
    builder = TableNodeBuilder()
    output_path = builder.run(input_path)
    print(f"Table nodes saved to: {output_path}")
