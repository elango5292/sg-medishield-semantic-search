"""
Run ONLY the embedding step on nodes.

Usage:
    python -m pdf_pipeline.run_embed medishield

    # With custom embedding model
    python -m pdf_pipeline.run_embed medishield --provider google --model models/embedding-001
"""
import sys
import argparse
from pathlib import Path

from pdf_pipeline import config
from pdf_pipeline.embedders import LangChainEmbedder
from pdf_pipeline.models import ModelProvider, ModelConfig, set_default_provider


def run_embed(
    filename: str,
    embedding_provider: str = None,
    embedding_model: str = None,
):
    """Run embedding on all node files."""
    
    print(f"Embedding nodes for: {filename}")
    
    # Setup model provider
    if embedding_provider or embedding_model:
        provider = ModelProvider(
            embedding_config=ModelConfig(
                provider=embedding_provider or config.EMBEDDING_PROVIDER,
                model_name=embedding_model or config.EMBEDDING_MODEL,
            )
        )
        set_default_provider(provider)
        print(f"Using: {embedding_provider or config.EMBEDDING_PROVIDER}/{embedding_model or config.EMBEDDING_MODEL}")
    
    embedder = LangChainEmbedder()
    
    node_dirs = [
        config.NODES_TABLES_GRANULAR_DIR,
        config.NODES_TABLES_FULL_DIR,
        config.NODES_TEXT_SECTIONS_DIR,
        config.NODES_TEXT_PARAGRAPHS_DIR,
        config.NODES_TEXT_SENTENCES_DIR,
        config.NODES_TEXT_IMAGES_DIR,
    ]
    
    for node_dir in node_dirs:
        json_file = node_dir / f"{filename}.json"
        if json_file.exists():
            embedder.run(json_file)
            print(f"  -> Embedded: {json_file}")
        else:
            print(f"  -> Skipped (not found): {json_file}")
    
    print("\n✓ Embedding complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run embedding on nodes")
    parser.add_argument("filename", help="Filename (without extension) e.g. 'medishield'")
    parser.add_argument("--provider", help="Embedding provider (openai, google, ollama)")
    parser.add_argument("--model", help="Embedding model name")
    
    args = parser.parse_args()
    
    run_embed(args.filename, args.provider, args.model)
