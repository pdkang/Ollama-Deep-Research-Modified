from qdrant_client import QdrantClient

# Connect to QDrant
client = QdrantClient(host="localhost", port=6333)

# Collection name
collection_name = "DnD_Documents"

# Get collection info
collection_info = client.get_collection(collection_name)
print(f"Collection info: {collection_info}")

# Get a sample of points
sample_size = 5
points = client.scroll(
    collection_name=collection_name,
    limit=sample_size
)[0]

print(f"\nSample of {len(points)} points from collection:")
for i, point in enumerate(points):
    print(f"\nPoint {i+1}:")
    print(f"ID: {point.id}")
    print(f"Vector dimensions: {len(point.vector) if point.vector else 'No vector'}")
    
    # Check payload
    if point.payload:
        print(f"Payload keys: {list(point.payload.keys())}")
        for key, value in point.payload.items():
            if isinstance(value, str):
                print(f"{key}: {value[:100]}..." if len(value) > 100 else f"{key}: {value}")
            else:
                print(f"{key}: {value}")
    else:
        print("No payload") 