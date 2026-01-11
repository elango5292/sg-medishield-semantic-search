"""
Run enrichment (LLM calls) on raw extraction output.

Usage:
    python -m pdf_pipeline.run_enrich medishield
    python -m pdf_pipeline.run_enrich medishield --dry-run
"""
import sys
import argparse
from pathlib import Path

from pdf_pipeline import config
from pdf_pipeline.enrichers import TableEnricher, ImageEnricher
from pdf_pipeline.models import ModelProvider, ModelConfig, set_default_provider


def count_files(directory: Path, pattern: str = "*") -> int:
    if not directory.exists():
        return 0
    return len(list(directory.glob(pattern)))


def run_enrich(filename: str, dry_run: bool = False):
    """Run enrichment from raw output using config settings."""
    
    print(f"Processing: {filename}")
    config.create_output_dirs()
    
    raw_tables_path = config.RAW_TABLES_DIR / f"{filename}.json"
    raw_text_path = config.RAW_TEXT_DIR / f"{filename}.json"
    
    if not raw_tables_path.exists():
        print(f"Error: {raw_tables_path} not found")
        sys.exit(1)
    if not raw_text_path.exists():
        print(f"Error: {raw_text_path} not found")
        sys.exit(1)
    
    table_images = count_files(config.IMAGES_TABLES_DIR, "*.png")
    figure_images = count_files(config.IMAGES_FIGURES_DIR, "*.jpg") + count_files(config.IMAGES_FIGURES_DIR, "*.png")
    
    print(f"\nFound:")
    print(f"  - {table_images} table images")
    print(f"  - {figure_images} figure images")
    print(f"  - Total LLM calls: {table_images + figure_images}")
    print(f"\nUsing: {config.LLM_PROVIDER}/{config.LLM_MODEL}")
    
    if dry_run:
        print("\n[DRY RUN] Run without --dry-run to execute.")
        return
    
    # Setup provider from config
    provider = ModelProvider(
        llm_config=ModelConfig(
            provider=config.LLM_PROVIDER,
            model_name=config.LLM_MODEL,
            api_key=config.GOOGLE_API_KEY if config.LLM_PROVIDER == "google" else config.OPENAI_API_KEY,
        )
    )
    set_default_provider(provider)
    
    print("\n[1/2] Enriching tables...")
    table_enricher = TableEnricher()
    enriched_tables_path = table_enricher.run(raw_tables_path)
    print(f"  -> {enriched_tables_path}")
    
    print("\n[2/2] Enriching images...")
    image_enricher = ImageEnricher()
    enriched_images_path = image_enricher.run(raw_text_path)
    print(f"  -> {enriched_images_path}")
    
    print("\n✓ Enrichment complete!")
    print(f"\nNext: python -m pdf_pipeline.run_nodes {filename}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run enrichment")
    parser.add_argument("filename", help="Filename (without extension)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed")
    args = parser.parse_args()
    run_enrich(args.filename, dry_run=args.dry_run)
