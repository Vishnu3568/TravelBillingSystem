import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app
from parser import ParserFactory
from chunking import ChunkerFactory
from embeddings import EmbeddingsFactory
from vectorstore import VectorStoreFactory
from retrieval import RetrievalService
from reranker import RerankerFactory


client = TestClient(app)

def test_parsers():
    p_text = ParserFactory.get_parser("doc.txt")
    assert p_text.parse(b"Hello World", "doc.txt") == "Hello World"
    
    p_json = ParserFactory.get_parser("data.json")
    val = p_json.parse(b'{"key": "value"}', "data.json")
    assert "value" in val

    p_csv = ParserFactory.get_parser("data.csv")
    val_csv = p_csv.parse(b"Name,Age\nJohn,30", "data.csv")
    assert "John | 30" in val_csv

def test_chunking():
    chunker = ChunkerFactory.get_chunker("fixed")
    chunks = chunker.chunk("abcdefgh", chunk_size=4, chunk_overlap=0)
    assert len(chunks) == 2
    assert chunks[0] == "abcd"

    recursive = ChunkerFactory.get_chunker("recursive")
    r_chunks = recursive.chunk("Paragraph one.\n\nParagraph two.", chunk_size=20, chunk_overlap=0)
    assert len(r_chunks) == 2

def test_embeddings():
    embedder = EmbeddingsFactory.get_embeddings("mock")
    vec = embedder.embed_query("test query")
    assert len(vec) == 768
    
    vecs = embedder.embed_documents(["doc1", "doc2"])
    assert len(vecs) == 2
    assert len(vecs[0]) == 768

def test_vector_store():
    store = VectorStoreFactory.get_vector_store()
    store.store = []
    
    embedder = EmbeddingsFactory.get_embeddings("mock")
    v1 = embedder.embed_query("Travel bill for Ashapura.")
    v2 = embedder.embed_query("Office supplies invoice.")
    
    store.add_embeddings("doc_1", "c1", v1, "Travel bill for Ashapura.", {"source": "f1.txt"})
    store.add_embeddings("doc_2", "c2", v2, "Office supplies invoice.", {"source": "f2.txt"})
    
    matches = store.similarity_search(v1, top_k=1)
    assert len(matches) == 1
    assert matches[0]["doc_id"] == "doc_1"

def test_retrieval_and_rerank():
    store = VectorStoreFactory.get_vector_store()
    store.store = []
    
    embedder = EmbeddingsFactory.get_embeddings("mock")
    v1 = embedder.embed_query("Delhi to Mumbai flight bill.")
    v2 = embedder.embed_query("Hotel stay in Pune.")
    
    store.add_embeddings("doc1", "c1", v1, "Delhi to Mumbai flight bill.", {"source": "flight.txt"})
    store.add_embeddings("doc2", "c2", v2, "Hotel stay in Pune.", {"source": "hotel.txt"})
    
    results = RetrievalService.retrieve("Delhi flight bill", top_k=1, threshold=0.1)
    assert len(results) == 1
    assert results[0]["doc_id"] == "doc1"
    
    reranker = RerankerFactory.get_reranker()
    reranked = reranker.rerank("flight bill", results)
    assert len(reranked) == 1

def test_api_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_api_upload_and_query():
    files = {"file": ("test.txt", b"Duty slip number DS-9999 for Ashapura Travels in Pune.", "text/plain")}
    response = client.post("/upload", files=files)
    assert response.status_code == 200
    assert "document_id" in response.json()
    doc_id = response.json()["document_id"]
    
    response = client.get("/documents")
    assert response.status_code == 200
    assert any(d["document_id"] == doc_id for d in response.json())
    
    req_body = {
        "query": "What is the duty slip number?",
        "top_k": 1,
        "use_reranker": True
    }
    response = client.post("/query", json=req_body)
    assert response.status_code == 200
    assert "answer" in response.json()
    
    response = client.delete(f"/document/{doc_id}")
    assert response.status_code == 200
