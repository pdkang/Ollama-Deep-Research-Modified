import os
import requests
from typing import Dict, Any, List, Optional
from langsmith import traceable
from tavily import TavilyClient
from duckduckgo_search import DDGS
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import HuggingFaceEmbeddings

def deduplicate_and_format_sources(search_response, max_tokens_per_source, include_raw_content=False):
    """
    Takes either a single search response or list of responses from search APIs and formats them.
    Limits the raw_content to approximately max_tokens_per_source.
    include_raw_content specifies whether to include the raw_content from Tavily in the formatted string.
    
    Args:
        search_response: Either:
            - A dict with a 'results' key containing a list of search results
            - A list of dicts, each containing search results
            
    Returns:
        str: Formatted string with deduplicated sources
    """
    # Convert input to list of results
    if isinstance(search_response, dict):
        sources_list = search_response['results']
    elif isinstance(search_response, list):
        sources_list = []
        for response in search_response:
            if isinstance(response, dict) and 'results' in response:
                sources_list.extend(response['results'])
            else:
                sources_list.extend(response)
    else:
        raise ValueError("Input must be either a dict with 'results' or a list of search results")
    
    # Deduplicate by URL
    unique_sources = {}
    for source in sources_list:
        if source['url'] not in unique_sources:
            unique_sources[source['url']] = source
    
    # Format output
    formatted_text = "Sources:\n\n"
    for i, source in enumerate(unique_sources.values(), 1):
        formatted_text += f"Source {source['title']}:\n===\n"
        formatted_text += f"URL: {source['url']}\n===\n"
        formatted_text += f"Most relevant content from source: {source['content']}\n===\n"
        if include_raw_content:
            # Using rough estimate of 4 characters per token
            char_limit = max_tokens_per_source * 4
            # Handle None raw_content
            raw_content = source.get('raw_content', '')
            if raw_content is None:
                raw_content = ''
                print(f"Warning: No raw_content found for source {source['url']}")
            if len(raw_content) > char_limit:
                raw_content = raw_content[:char_limit] + "... [truncated]"
            formatted_text += f"Full source content limited to {max_tokens_per_source} tokens: {raw_content}\n\n"
                
    return formatted_text.strip()

def format_sources(search_results):
    """Format search results into a bullet-point list of sources.
    
    Args:
        search_results (dict): Tavily search response containing results
        
    Returns:
        str: Formatted string with sources and their URLs
    """
    return '\n'.join(
        f"* {source['title']} : {source['url']}"
        for source in search_results['results']
    )

@traceable
def duckduckgo_search(query: str, max_results: int = 3, fetch_full_page: bool = False) -> Dict[str, List[Dict[str, str]]]:
    """Search the web using DuckDuckGo.
    
    Args:
        query (str): The search query to execute
        max_results (int): Maximum number of results to return
        
    Returns:
        dict: Search response containing:
            - results (list): List of search result dictionaries, each containing:
                - title (str): Title of the search result
                - url (str): URL of the search result
                - content (str): Snippet/summary of the content
                - raw_content (str): Same as content since DDG doesn't provide full page content
    """
    try:
        with DDGS() as ddgs:
            results = []
            search_results = list(ddgs.text(query, max_results=max_results))
            
            for r in search_results:
                url = r.get('href')
                title = r.get('title')
                content = r.get('body')
                
                if not all([url, title, content]):
                    print(f"Warning: Incomplete result from DuckDuckGo: {r}")
                    continue

                raw_content = content
                if fetch_full_page:
                    try:
                        # Try to fetch the full page content using curl
                        import urllib.request
                        from bs4 import BeautifulSoup

                        response = urllib.request.urlopen(url)
                        html = response.read()
                        soup = BeautifulSoup(html, 'html.parser')
                        raw_content = soup.get_text()
                        
                    except Exception as e:
                        print(f"Warning: Failed to fetch full page content for {url}: {str(e)}")
                
                # Add result to list
                result = {
                    "title": title,
                    "url": url,
                    "content": content,
                    "raw_content": raw_content
                }
                results.append(result)
            
            return {"results": results}
    except Exception as e:
        print(f"Error in DuckDuckGo search: {str(e)}")
        print(f"Full error details: {type(e).__name__}")
        return {"results": []}

@traceable
def tavily_search(query, include_raw_content=True, max_results=3):
    """ Search the web using the Tavily API.
    
    Args:
        query (str): The search query to execute
        include_raw_content (bool): Whether to include the raw_content from Tavily in the formatted string
        max_results (int): Maximum number of results to return
        
    Returns:
        dict: Search response containing:
            - results (list): List of search result dictionaries, each containing:
                - title (str): Title of the search result
                - url (str): URL of the search result
                - content (str): Snippet/summary of the content
                - raw_content (str): Full content of the page if available"""
     
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY environment variable is not set")
    tavily_client = TavilyClient(api_key=api_key)
    return tavily_client.search(query, 
                         max_results=max_results, 
                         include_raw_content=include_raw_content)

