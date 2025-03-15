from qdrant_client import QdrantClient
from qdrant_client.http import models

# Connect to QDrant
client = QdrantClient(host="localhost", port=6333)

# Collection name
collection_name = "DnD_Documents"

# Delete the existing collection
print(f"Deleting collection '{collection_name}'...")
client.delete_collection(collection_name)

# Create a new collection with the correct dimension
print(f"Creating collection '{collection_name}' with dimension 384...")
client.create_collection(
    collection_name=collection_name,
    vectors_config=models.VectorParams(
        size=384,  # Dimension for 'all-MiniLM-L6-v2'
        distance=models.Distance.COSINE
    )
)

print(f"Collection '{collection_name}' recreated with dimension 384") 