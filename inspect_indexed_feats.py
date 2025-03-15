from qdrant_client import QdrantClient

# Connect to QDrant
client = QdrantClient(host="localhost", port=6333)

# Collection name
collection_name = "DnD_Documents"

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
        print(f"Title: {point.payload.get('title', 'Untitled')}")
        content = point.payload.get('content', '')
        print(f"Content preview: {content[:200]}..." if len(content) > 200 else f"Content: {content}")
    else:
        print("No payload") 