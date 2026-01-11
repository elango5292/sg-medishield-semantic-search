"""
PDF Extraction Pipeline

A modular pipeline for extracting tables and text from PDFs,
enriching them with metadata, and indexing to Pinecone.
"""
from pdf_pipeline import config
from pdf_pipeline.extractors import TableExtractor, TextExtractor
from pdf_pipeline.enrichers import TableEnricher, ImageEnricher
from pdf_pipeline.node_builders import TableNodeBuilder, TextNodeBuilder
from pdf_pipeline.embedders import LangChainEmbedder
from pdf_pipeline.indexers import PineconeIndexer
from pdf_pipeline.models import ModelProvider, ModelConfig, get_default_provider, set_default_provider

__all__ = [
    "config",
    "TableExtractor",
    "TextExtractor",
    "TableEnricher",
    "ImageEnricher",
    "TableNodeBuilder",
    "TextNodeBuilder",
    "LangChainEmbedder",
    "PineconeIndexer",
    "ModelProvider",
    "ModelConfig",
    "get_default_provider",
    "set_default_provider",
]
