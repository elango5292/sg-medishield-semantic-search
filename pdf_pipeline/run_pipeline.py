"""
Simple script to run the full PDF extraction pipeline.
"""
import sys
from pathlib import Path

from pdf_pipeline import config
from pdf_pipeline.extractors import TableExtractor, TextExtractor
from pdf_pipeline.enrichers import TableEnricher, ImageEnricher
from pdf_pipeline.node_builders import TableNodeBuilder, TextNodeBuilder
from pdf_pipeline.embedders import LangChainEmbedder
from pdf_pipeline.indexers import PineconeIndexer
from pdf_pipeline.models import ModelProvider, ModelConfig, set_default_provider


def run_pipeline(
    pdf_path_str: str,
    skip_embedding: bool = False,
    skip_indexing: bool = False,
    llm_provider: str = None,
    llm_model: str = None,
    embedding_provider: str = None,
    embedding_model: str = None,
):
    """
    Run the full PDF extraction pipeline.
    
    Args:
        pdf_path_str: Path to the PDF file
        skip_embedding: Skip embedding step
        skip_indexing: Skip indexing step
        llm_provider: LLM provider (openai, google, anthropic, ollama)
        llm_model: LLM model name
        embedding_provider: Embedding provider
        embedding_model: Embedding model name
    """
    pdf_path = Path(pdf_path_str)
    filename = pdf_path.stem
    
    print(f"Processing: {pdf_path}")
    
    # Create output directories
    config.create_output_dirs()
    
    # Setup model provider if custom models specified
    if llm_provider or embedding_provider:
        provider = ModelProvider(
            llm_config=ModelConfig(
                provider=llm_provider or config.LLM_PROVIDER,
                model_name=llm_model or config.LLM_MODEL,
            ) if llm_provider or llm_model else None,
            embedding_config=ModelConfig(
                provider=embedding_provider or config.EMBEDDING_PROVIDER,
                model_name=embedding_model or config.EMBEDDING_MODEL,
            ) if embedding_provider or embedding_model else None,
        )
        set_default_provider(provider)
        print(f"Using LLM: {llm_provider or config.LLM_PROVIDER}/{llm_model or config.LLM_MODEL}")
        print(f"Using Embeddings: {embedding_provider or config.EMBEDDING_PROVIDER}/{embedding_model or config.EMBEDDING_MODEL}")
    
    # Step 1: Extract tables and text
    print("\n[1/6] Extracting tables...")
    table_extractor = TableExtractor()
    raw_tables_path = table_extractor.run(pdf_path)
    print(f"  -> {raw_tables_path}")
    
    print("\n[2/6] Extracting text...")
    text_extractor = TextExtractor()
    raw_text_path = text_extractor.run(pdf_path)
    print(f"  -> {raw_text_path}")
    
    # Step 2: Enrich data
    print("\n[3/6] Enriching tables...")
    table_enricher = TableEnricher()
    enriched_tables_path = table_enricher.run(raw_tables_path)
    print(f"  -> {enriched_tables_path}")
    
    print("\n[4/6] Enriching images...")
    image_enricher = ImageEnricher()
    enriched_images_path = image_enricher.run(raw_text_path)
    print(f"  -> {enriched_images_path}")
    
    # Step 3: Build nodes
    print("\n[5/6] Building table nodes...")
    table_node_builder = TableNodeBuilder()
    table_nodes_path = table_node_builder.run(enriched_tables_path)
    print(f"  -> Granular: {table_nodes_path}")
    print(f"  -> Full: {config.NODES_TABLES_FULL_DIR / f'{filename}.json'}")
    
    print("\n[6/6] Building text nodes...")
    text_node_builder = TextNodeBuilder()
    text_node_builder.load_enriched_images(enriched_images_path)
    text_nodes_path = text_node_builder.run(raw_text_path)
    print(f"  -> Sections: {text_nodes_path}")
    print(f"  -> Paragraphs: {config.NODES_TEXT_PARAGRAPHS_DIR / f'{filename}.json'}")
    print(f"  -> Sentences: {config.NODES_TEXT_SENTENCES_DIR / f'{filename}.json'}")
    print(f"  -> Images: {config.NODES_TEXT_IMAGES_DIR / f'{filename}.json'}")
    
    if skip_embedding:
        print("\n[Skipping embedding]")
    else:
        print("\n[7/8] Adding embeddings...")
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
    
    if skip_indexing:
        print("\n[Skipping indexing]")
    else:
        print("\n[8/8] Indexing to Pinecone...")
        indexer = PineconeIndexer()
        
        namespaces = {
            config.NODES_TABLES_GRANULAR_DIR: "table_rows",
            config.NODES_TABLES_FULL_DIR: "table_full",
            config.NODES_TEXT_SECTIONS_DIR: "sections",
            config.NODES_TEXT_PARAGRAPHS_DIR: "paragraphs",
            config.NODES_TEXT_SENTENCES_DIR: "sentences",
            config.NODES_TEXT_IMAGES_DIR: "images",
        }
        
        for node_dir, namespace in namespaces.items():
            json_file = node_dir / f"{filename}.json"
            if json_file.exists():
                count = indexer.run(json_file, namespace)
                print(f"  -> Indexed {count} vectors to '{namespace}'")
    
    print("\n✓ Pipeline complete!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run PDF extraction pipeline")
    parser.add_argument("pdf_path", help="Path to PDF file")
    parser.add_argument("--skip-embedding", action="store_true", help="Skip embedding step")
    parser.add_argument("--skip-indexing", action="store_true", help="Skip indexing step")
    parser.add_argument("--llm-provider", help="LLM provider (openai, google, anthropic, ollama)")
    parser.add_argument("--llm-model", help="LLM model name")
    parser.add_argument("--embedding-provider", help="Embedding provider")
    parser.add_argument("--embedding-model", help="Embedding model name")
    
    args = parser.parse_args()
    
    run_pipeline(
        args.pdf_path,
        skip_embedding=args.skip_embedding,
        skip_indexing=args.skip_indexing,
        llm_provider=args.llm_provider,
        llm_model=args.llm_model,
        embedding_provider=args.embedding_provider,
        embedding_model=args.embedding_model,
    )
