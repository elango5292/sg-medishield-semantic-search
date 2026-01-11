"""
Run enrichment + node building from raw extraction output.

Use this after downloading raw output from remote extraction.

Usage:
    python -m pdf_pipeline.run_enrich medishield

    # With custom models
    python -m pdf_pipeline.run_enrich medishield --llm-provider google --llm-model gemini-1.5-flash

    # Skip LLM (use heuristics only)
    python -m pdf_pipeline.run_enrich medishield --no-llm
"""
import sys
import argparse
from pathlib import Path

from pdf_pipeline import config
from pdf_pipeline.enrichers import TableEnricher, ImageEnricher
from pdf_pipeline.node_builders import TableNodeBuilder, TextNodeBuilder
from pdf_pipeline.models import ModelProvider, ModelConfig, set_default_provider


def run_enrich(
    filename: str,
    use_llm: bool = True,
    llm_provider: str = None,
    llm_model: str = None,
):
    """Run enrichment and node building from raw output."""
    
    print(f"Processing: {filename}")
    config.create_output_dirs()
    
    # Setup model provider
    if llm_provider or llm_model:
        provider = ModelProvider(
            llm_config=ModelConfig(
                provider=llm_provider or config.LLM_PROVIDER,
                model_name=llm_model or config.LLM_MODEL,
            )
        )
        set_default_provider(provider)
        print(f"Using LLM: {llm_provider or config.LLM_PROVIDER}/{llm_model or config.LLM_MODEL}")
    
    # Check raw files exist
    raw_tables_path = config.RAW_TABLES_DIR / f"{filename}.json"
    raw_text_path = config.RAW_TEXT_DIR / f"{filename}.json"
    
    if not raw_tables_path.exists():
        print(f"Error: {raw_tables_path} not found")
        sys.exit(1)
    if not raw_text_path.exists():
        print(f"Error: {raw_text_path} not found")
        sys.exit(1)
    
    # Enrich tables
    print("\n[1/4] Enriching tables...")
    table_enricher = TableEnricher(use_llm=use_llm)
    enriched_tables_path = table_enricher.run(raw_tables_path)
    print(f"  -> {enriched_tables_path}")
    
    # Enrich images
    print("\n[2/4] Enriching images...")
    image_enricher = ImageEnricher(use_llm=use_llm)
    enriched_images_path = image_enricher.run(raw_text_path)
    print(f"  -> {enriched_images_path}")
    
    # Build table nodes
    print("\n[3/4] Building table nodes...")
    table_node_builder = TableNodeBuilder()
    table_nodes_path = table_node_builder.run(enriched_tables_path)
    print(f"  -> Granular: {table_nodes_path}")
    print(f"  -> Full: {config.NODES_TABLES_FULL_DIR / f'{filename}.json'}")
    
    # Build text nodes
    print("\n[4/4] Building text nodes...")
    text_node_builder = TextNodeBuilder()
    text_node_builder.load_enriched_images(enriched_images_path)
    text_nodes_path = text_node_builder.run(raw_text_path)
    print(f"  -> Sections: {text_nodes_path}")
    print(f"  -> Paragraphs: {config.NODES_TEXT_PARAGRAPHS_DIR / f'{filename}.json'}")
    print(f"  -> Sentences: {config.NODES_TEXT_SENTENCES_DIR / f'{filename}.json'}")
    print(f"  -> Images: {config.NODES_TEXT_IMAGES_DIR / f'{filename}.json'}")
    
    print("\n✓ Enrichment complete!")
    print(f"\nNodes ready at: {config.NODES_DIR}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run enrichment from raw output")
    parser.add_argument("filename", help="Filename (without extension) e.g. 'medishield'")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM, use heuristics only")
    parser.add_argument("--llm-provider", help="LLM provider (openai, google, anthropic, ollama)")
    parser.add_argument("--llm-model", help="LLM model name")
    
    args = parser.parse_args()
    
    run_enrich(
        args.filename,
        use_llm=not args.no_llm,
        llm_provider=args.llm_provider,
        llm_model=args.llm_model,
    )
