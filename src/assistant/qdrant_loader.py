import os
import argparse
from typing import List, Optional
from langchain_community.document_loaders import (
    DirectoryLoader, 
    TextLoader, 
    PyPDFLoader,
    CSVLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import HuggingFaceEmbeddings
from qdrant_client import QdrantClient

def load_documents(directory: str, extensions: List[str] = None):
    """Load documents from a directory with specified extensions."""
    if extensions is None:
        extensions = [".txt", ".pdf", ".csv"]
    
    documents = []
    
    # Configure loaders for different file types
    if ".txt" in extensions:
        txt_loader = DirectoryLoader(
            directory, 
            glob="**/*.txt", 
            loader_cls=TextLoader,
            show_progress=True
        )
        documents.extend(txt_loader.load())
    
    if ".pdf" in extensions:
        pdf_loader = DirectoryLoader(
            directory, 
            glob="**/*.pdf", 
            loader_cls=PyPDFLoader,
            show_progress=True
        )
        documents.extend(pdf_loader.load())
    
    if ".csv" in extensions:
        csv_loader = DirectoryLoader(
            directory, 
            glob="**/*.csv", 
            loader_cls=CSVLoader,
            show_progress=True
        )
        documents.extend(csv_loader.load())
    
    print(f"Loaded {len(documents)} documents")
    return documents

def split_documents(documents, chunk_size=1000, chunk_overlap=200):
    """Split documents into chunks."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks")
    return chunks

def get_embeddings():
    """Get the embeddings model."""
    model_name = os.getenv("EMBEDDINGS_MODEL", "all-MiniLM-L6-v2")
    
    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    return embeddings

def index_to_qdrant(chunks, collection_name="research_documents"):
    """Index document chunks to QDrant."""
    # Get QDrant client
    host = os.getenv("QDRANT_HOST", "localhost")
    port = int(os.getenv("QDRANT_PORT", "6333"))
    client = QdrantClient(host=host, port=port)
    
    # Get embeddings
    embeddings = get_embeddings()
    
    # Create or update collection
    Qdrant.from_documents(
        documents=chunks,
        embedding=embeddings,
        url=f"http://{host}:{port}",
        collection_name=collection_name,
        force_recreate=False  # Set to True to recreate the collection
    )
    
    print(f"Indexed {len(chunks)} chunks to QDrant collection '{collection_name}'")

def main():
    parser = argparse.ArgumentParser(description="Load and index documents to QDrant")
    parser.add_argument("--directory", type=str, required=True, help="Directory containing documents")
    parser.add_argument("--collection", type=str, default="research_documents", help="QDrant collection name")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Document chunk size")
    parser.add_argument("--chunk-overlap", type=int, default=200, help="Document chunk overlap")
    
    args = parser.parse_args()
    
    # Load documents
    documents = load_documents(args.directory)
    
    # Split documents
    chunks = split_documents(documents, args.chunk_size, args.chunk_overlap)
    
    # Index to QDrant
    index_to_qdrant(chunks, args.collection)

if __name__ == "__main__":
    main() 