from qdrant_client import QdrantClient

# Connect to QDrant
client = QdrantClient(host="localhost", port=6333)

# Collection name
collection_name = "DnD_Documents"

# Get collection info
collection_info = client.get_collection(collection_name)
print(f"Collection info: {collection_info}")

# Get vector config
try:
    # For newer QDrant versions
    vector_config = collection_info.config.params.vectors
    print(f"Vector dimension: {vector_config.size}")
    print(f"Vector distance: {vector_config.distance}")
except AttributeError:
    # For older QDrant versions with named vectors
    vector_config = collection_info.config.params.vectors.get('')
    if vector_config:
        print(f"Vector dimension: {vector_config.size}")
        print(f"Vector distance: {vector_config.distance}")
    else:
        print("Could not determine vector configuration") 