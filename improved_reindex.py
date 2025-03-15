import os
import json
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer

# Path to your feats.json file
json_file = "/home/pkang/ai/aibootcamp/AIE5/17_On_Prem_Agent/data/data/feats.json"

# Load the JSON file
with open(json_file, 'r') as f:
    feats_data = json.load(f)

# Process the JSON structure
all_feats = []
if isinstance(feats_data, dict):
    for key, value in feats_data.items():
        if isinstance(value, list):
            # If value is a list of feats
            print(f"Found list of {len(value)} feats under key '{key}'")
            all_feats.extend(value)
        elif isinstance(value, dict):
            # If value is a single feat
            all_feats.append(value)
elif isinstance(feats_data, list):
    all_feats = feats_data

print(f"Processing {len(all_feats)} total feats")

# Connect to QDrant
client = QdrantClient(host="localhost", port=6333)

# Collection name
collection_name = "DnD_Documents"

# Force delete the collection if it exists
print(f"Deleting collection '{collection_name}' if it exists...")
try:
    client.delete_collection(collection_name)
    print(f"Collection '{collection_name}' deleted")
except Exception as e:
    print(f"Collection deletion error (probably doesn't exist): {str(e)}")

# Create a new collection
print(f"Creating collection '{collection_name}'...")
client.create_collection(
    collection_name=collection_name,
    vectors_config=models.VectorParams(
        size=384,  # For all-MiniLM-L6-v2
        distance=models.Distance.COSINE
    )
)

# Load the embedding model
print("Loading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Function to convert a feat to a document
def feat_to_document(feat):
    if not isinstance(feat, dict):
        return f"Content: {str(feat)}", "Unnamed Feat"
    
    content = f"Name: {feat.get('name', 'Unnamed Feat')}\n"
    
    # Add source if available
    if 'source' in feat:
        content += f"Source: {feat['source']}\n"
    
    # Add prerequisite if available
    if 'prerequisite' in feat:
        if isinstance(feat['prerequisite'], list):
            prereq_text = []
            for prereq in feat['prerequisite']:
                if isinstance(prereq, dict):
                    prereq_text.append(", ".join(f"{k}: {v}" for k, v in prereq.items()))
                else:
                    prereq_text.append(str(prereq))
            content += f"Prerequisite: {'; '.join(prereq_text)}\n"
        else:
            content += f"Prerequisite: {feat['prerequisite']}\n"
    
    # Add description if available
    if 'description' in feat:
        content += f"Description: {feat['description']}\n"
    
    # Add entries if available (common in D&D data)
    if 'entries' in feat and isinstance(feat['entries'], list):
        content += "Details:\n"
        for entry in feat['entries']:
            if isinstance(entry, str):
                content += f"- {entry}\n"
            elif isinstance(entry, dict) and 'name' in entry and 'entries' in entry:
                content += f"- {entry['name']}:\n"
                for subentry in entry['entries']:
                    if isinstance(subentry, str):
                        content += f"  - {subentry}\n"
    
    return content, feat.get('name', 'Unnamed Feat')

# Index documents
print("Indexing documents...")
batch_size = 50
total_feats = len(all_feats)

# Process in batches
for i in range(0, total_feats, batch_size):
    end_idx = min(i + batch_size, total_feats)
    batch = all_feats[i:end_idx]
    points = []
    
    for j, feat in enumerate(batch):
        # Convert feat to document
        content, title = feat_to_document(feat)
        
        # Create embedding
        vector = model.encode(content, normalize_embeddings=True).tolist()
        
        # Add to batch
        points.append(
            models.PointStruct(
                id=i+j,
                vector=vector,
                payload={
                    "title": title,
                    "source": json_file,
                    "content": content
                }
            )
        )
    
    # Add batch to QDrant
    client.upsert(
        collection_name=collection_name,
        points=points
    )
    
    print(f"Indexed {end_idx}/{total_feats} documents")

print(f"Finished indexing {total_feats} documents")

# Test search
print("\nTesting search...")
test_queries = [
    "What are the combat feats?",
    "Tell me about feats that improve spellcasting",
    "What feats are available for archers?",
    "Feats that improve strength",
    "Defensive feats"
]

for test_query in test_queries:
    print(f"\nQuery: {test_query}")
    
    # Create embedding for query
    query_vector = model.encode(test_query, normalize_embeddings=True).tolist()
    
    # Search
    search_results = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=3
    )
    
    if search_results:
        print(f"Found {len(search_results)} results:")
        for i, result in enumerate(search_results, 1):
            print(f"Result {i} (score: {result.score}):")
            print(f"Title: {result.payload.get('title', 'Untitled')}")
            print(f"Content: {result.payload.get('content', '')[:200]}...")
            print("-" * 50)
    else:
        print("No results found") 