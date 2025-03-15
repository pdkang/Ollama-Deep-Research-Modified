# Ollama Deep Researcher

Ollama Deep Researcher is a fully local web research assistant that uses any LLM hosted by [Ollama](https://ollama.com/search). Give it a topic and it will generate a web search query, gather web search results (via [Tavily](https://www.tavily.com/) by default), summarize the results of web search, reflect on the summary to examine knowledge gaps, generate a new search query to address the gaps, search, and improve the summary for a user-defined number of cycles. It will provide the user a final markdown summary with all sources used.

## 🚀 Quickstart

### Mac

1. Download the Ollama app for Mac [here](https://ollama.com/download).

2. Pull a local LLM from [Ollama](https://ollama.com/search). As an [example](https://ollama.com/library/deepseek-r1:8b):
```bash
ollama pull deepseek-r1:8b
```

3. Launch the assistant with the LangGraph server:

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh
uvx --refresh --from "langgraph-cli[inmem]" --with-editable . --python 3.11 langgraph dev
```

### Windows

1. Download the Ollama app for Windows [here](https://ollama.com/download).

2. Pull a local LLM from [Ollama](https://ollama.com/search). As an [example](https://ollama.com/library/deepseek-r1:8b):
```powershell
ollama pull deepseek-r1:8b
```

3. Clone the repository:
```bash
git clone https://github.com/langchain-ai/ollama-deep-researcher.git
cd ollama-deep-researcher
```

4. Launch the assistant with the LangGraph server:

```powershell
uv run langgraph dev
```

### Using the LangGraph Studio UI

When you launch LangGraph server, you should see the following output and Studio will open in your browser:
> Ready!
>
> API: http://127.0.0.1:2024
>
> Docs: http://127.0.0.1:2024/docs
>
> LangGraph Studio Web UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024

Open `LangGraph Studio Web UI` via the URL in the output above.

In the `configuration` tab:
* Pick your web search tool (DuckDuckGo, Tavily, or Perplexity) (it will by default be `DuckDuckGo`) 
* Set the name of your local LLM to use with Ollama (it will by default be `llama3.2`) 
* You can set the depth of the research iterations (it will by default be `3`)

<img width="1621" alt="Screenshot 2025-01-24 at 10 08 31 PM" src="https://github.com/user-attachments/assets/7cfd0e04-28fd-4cfa-aee5-9a556d74ab21" />

Give the assistant a topic for research, and you can visualize its process!

<img width="1621" alt="Screenshot 2025-01-24 at 10 08 22 PM" src="https://github.com/user-attachments/assets/4de6bd89-4f3b-424c-a9cb-70ebd3d45c5f" />

### Model Compatibility Note

When selecting a local LLM, note that this application relies on the model's ability to produce structured JSON output. Some models may have difficulty with this requirement:

- **Working well**: 
  - [Llama2 3.2](https://ollama.com/library/llama3.2)
  - [DeepSeek R1 (8B)](https://ollama.com/library/deepseek-r1:8b)
  
- **Known issues**:
  - [DeepSeek R1 (7B)](https://ollama.com/library/deepseek-llm:7b) - Currently has difficulty producing required JSON output
  
If you [encounter JSON-related errors](https://github.com/langchain-ai/ollama-deep-researcher/issues/18) (e.g., `KeyError: 'query'`), try switching to one of the confirmed working models.

### Browser Compatibility Note

When accessing the LangGraph Studio UI:
- Firefox is recommended for the best experience
- Safari users may encounter security warnings due to mixed content (HTTPS/HTTP)
- If you encounter issues, try:
  1. Using Firefox or another browser
  2. Disabling ad-blocking extensions
  3. Checking browser console for specific error messages

## How it works

Ollama Deep Researcher is inspired by [IterDRAG](https://arxiv.org/html/2410.04343v1#:~:text=To%20tackle%20this%20issue%2C%20we,used%20to%20generate%20intermediate%20answers.). This approach will decompose a query into sub-queries, retrieve documents for each one, answer the sub-query, and then build on the answer by retrieving docs for the second sub-query. Here, we do similar:
- Given a user-provided topic, use a local LLM (via [Ollama](https://ollama.com/search)) to generate a web search query
- Uses a search engine (configured for [DuckDuckGo](https://duckduckgo.com/), [Tavily](https://www.tavily.com/), or [Perplexity](https://www.perplexity.ai/hub/blog/introducing-the-sonar-pro-api)) to find relevant sources
- Uses LLM to summarize the findings from web search related to the user-provided research topic
- Then, it uses the LLM to reflect on the summary, identifying knowledge gaps
- It generates a new search query to address the knowledge gaps
- The process repeats, with the summary being iteratively updated with new information from web search
- It will repeat down the research rabbit hole
- Runs for a configurable number of iterations (see `configuration` tab)

## Outputs

The output of the graph is a markdown file containing the research summary, with citations to the sources used.

All sources gathered during research are saved to the graph state.

You can visualize them in the graph state, which is visible in LangGraph Studio:

![Screenshot 2024-12-05 at 4 08 59 PM](https://github.com/user-attachments/assets/e8ac1c0b-9acb-4a75-8c15-4e677e92f6cb)

The final summary is saved to the graph state as well:

![Screenshot 2024-12-05 at 4 10 11 PM](https://github.com/user-attachments/assets/f6d997d5-9de5-495f-8556-7d3891f6bc96)

## Deployment Options

There are [various ways](https://langchain-ai.github.io/langgraph/concepts/#deployment-options) to deploy this graph.

See [Module 6](https://github.com/langchain-ai/langchain-academy/tree/main/module-6) of LangChain Academy for a detailed walkthrough of deployment options with LangGraph.

## TypeScript Implementation

A TypeScript port of this project (without Perplexity search) is available at:
https://github.com/PacoVK/ollama-deep-researcher-ts

## Running as a Docker container

The included `Dockerfile` only runs LangChain Studio with ollama-deep-researcher as a service, but does not include Ollama as a dependant service. You must run Ollama separately and configure the `OLLAMA_BASE_URL` environment variable. Optionally you can also specify the Ollama model to use by providing the `OLLAMA_MODEL` environment variable.

Clone the repo and build an image:
```
$ docker build -t ollama-deep-researcher .
```

Run the container:
```
$ docker run --rm -it -p 2024:2024 \
  -e SEARCH_API="tavily" \ 
  -e TAVILY_API_KEY="tvly-***YOUR_KEY_HERE***" \
  -e OLLAMA_BASE_URL="http://host.docker.internal:11434/" \
  -e OLLAMA_MODEL="llama3.2" \  
  ollama-deep-researcher
```

NOTE: You will see log message:
```
2025-02-10T13:45:04.784915Z [info     ] 🎨 Opening Studio in your browser... [browser_opener] api_variant=local_dev message=🎨 Opening Studio in your browser...
URL: https://smith.langchain.com/studio/?baseUrl=http://0.0.0.0:2024
```
...but the browser will not launch from the container.

Instead, visit this link with the correct baseUrl IP address: [`https://smith.langchain.com/studio/thread?baseUrl=http://127.0.0.1:2024`](https://smith.langchain.com/studio/thread?baseUrl=http://127.0.0.1:2024)



===================================

## Using QDrant for Local RAG

This agent supports local RAG (Retrieval Augmented Generation) using QDrant vector database.

### fix qdrant_client not found error

1. uv add qdrant-client
2. uv add sentence-transformers

### Setup QDrant

1. Start QDrant (using Docker):
   ```bash
   docker run -p 6333:6333 -p 6334:6334 -v $(pwd)/qdrant_data:/qdrant/storage qdrant/qdrant
   ```

2. Index your documents:  (skip if you have already indexed your documents)
   ```bash
   python -m src.assistant.qdrant_loader --directory /path/to/your/documents --collection DnD_Documents
   ```

### Configuration

Set the following environment variables to configure QDrant:

- `QDRANT_HOST`: QDrant server host (default: "localhost")
- `QDRANT_PORT`: QDrant server port (default: "6333")
- `QDRANT_COLLECTION`: Collection name (default: "DnD_Documents")
- `QDRANT_TOP_K`: Number of results to retrieve (default: 5)
- `USE_RAG`: Enable/disable RAG (default: True)
- `EMBEDDINGS_MODEL`: HuggingFace model for embeddings (default: "all-MiniLM-L6-v2")

The agent will now:
1. Generate a search query
2. Query the local QDrant database for relevant documents
3. Query the web for additional information
4. Summarize both local and web sources
5. Continue with the existing reflection and follow-up process


===================================

project_root/
├── src/
│   └── assistant/
│       ├── __init__.py
│       ├── graph.py
│       ├── utils.py
│       └── utils_qdrant.py
├── reindex_dnd_feats.py
├── simple_test_qdrant.py
├── test_utils_qdrant.py
└── inspect_indexed_feats.py

Files Required to Run LangGraph Studio
To run LangGraph Studio with your RAG-enabled application, you need several key files. Let me explain what each file does and which ones are essential:

Essential Files
1. src/assistant/graph.py
- Purpose: Defines your LangGraph application structure
- Content: Contains the graph definition, nodes, and edges
- Importance: Critical - this is the main entry point for LangGraph Studio

2. src/assistant/utils_qdrant.py
- Purpose: Provides QDrant vector database integration
- Content: Contains functions to query QDrant for relevant documents
- Importance: Essential for RAG functionality

3. src/assistant/utils.py
- Purpose: Contains utility functions used by the graph
- Content: May include helper functions, data processing, etc.
- Importance: Essential if referenced by graph.py

4. src/assistant/_init_.py
- Purpose: Makes the assistant directory a proper Python package
- Content: Usually empty or contains minimal imports
- Importance: Required for proper Python package structure

Supporting Files (Not Directly Used by LangGraph Studio)
5. reindex_dnd_feats.py
- Purpose: Indexes your D&D feats data into QDrant
- Content: Script to process and store data in QDrant
- Importance: Used once to set up the vector database, not needed for runtime

6. inspect_indexed_feats.py
- Purpose: Helps inspect the data in your QDrant collection
- Content: Diagnostic tool to view indexed documents
- Importance: Useful for debugging, not needed for runtime

7. simple_test_qdrant.py
- Purpose: Tests QDrant integration outside of LangGraph
- Content: Simple script to verify QDrant queries work
- Importance: Useful for testing, not needed for runtime

8. test_utils_qdrant.py
- Purpose: Tests the utils_qdrant.py functionality
- Content: Test script for QDrant integration
- Importance: Useful for testing, not needed for runtime

Running LangGraph Studio

To run LangGraph Studio with your application:
This command:

uvx --refresh --from "langgraph-cli[inmem]" --with-editable . --python 3.11 langgraph dev

