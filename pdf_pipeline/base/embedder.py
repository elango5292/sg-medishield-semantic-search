"""
Base class for embedders.
"""
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseEmbedder(ABC):
    """
    Base class for embedders.
    
    Embedders add vector embeddings to nodes.
    """
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
    
    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embedding vectors
        """
        pass
    
    def load_nodes(self, input_path: Path) -> list[dict[str, Any]]:
        """
        Load nodes from JSON file.
        
        Args:
            input_path: Path to input JSON file
            
        Returns:
            List of node dictionaries
        """
        with open(input_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def save_nodes(self, nodes: list[dict[str, Any]], output_path: Path) -> Path:
        """
        Save nodes with embeddings to JSON file.
        
        Args:
            nodes: List of node dictionaries with embeddings
            output_path: Path to output JSON file
            
        Returns:
            Path to saved file
        """
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(nodes, f, indent=2, ensure_ascii=False)
        return output_path
    
    def embed_nodes(self, nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Add embeddings to nodes.
        
        Args:
            nodes: List of node dictionaries
            
        Returns:
            Nodes with embeddings added
        """
        import time
        
        # Filter nodes that need embeddings
        nodes_to_embed = [n for n in nodes if "embedding" not in n]
        
        if not nodes_to_embed:
            return nodes
        
        # Extract texts
        texts = [n["text"] for n in nodes_to_embed]
        
        # Embed in batches with retry and delay
        all_embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            
            # Retry with backoff
            for attempt in range(5):
                try:
                    embeddings = self.embed_texts(batch)
                    all_embeddings.extend(embeddings)
                    break
                except Exception as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        wait_time = 30 * (attempt + 1)
                        print(f"    Rate limited, waiting {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        raise
            
            # Progress
            print(f"    Embedded {min(i + self.batch_size, len(texts))}/{len(texts)}")
            
            # Delay between batches
            if i + self.batch_size < len(texts):
                time.sleep(2)
        
        # Add embeddings to nodes
        for node, embedding in zip(nodes_to_embed, all_embeddings):
            node["embedding"] = embedding
        
        return nodes
    
    def run(self, input_path: Path, output_path: Path = None) -> Path:
        """
        Run embedding and save output.
        
        Args:
            input_path: Path to input JSON file
            output_path: Path to output JSON file (defaults to input path)
            
        Returns:
            Path to saved JSON file
        """
        input_path = Path(input_path)
        output_path = Path(output_path) if output_path else input_path
        
        nodes = self.load_nodes(input_path)
        nodes = self.embed_nodes(nodes)
        return self.save_nodes(nodes, output_path)
