import os
from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from pipeline import IngestionPipeline, QueryPipeline
from vectorstore import VectorStoreFactory


router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    use_reranker: bool = True

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        content = await file.read()
        res = IngestionPipeline.ingest_document(content, file.filename)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query")
def query_rag(req: QueryRequest):
    try:
        res = QueryPipeline.query(req.query, top_k=req.top_k, use_reranker=req.use_reranker)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents")
def list_documents():
    store = VectorStoreFactory.get_vector_store()
    docs = {}
    for item in store.store:
        doc_id = item["doc_id"]
        filename = item["metadata"].get("source_filename", "unknown")
        if doc_id not in docs:
            docs[doc_id] = {
                "document_id": doc_id,
                "filename": filename,
                "chunks_count": 0
            }
        docs[doc_id]["chunks_count"] += 1
    return list(docs.values())

@router.delete("/document/{id}")
def delete_document(id: str):
    store = VectorStoreFactory.get_vector_store()
    store.delete_document(id)
    store.save("./vector_index.pkl")
    return {"message": f"Document {id} deleted successfully."}

@router.post("/reindex")
def reindex_store():
    store = VectorStoreFactory.get_vector_store()
    store.save("./vector_index.pkl")
    return {"message": "Reindexing completed successfully."}
