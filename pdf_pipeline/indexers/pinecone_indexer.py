"""
Pinecone indexer - upserts nodes to Pinecone.
"""
from pathlib import Path
from typing import Any

from pinecone import Pinecone

from pdf_pipeline.base import BaseIndexer
from pdf_pipeline import config


class PineconeIndexer(BaseIndexer):
    """
    Upsert nodes with embeddings to Pinecone.
    """
    
    def __init__(
        self,
        index_name: str = None,
        batch_size: int = 100,
    ):
        super().__init__(batch_size)
        
        self.index_name = index_name or config.PINECONE_INDEX_NAME
        
        if config.PINECONE_API_KEY:
            self.pc = Pinecone(api_key=config.PINECONE_API_KEY)
            
            # Create index if it doesn't exist
            existing_indexes = [idx.name for idx in self.pc.list_indexes()]
            if self.index_name not in existing_indexes:
                print(f"Creating index '{self.index_name}'...")
                from pinecone import ServerlessSpec
                self.pc.create_index(
                    name=self.index_name,
                    dimension=config.EMBEDDING_DIMENSION,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                )
                # Wait for index to be ready
                import time
                while not self.pc.describe_index(self.index_name).status.ready:
                    time.sleep(1)
                print(f"Index '{self.index_name}' created!")
            
            self.index = self.pc.Index(self.index_name)
        else:
            self.pc = None
            self.index = None
    
    def upsert(self, nodes: list[dict[str, Any]], namespace: str = None) -> int:
        """
        Upsert nodes to Pinecone.
        
        Args:
            nodes: List of node dictionaries with embeddings
            namespace: Optional namespace for the vectors
            
        Returns:
            Number of vectors upserted
        """
        import json as json_lib
        
        if not self.index:
            raise ValueError("Pinecone not configured")
        
        # Filter nodes with embeddings
        nodes_with_embeddings = [n for n in nodes if "embedding" in n]
        
        if not nodes_with_embeddings:
            print("No nodes with embeddings to upsert")
            return 0
        
        # Prepare vectors for upsert
        vectors = []
        for node in nodes_with_embeddings:
            # Clean metadata - convert non-supported types to strings
            metadata = {}
            for k, v in node.get("metadata", {}).items():
                if isinstance(v, (list, dict)):
                    metadata[k] = json_lib.dumps(v)
                else:
                    metadata[k] = v
            metadata["text"] = node.get("text", "")[:1000]  # Truncate text
            
            vector = {
                "id": node["id"],
                "values": node["embedding"],
                "metadata": metadata,
            }
            vectors.append(vector)
        
        # Upsert in batches
        total_upserted = 0
        for i in range(0, len(vectors), self.batch_size):
            batch = vectors[i:i + self.batch_size]
            
            if namespace:
                self.index.upsert(vectors=batch, namespace=namespace)
            else:
                self.index.upsert(vectors=batch)
            
            total_upserted += len(batch)
            print(f"Upserted {total_upserted}/{len(vectors)} vectors")
        
        return total_upserted
    
    def upsert_directory(self, input_dir: Path, namespace: str = None) -> int:
        """
        Upsert all JSON files in a directory.
        
        Args:
            input_dir: Directory containing node JSON files with embeddings
            namespace: Optional namespace for the vectors
            
        Returns:
            Total number of vectors upserted
        """
        input_dir = Path(input_dir)
        total = 0
        
        for json_file in input_dir.glob("*.json"):
            count = self.run(json_file, namespace)
            total += count
        
        return total


# CLI entry point
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m pdf_pipeline.indexers.pinecone_indexer <input_json_or_dir> [namespace]")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    namespace = sys.argv[2] if len(sys.argv) > 2 else None
    
    indexer = PineconeIndexer()
    
    if input_path.is_dir():
        total = indexer.upsert_directory(input_path, namespace)
        print(f"Total vectors upserted: {total}")
    else:
        count = indexer.run(input_path, namespace)
        print(f"Vectors upserted: {count}")
