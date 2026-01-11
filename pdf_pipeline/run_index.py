"""
Run ONLY the indexing step to Pinecone.

Usage:
    python -m pdf_pipeline.run_index medishield
"""
import sys
import argparse
from pathlib import Path

from pdf_pipeline import config
from pdf_pipeline.indexers import PineconeIndexer


def run_index(filename: str):
    """Index nodes to Pinecone."""
    
    print(f"Indexing nodes for: {filename}")
    
    indexer = PineconeIndexer()
    
    namespaces = {
        config.NODES_TABLES_GRANULAR_DIR: "table_rows",
        config.NODES_TABLES_FULL_DIR: "table_full",
        config.NODES_TEXT_SECTIONS_DIR: "sections",
        config.NODES_TEXT_PARAGRAPHS_DIR: "paragraphs",
        config.NODES_TEXT_SENTENCES_DIR: "sentences",
        config.NODES_TEXT_IMAGES_DIR: "images",
    }
    
    total = 0
    for node_dir, namespace in namespaces.items():
        json_file = node_dir / f"{filename}.json"
        if json_file.exists():
            count = indexer.run(json_file, namespace)
            print(f"  -> Indexed {count} vectors to '{namespace}'")
            total += count
        else:
            print(f"  -> Skipped (not found): {json_file}")
    
    print(f"\n✓ Indexed {total} total vectors!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index nodes to Pinecone")
    parser.add_argument("filename", help="Filename (without extension) e.g. 'medishield'")
    
    args = parser.parse_args()
    
    run_index(args.filename)
