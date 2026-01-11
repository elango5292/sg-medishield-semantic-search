"""
Airflow DAG for the PDF extraction pipeline.
"""
from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator

# Import pipeline components
from pdf_pipeline import config
from pdf_pipeline.extractors import TableExtractor, TextExtractor
from pdf_pipeline.enrichers import TableEnricher, ImageEnricher
from pdf_pipeline.node_builders import TableNodeBuilder, TextNodeBuilder
from pdf_pipeline.embedders import OpenAIEmbedder
from pdf_pipeline.indexers import PineconeIndexer


# Default args
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
}


def run_table_extractor(**context):
    """Extract tables from PDF."""
    pdf_path = context["dag_run"].conf.get("pdf_path")
    config.create_output_dirs()
    extractor = TableExtractor()
    output_path = extractor.run(pdf_path)
    return str(output_path)


def run_text_extractor(**context):
    """Extract text from PDF."""
    pdf_path = context["dag_run"].conf.get("pdf_path")
    config.create_output_dirs()
    extractor = TextExtractor()
    output_path = extractor.run(pdf_path)
    return str(output_path)


def run_table_enricher(**context):
    """Enrich tables with metadata."""
    raw_tables_path = context["ti"].xcom_pull(task_ids="extract_tables")
    enricher = TableEnricher()
    output_path = enricher.run(raw_tables_path)
    return str(output_path)


def run_image_enricher(**context):
    """Enrich images with metadata."""
    raw_text_path = context["ti"].xcom_pull(task_ids="extract_text")
    enricher = ImageEnricher()
    output_path = enricher.run(raw_text_path)
    return str(output_path)


def run_table_node_builder(**context):
    """Build table nodes."""
    enriched_tables_path = context["ti"].xcom_pull(task_ids="enrich_tables")
    builder = TableNodeBuilder()
    output_path = builder.run(enriched_tables_path)
    return str(output_path)


def run_text_node_builder(**context):
    """Build text nodes."""
    raw_text_path = context["ti"].xcom_pull(task_ids="extract_text")
    enriched_images_path = context["ti"].xcom_pull(task_ids="enrich_images")
    
    builder = TextNodeBuilder()
    builder.load_enriched_images(Path(enriched_images_path))
    output_path = builder.run(raw_text_path)
    return str(output_path)


def run_embedder(**context):
    """Add embeddings to all nodes."""
    embedder = OpenAIEmbedder()
    
    # Get filename from PDF path
    pdf_path = context["dag_run"].conf.get("pdf_path")
    filename = Path(pdf_path).stem
    
    # Embed all node directories
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
    
    return "Embeddings complete"


def run_pinecone_indexer(**context):
    """Index nodes to Pinecone."""
    indexer = PineconeIndexer()
    
    # Get filename from PDF path
    pdf_path = context["dag_run"].conf.get("pdf_path")
    filename = Path(pdf_path).stem
    
    # Index with namespaces
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
            total += count
    
    return f"Indexed {total} vectors"


# Define DAG
with DAG(
    "pdf_extraction_pipeline",
    default_args=default_args,
    description="Extract, enrich, and index PDF content",
    schedule_interval=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["pdf", "extraction", "pinecone"],
) as dag:
    
    # Extractors (parallel)
    extract_tables = PythonOperator(
        task_id="extract_tables",
        python_callable=run_table_extractor,
    )
    
    extract_text = PythonOperator(
        task_id="extract_text",
        python_callable=run_text_extractor,
    )
    
    # Enrichers
    enrich_tables = PythonOperator(
        task_id="enrich_tables",
        python_callable=run_table_enricher,
    )
    
    enrich_images = PythonOperator(
        task_id="enrich_images",
        python_callable=run_image_enricher,
    )
    
    # Node Builders
    build_table_nodes = PythonOperator(
        task_id="build_table_nodes",
        python_callable=run_table_node_builder,
    )
    
    build_text_nodes = PythonOperator(
        task_id="build_text_nodes",
        python_callable=run_text_node_builder,
    )
    
    # Embedder
    embed_nodes = PythonOperator(
        task_id="embed_nodes",
        python_callable=run_embedder,
    )
    
    # Indexer
    index_to_pinecone = PythonOperator(
        task_id="index_to_pinecone",
        python_callable=run_pinecone_indexer,
    )
    
    # Define flow
    extract_tables >> enrich_tables >> build_table_nodes
    extract_text >> enrich_images >> build_text_nodes
    [build_table_nodes, build_text_nodes] >> embed_nodes >> index_to_pinecone
