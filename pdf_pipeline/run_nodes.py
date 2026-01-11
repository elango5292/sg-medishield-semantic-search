"""
Run ONLY node building from enriched output. No LLM calls.

Usage:
    python -m pdf_pipeline.run_nodes medishield
"""
import sys
import argparse
from pathlib import Path

from pdf_pipeline import config
from pdf_pipeline.node_builders import TableNodeBuilder, TextNodeBuilder


def run_nodes(filename: str):
    """Build nodes from enriched output. No LLM calls."""
    
    print(f"Building nodes for: {filename}")
    config.create_output_dirs()
    
    enriched_tables_path = config.ENRICHED_TABLES_DIR / f"{filename}.json"
    enriched_images_path = config.ENRICHED_IMAGES_DIR / f"{filename}.json"
    raw_text_path = config.RAW_TEXT_DIR / f"{filename}.json"
    
    if not enriched_tables_path.exists():
        print(f"Error: {enriched_tables_path} not found. Run enrich first.")
        sys.exit(1)
    if not raw_text_path.exists():
        print(f"Error: {raw_text_path} not found")
        sys.exit(1)
    
    print("\n[1/2] Building table nodes...")
    table_node_builder = TableNodeBuilder()
    table_nodes_path = table_node_builder.run(enriched_tables_path)
    print(f"  -> Granular: {table_nodes_path}")
    print(f"  -> Full: {config.NODES_TABLES_FULL_DIR / f'{filename}.json'}")
    
    print("\n[2/2] Building text nodes...")
    text_node_builder = TextNodeBuilder()
    if enriched_images_path.exists():
        text_node_builder.load_enriched_images(enriched_images_path)
    text_nodes_path = text_node_builder.run(raw_text_path)
    print(f"  -> Sections: {text_nodes_path}")
    print(f"  -> Paragraphs: {config.NODES_TEXT_PARAGRAPHS_DIR / f'{filename}.json'}")
    print(f"  -> Sentences: {config.NODES_TEXT_SENTENCES_DIR / f'{filename}.json'}")
    print(f"  -> Images: {config.NODES_TEXT_IMAGES_DIR / f'{filename}.json'}")
    
    print("\n✓ Node building complete!")
    print(f"\nNext step: python -m pdf_pipeline.run_embed {filename}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build nodes from enriched data (no LLM)")
    parser.add_argument("filename", help="Filename (without extension)")
    args = parser.parse_args()
    run_nodes(args.filename)
