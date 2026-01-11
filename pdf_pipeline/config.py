"""Configuration settings for the PDF extraction pipeline."""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR.parent / "data"
OUTPUT_DIR = BASE_DIR / "output"

# Output subdirectories
RAW_DIR = OUTPUT_DIR / "raw"
RAW_TABLES_DIR = RAW_DIR / "tables"
RAW_TEXT_DIR = RAW_DIR / "text"

ENRICHED_DIR = OUTPUT_DIR / "enriched"
ENRICHED_TABLES_DIR = ENRICHED_DIR / "tables"
ENRICHED_IMAGES_DIR = ENRICHED_DIR / "images"

IMAGES_DIR = OUTPUT_DIR / "images"
IMAGES_TABLES_DIR = IMAGES_DIR / "tables"
IMAGES_FIGURES_DIR = IMAGES_DIR / "figures"

NODES_DIR = OUTPUT_DIR / "nodes"
NODES_TABLES_DIR = NODES_DIR / "tables"
NODES_TABLES_GRANULAR_DIR = NODES_TABLES_DIR / "granular"
NODES_TABLES_FULL_DIR = NODES_TABLES_DIR / "full"
NODES_TEXT_DIR = NODES_DIR / "text"
NODES_TEXT_SECTIONS_DIR = NODES_TEXT_DIR / "sections"
NODES_TEXT_PARAGRAPHS_DIR = NODES_TEXT_DIR / "paragraphs"
NODES_TEXT_SENTENCES_DIR = NODES_TEXT_DIR / "sentences"
NODES_TEXT_IMAGES_DIR = NODES_TEXT_DIR / "images"

# =============================================================================
# API Keys (set via environment variables)
# =============================================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "pdf-pipeline")

# =============================================================================
# LLM Settings (for enrichment)
# =============================================================================
# LLM_PROVIDER options: "openai", "google", "anthropic", "ollama", "bedrock"
# LLM_MODEL examples:
#   openai:    "gpt-4o-mini", "gpt-4o", "gpt-4-turbo"
#   google:    "gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"
#   anthropic: "claude-3-haiku-20240307", "claude-3-sonnet-20240229"
#   ollama:    "llama3.2-vision", "llava"
#   bedrock:   "anthropic.claude-3-haiku-20240307-v1:0"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# =============================================================================
# Embedding Settings
# =============================================================================
# EMBEDDING_PROVIDER options: "openai", "google", "ollama", "bedrock", "huggingface"
# EMBEDDING_MODEL examples:
#   openai:      "text-embedding-3-small", "text-embedding-3-large"
#   google:      "models/embedding-001", "models/text-embedding-004"
#   ollama:      "nomic-embed-text", "mxbai-embed-large"
#   huggingface: "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_BATCH_SIZE = 100


def create_output_dirs():
    """Create all output directories if they don't exist."""
    dirs = [
        RAW_TABLES_DIR,
        RAW_TEXT_DIR,
        ENRICHED_TABLES_DIR,
        ENRICHED_IMAGES_DIR,
        IMAGES_TABLES_DIR,
        IMAGES_FIGURES_DIR,
        NODES_TABLES_GRANULAR_DIR,
        NODES_TABLES_FULL_DIR,
        NODES_TEXT_SECTIONS_DIR,
        NODES_TEXT_PARAGRAPHS_DIR,
        NODES_TEXT_SENTENCES_DIR,
        NODES_TEXT_IMAGES_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
