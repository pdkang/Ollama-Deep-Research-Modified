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

# Check the structure of the loaded data
print(f"Loaded data type: {type(feats_data)}")
if isinstance(feats_data, dict):
    # If it's a dictionary, convert to a list of items
    print("Converting dictionary to list of items...")
    feats_list = []
    for key, value in feats_data.items():
        if isinstance(value, dict):
            # Add the key as a name if not present
            if 'name' not in value:
                value['name'] = key
            feats_list.append(value)
        else:
            feats_list.append({'name': key, 'description': str(value)})
    feats_data = feats_list
    
print(f"Processing {len(feats_data)} feats from JSON")

# Connect to QDrant
client = QdrantClient(host="localhost", port=6333)

# Collection name
collection_name = "DnD_Documents"

# Check if collection exists
collections = client.get_collections().collections
collection_names = [collection.name for collection in collections]

if collection_name not in collection_names:
    print(f"Creating collection '{collection_name}'...")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=1024,  # For BAAI/bge-large-en-v1.5
            distance=models.Distance.COSINE
        )
    )
else:
    # Clear the collection
    print(f"Clearing collection '{collection_name}'...")
    client.delete(
        collection_name=collection_name,
        points_selector=models.Filter()  # Empty filter deletes all points
    )

# Load the embedding model
print("Loading embedding model...")
model = SentenceTransformer('BAAI/bge-large-en-v1.5')

# Function to convert a feat to a document
def feat_to_document(feat):
    # Adjust based on your JSON structure
    if isinstance(feat, dict):
        content = f"Name: {feat.get('name', 'Unnamed Feat')}\n"
        if 'prerequisite' in feat:
            content += f"Prerequisite: {feat['prerequisite']}\n"
        if 'description' in feat:
            content += f"Description: {feat['description']}\n"
        return content, feat.get('name', 'Unnamed Feat')
    else:
        # Handle case where feat is not a dictionary
        return f"Content: {str(feat)}", "Unnamed Feat"

# Index documents
print("Indexing documents...")
batch_size = 100
total_feats = len(feats_data)

# Process in batches
for i in range(0, total_feats, batch_size):
    end_idx = min(i + batch_size, total_feats)
    batch = feats_data[i:end_idx]
    points = []
    
    for j, feat in enumerate(batch):
        # Convert feat to document
        content, title = feat_to_document(feat)
        
        # Create embedding
        vector = model.encode(content).tolist()
        
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
test_query = "What are the combat feats?"
print(f"Query: {test_query}")

# Create embedding for query
query_vector = model.encode(test_query).tolist()

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