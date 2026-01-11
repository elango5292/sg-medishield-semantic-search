# PDF Extraction Pipeline

A modular pipeline for extracting tables and text from PDFs, enriching them with metadata, and indexing to Pinecone.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-key"

# Run with defaults (OpenAI)
python -m pdf_pipeline.run_pipeline data/medishield.pdf

# Skip embedding/indexing for testing
python -m pdf_pipeline.run_pipeline data/medishield.pdf --skip-embedding --skip-indexing
```

## Switching Models

### Via CLI

```bash
# Use Google Gemini for LLM
python -m pdf_pipeline.run_pipeline data/doc.pdf \
  --llm-provider google \
  --llm-model gemini-1.5-flash

# Use different embedding provider
python -m pdf_pipeline.run_pipeline data/doc.pdf \
  --embedding-provider google \
  --embedding-model models/embedding-001

# Mix providers
python -m pdf_pipeline.run_pipeline data/doc.pdf \
  --llm-provider anthropic \
  --llm-model claude-3-haiku-20240307 \
  --embedding-provider openai \
  --embedding-model text-embedding-3-small
```

### Via Environment Variables

```bash
export LLM_PROVIDER=google
export LLM_MODEL=gemini-1.5-flash
export EMBEDDING_PROVIDER=openai
export EMBEDDING_MODEL=text-embedding-3-small
export GOOGLE_API_KEY=your-key
export OPENAI_API_KEY=your-key
```

### Via Code

```python
from pdf_pipeline import (
    ModelProvider, ModelConfig, set_default_provider,
    TableEnricher, ImageEnricher, LangChainEmbedder
)

# Set pipeline-wide defaults
provider = ModelProvider(
    llm_config=ModelConfig("google", "gemini-1.5-flash"),
    embedding_config=ModelConfig("openai", "text-embedding-3-small"),
)
set_default_provider(provider)

# Or override per-component
table_enricher = TableEnricher(
    llm_config=ModelConfig("anthropic", "claude-3-haiku-20240307")
)

# Or pass a custom provider
custom_provider = ModelProvider(
    llm_config=ModelConfig("ollama", "llama3.2-vision")
)
image_enricher = ImageEnricher(model_provider=custom_provider)
```

## Supported Providers

| Provider | LLM | Embeddings | Package |
|----------|-----|------------|---------|
| OpenAI | ✅ | ✅ | `langchain-openai` |
| Google | ✅ | ✅ | `langchain-google-genai` |
| Anthropic | ✅ | ❌ | `langchain-anthropic` |
| Ollama | ✅ | ✅ | `langchain-ollama` |
| AWS Bedrock | ✅ | ✅ | `langchain-aws` |
| HuggingFace | ❌ | ✅ | `langchain-huggingface` |

## Architecture

```
PDF Input
    │
    ├── Extractors (raw JSON output)
    │   ├── TableExtractor (pdfplumber)
    │   └── TextExtractor (unstructured)
    │
    ├── Enrichers (add metadata) ← uses LLM
    │   ├── TableEnricher
    │   └── ImageEnricher
    │
    ├── Node Builders (create nodes)
    │   ├── TableNodeBuilder
    │   └── TextNodeBuilder
    │
    ├── Embedders ← uses Embedding model
    │   └── LangChainEmbedder
    │
    └── Indexers
        └── PineconeIndexer
```

## Output Structure

```
output/
├── raw/                    # Raw extractor outputs
│   ├── tables/
│   └── text/
├── enriched/               # Enriched data
│   ├── tables/
│   └── images/
├── images/                 # Cropped images
│   ├── tables/
│   └── figures/
└── nodes/                  # Final nodes
    ├── tables/
    │   ├── granular/
    │   └── full/
    └── text/
        ├── sections/
        ├── paragraphs/
        ├── sentences/
        └── images/
```

## Node Types

| Type | Description |
|------|-------------|
| `table_row` | One row from a table |
| `table_full` | Full table in markdown |
| `section` | Title + all paragraphs |
| `paragraph` | Single paragraph |
| `sentence` | Single sentence |
| `image` | Image with description |
