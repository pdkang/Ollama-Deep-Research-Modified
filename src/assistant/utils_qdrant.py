# src/assistant/utils_qdrant.py
import os
import importlib
from langsmith import traceable
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer

# Global variable to store the model
_embeddings_model = None

@traceable
def setup_qdrant_client(collection_name="DnD_Documents"):
    """Set up and return a QdrantClient instance."""
    host = os.getenv("QDRANT_HOST", "localhost")
    port = int(os.getenv("QDRANT_PORT", "6333"))
    
    client = QdrantClient(host=host, port=port)
    return client

@traceable
def get_embeddings_model(force_reload=False):
    """Get the embeddings model."""
    global _embeddings_model
    
    # If model is already loaded and we don't need to force reload, return it
    if _embeddings_model is not None and not force_reload:
        return _embeddings_model
    
    # Load the model
    model_name = os.getenv("EMBEDDINGS_MODEL", "all-MiniLM-L6-v2")
    print(f"Loading embedding model: {model_name}")
    _embeddings_model = SentenceTransformer(model_name)
    
    # Ensure normalization is enabled
    _embeddings_model.encode_kwargs = {'normalize_embeddings': True}
    
    return _embeddings_model

@traceable
def query_qdrant(query, collection_name="DnD_Documents", top_k=5):
    """Query the QDrant vector store with the given query."""
    try:
        print(f"Querying QDrant with: '{query}'")
        
        # Get client and embeddings
        client = setup_qdrant_client(collection_name)
        
        # Create a new model instance every time to ensure correct dimensions
        model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Create embedding for query
        query_vector = model.encode(query, normalize_embeddings=True).tolist()
        
        # Search
        search_results = client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=top_k
        )
        
        # Format results
        results = []
        for result in search_results:
            # Extract data
            payload = result.payload
            title = payload.get("title", "Untitled Document")
            url = payload.get("source", "local")
            content = payload.get("content", "")
            
            # Create result entry
            result_entry = {
                "title": title,
                "url": url,
                "content": content[:200] + "...",  # Short preview
                "raw_content": content,
                "score": result.score
            }
            results.append(result_entry)
            print(f"Result: {title} (score: {result.score})")
        
        return {"results": results}
    except Exception as e:
        import traceback
        print(f"Error in QDrant search: {str(e)}")
        print(traceback.format_exc())
        return {"results": []}