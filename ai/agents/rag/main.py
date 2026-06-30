"""
Main entrypoint for FastAPI RAG Agent Service.
"""
import os
from fastapi import FastAPI
from api import router as api_router
from vectorstore import VectorStoreFactory


app = FastAPI(title="RAG Agent Service", version="1.0.0")

@app.on_event("startup")
def startup_event():
    store = VectorStoreFactory.get_vector_store()
    if os.path.exists("./vector_index.pkl"):
        store.load("./vector_index.pkl")

app.include_router(api_router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
