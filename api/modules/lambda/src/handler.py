"""Lambda handler for MediShield semantic search API."""
import json
import os

from pinecone import Pinecone
from google import genai


# Initialize clients
pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
index = pc.Index(os.environ.get("PINECONE_INDEX_NAME", "medishield-pdf-pipeline"))

genai_client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))


def get_embedding(text: str) -> list[float]:
    """Generate embedding for query text."""
    response = genai_client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=text,
        config={"output_dimensionality": 1536},
    )
    return response.embeddings[0].values


def search(query: str, namespace: str = "sentences", top_k: int = 10) -> list[dict]:
    """Search Pinecone index."""
    embedding = get_embedding(query)
    
    results = index.query(
        vector=embedding,
        namespace=namespace,
        top_k=top_k,
        include_metadata=True,
    )
    
    return [
        {
            "id": match.id,
            "score": match.score,
            "text": match.metadata.get("text", ""),
            "page": match.metadata.get("page"),
            "node_type": match.metadata.get("node_type"),
            "coordinates": match.metadata.get("coordinates"),
        }
        for match in results.matches
    ]


def lambda_handler(event, context):
    """Lambda entry point."""
    path = event.get("rawPath", "")
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    
    # Health check
    if path == "/health" and method == "GET":
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"status": "healthy"}),
        }
    
    # Search endpoint
    if path == "/search" and method == "POST":
        try:
            body = json.loads(event.get("body", "{}"))
            query = body.get("query", "")
            namespace = body.get("namespace", "sentences")
            top_k = body.get("top_k", 10)
            
            if not query:
                return {
                    "statusCode": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "query is required"}),
                }
            
            results = search(query, namespace, top_k)
            
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"results": results}),
            }
        except Exception as e:
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": str(e)}),
            }
    
    return {
        "statusCode": 404,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": "Not found"}),
    }
