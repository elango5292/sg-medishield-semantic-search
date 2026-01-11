"""
Embedder - adds embeddings to nodes using LangChain.
"""
from pathlib import Path
from typing import Any

from pdf_pipeline.base import BaseEmbedder
from pdf_pipeline.models import ModelProvider, get_default_provider, ModelConfig


class LangChainEmbedder(BaseEmbedder):
    """
    Add embeddings to nodes using LangChain embeddings.
    
    Supports any LangChain-compatible embedding provider.
    """
    
    def __init__(
        self,
        model_provider: ModelProvider = None,
        embedding_config: ModelConfig = None,
        batch_size: int = 100,
    ):
        super().__init__(batch_size)
        
        # Use provided provider, or create one with custom config, or use default
        if model_provider:
            self.provider = model_provider
        elif embedding_config:
            self.provider = ModelProvider(embedding_config=embedding_config)
        else:
            self.provider = get_default_provider()
    
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        embeddings_model = self.provider.get_embeddings()
        if not embeddings_model:
            raise ValueError("No embedding model configured")
        
        # Clean texts (remove empty strings)
        texts = [t if t else " " for t in texts]
        
        return embeddings_model.embed_documents(texts)
    
    def embed_directory(self, input_dir: Path, output_dir: Path = None) -> list[Path]:
        """Embed all JSON files in a directory."""
        input_dir = Path(input_dir)
        output_dir = Path(output_dir) if output_dir else input_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_paths = []
        for json_file in input_dir.glob("*.json"):
            output_path = output_dir / json_file.name
            self.run(json_file, output_path)
            output_paths.append(output_path)
        
        return output_paths


# Alias for backward compatibility
OpenAIEmbedder = LangChainEmbedder


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m pdf_pipeline.embedders.embedder <input_json_or_dir> [output_path]")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    
    embedder = LangChainEmbedder()
    
    if input_path.is_dir():
        output_paths = embedder.embed_directory(input_path, output_path)
        print(f"Embedded {len(output_paths)} files")
    else:
        result_path = embedder.run(input_path, output_path)
        print(f"Embeddings saved to: {result_path}")
