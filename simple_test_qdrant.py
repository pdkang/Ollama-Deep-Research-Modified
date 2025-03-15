# A simplified test script for QDrant queries
from src.assistant.utils_qdrant import query_qdrant

# Test queries
test_queries = [
    "What are the combat feats?",
    "Tell me about feats that improve spellcasting",
    "What feats are available for archers?",
    "Feats that improve strength",
    "Defensive feats"
]

# Collection name
collection_name = "DnD_Documents"

for query in test_queries:
    print(f"\nQuery: {query}")
    results = query_qdrant(query, collection_name=collection_name, top_k=3)
    
    if results and results.get("results"):
        print(f"Found {len(results['results'])} results:")
        for i, result in enumerate(results["results"], 1):
            print(f"Result {i} (score: {result['score']}):")
            print(f"Title: {result['title']}")
            print(f"Content: {result['content']}")
            print("-" * 50)
    else:
        print("No results found") 