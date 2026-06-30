# Clean Architecture RAG Agent System

An enterprise-grade, highly modular, and scalable Retrieval-Augmented Generation (RAG) system built in Python 3.12+ and FastAPI.

---

## 1. Directory Structure

```
ai/agents/rag/
├── api/             # FastAPI routers, endpoints, and request Pydantic models
├── cache/           # Local semantic query and embedding caching layer
├── chunking/        # Chunking strategies (Fixed, Recursive, Semantic)
├── config/          # Environment configuration loading using Pydantic
├── core/            # Core abstractions and shared base modules
├── embeddings/      # Embedding clients (Gemini, Mock, SentenceTransformers)
├── llm/             # LLM API connector with local Ollama fallback logic
├── logging/         # Structured logger with built-in latency profiling
├── parser/          # Isolated file parsers (PDF, DOCX, CSV, Excel, PPTX, JSON, TXT)
├── pipeline/        # Ingestion and Query orchestration pipelines
├── prompts/         # File-based prompt registry (system, context, answer)
├── reranker/        # Jaccard lexical/semantic hybrid reranking engine
├── retrieval/       # Top-K, similarity search, and score threshold filters
├── tests/           # Full pytest automation suite (parsers, chunks, stores, APIs)
├── vectorstore/     # Persistence vector indexes with metadata filtering
├── main.py          # Application entrypoint and startup lifecycle handlers
└── README.md        # Technical Documentation
```

---

## 2. Abstraction Abstraction Abstraction (SOLID)

To prevent third-party vendor lock-in, all primary engines are defined behind abstract base interfaces:
* **`BaseParser`**: Isolates how documents are read into text.
* **`BaseChunker`**: Isolates chunking algorithms.
* **`BaseEmbeddings`**: Isolates text vector generation.
* **`BaseVectorStore`**: Isolates persistence and search engines (swappable with Pinecone, Qdrant, Milvus).
* **`BaseReranker`**: Isolates reranking.
* **`BaseLlmClient`**: Isolates language model generation (swappable with OpenAI, Claude).

---

## 3. Supported File Types & Parsers
* **`.pdf`**: `pypdf` page parser.
* **`.docx`**: Block-level paragraph and table traversal parser preserving page layouts.
* **`.csv`**: Formats rows into clean Markdown tables.
* **`.xlsx` / `.xls`**: Iterates through sheets formatting cells using `openpyxl`.
* **`.pptx`**: PowerPoint slide shape text and speaker notes parser.
* **`.json`**: Structured json string representation.
* **`.txt` / `.md`**: UTF-8 plain text string decoder.

---

## 4. API Endpoints

* **`POST /upload`**: Uploads and indexes a file.
* **`POST /query`**: Submits a query to the RAG pipeline.
* **`GET /documents`**: Returns metadata about all ingested documents in the index.
* **`DELETE /document/{id}`**: Purges document vectors and updates persistence.
* **`POST /reindex`**: Serializes vector index store back to disk.
* **`GET /health`**: Live check.

---

## 5. Local Setup & Execution

### 5.1 Run Test Suite
To run all unit and API integration tests:
```powershell
backend\.venv\Scripts\python -m pytest ai/agents/rag/tests/test_rag.py -v
```

### 5.2 Start FastAPI Server
To launch the RAG service locally (runs on port `9002`):
```powershell
backend\.venv\Scripts\python -m uvicorn main:app --app-dir ai/agents/rag/ --port 9002 --reload
```
