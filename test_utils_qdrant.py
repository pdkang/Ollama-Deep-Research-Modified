from assistant.utils_qdrant import query_qdrant
from qdrant_client import QdrantClient

# First, check if the collection exists and has data
client = QdrantClient(host="localhost", port=6333)
collections = client.get_collections().collections
collection_names = [collection.name for collection in collections]

print(f"Available collections: {collection_names}")

collection_name = "DnD_Documents"
if collection_name in collection_names:
    collection_info = client.get_collection(collection_name)
    point_count = client.count(collection_name).count
    print(f"Collection '{collection_name}' info: {collection_info}")
    print(f"Number of points in collection: {point_count}")
else:
    print(f"Collection '{collection_name}' does not exist!")
    print("Please run load_dnd_feats.py first to create and populate the collection.")
    exit(1)

# Test queries
test_queries = [
    "What are the combat feats?",
    "Tell me about feats that improve spellcasting",
    "What feats are available for archers?",
    "Feats that improve strength",
    "Defensive feats"
]

for query in test_queries:
    print(f"\n\nTesting query: '{query}'")
    results = query_qdrant(query, collection_name=collection_name, top_k=3)
    
    if results and results.get("results"):
        print(f"Found {len(results['results'])} results")
        for i, result in enumerate(results["results"], 1):
            print(f"\nResult {i}:")
            print(f"Title: {result['title']}")
            print(f"Score: {result['score']}")
            print(f"Content preview: {result['content']}")
    else:
        print("No results found") 