@traceable
def perplexity_search(query: str, perplexity_search_loop_count: int) -> Dict[str, Any]:
    """Search the web using the Perplexity API.
    
    Args:
        query (str): The search query to execute
        perplexity_search_loop_count (int): The loop step for perplexity search (starts at 0)
  
    Returns:
        dict: Search response containing:
            - results (list): List of search result dictionaries, each containing:
                - title (str): Title of the search result
                - url (str): URL of the search result
                - content (str): Snippet/summary of the content
                - raw_content (str): Full content of the page if available
    """

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {os.getenv('PERPLEXITY_API_KEY')}"
    }
    
    payload = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "system",
                "content": "Search the web and provide factual information with sources."
            },
            {
                "role": "user",
                "content": query
            }
        ]
    }
    
    response = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers=headers,
        json=payload
    )
    response.raise_for_status()  # Raise exception for bad status codes
    
    # Parse the response
    data = response.json()
    content = data["choices"][0]["message"]["content"]

    # Perplexity returns a list of citations for a single search result
    citations = data.get("citations", ["https://perplexity.ai"])
    
    # Return first citation with full content, others just as references
    results = [{
        "title": f"Perplexity Search {perplexity_search_loop_count + 1}, Source 1",
        "url": citations[0],
        "content": content,
        "raw_content": content
    }]
    
    # Add additional citations without duplicating content
    for i, citation in enumerate(citations[1:], start=2):
        results.append({
            "title": f"Perplexity Search {perplexity_search_loop_count + 1}, Source {i}",
            "url": citation,
            "content": "See above for full content",
            "raw_content": None
        })
    
    return {"results": results}

@traceable
def setup_qdrant_client(collection_name="research_documents"):
    """Set up and return a QdrantClient instance.
    
    Args:
        collection_name (str): Name of the collection to use
        
    Returns:
        QdrantClient: Configured QdrantClient instance
    """
    # Get connection details from environment variables or use defaults
    host = os.getenv("QDRANT_HOST", "localhost")
    port = int(os.getenv("QDRANT_PORT", "6333"))
    
    # Create client
    client = QdrantClient(host=host, port=port)
    
    # Check if collection exists, create it if not
    collections = client.get_collections().collections
    collection_names = [collection.name for collection in collections]
    
    if collection_name not in collection_names:
        # Define the dimensionality of your embeddings
        # 384 is the dimension for 'all-MiniLM-L6-v2'
        embedding_size = 384
        
        # Create the collection
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=embedding_size,
                distance=models.Distance.COSINE
            )
        )
        print(f"Created new collection: {collection_name}")
    
    return client

@traceable
def get_embeddings_model():
    """Get the embeddings model.
    
    Returns:
        HuggingFaceEmbeddings: Configured embeddings model
    """
    # Use a small but effective model
    model_name = os.getenv("EMBEDDINGS_MODEL", "all-MiniLM-L6-v2")
    
    # Create embeddings instance
    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    return embeddings

@traceable
def query_qdrant(query, collection_name="research_documents", top_k=5):
    """Query the QDrant vector store with the given query.
    
    Args:
        query (str): The query to search for
        collection_name (str): Name of the collection to search
        top_k (int): Number of results to return
        
    Returns:
        dict: Search response containing:
            - results (list): List of search result dictionaries, each containing:
                - title (str): Title of the document
                - url (str): URL or source identifier
                - content (str): Snippet/summary of the content
                - raw_content (str): Full content of the document
    """
    try:
        # Get client and embeddings
        client = setup_qdrant_client(collection_name)
        embeddings = get_embeddings_model()
        
        # Create Qdrant wrapper
        qdrant = Qdrant(
            client=client,
            collection_name=collection_name,
            embeddings=embeddings,
        )
        
        # Search for similar documents
        docs = qdrant.similarity_search_with_score(query, k=top_k)
        
        # Format results
        results = []
        for doc, score in docs:
            # Extract metadata
            metadata = doc.metadata
            title = metadata.get("title", "Untitled Document")
            url = metadata.get("source", "local")
            
            # Create result entry
            result = {
                "title": title,
                "url": url,
                "content": doc.page_content[:200] + "...",  # Short preview
                "raw_content": doc.page_content,
                "score": score
            }
            results.append(result)
        
        return {"results": results}
    
    except Exception as e:
        print(f"Error in QDrant search: {str(e)}")
        return {"results": []}