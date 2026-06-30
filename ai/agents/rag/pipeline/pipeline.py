import time
import json
import uuid
from typing import List, Dict, Any
from parser import ParserFactory
from chunking import ChunkerFactory
from embeddings import EmbeddingsFactory
from vectorstore import VectorStoreFactory
from retrieval import RetrievalService
from reranker import RerankerFactory
from prompts import PromptLoader
from llm import LlmFactory


class IngestionPipeline:
    @staticmethod
    def ingest_document(file_bytes: bytes, file_name: str) -> Dict[str, Any]:
        start_time = time.time()
        
        # 1. Parse
        parse_start = time.time()
        parser = ParserFactory.get_parser(file_name)
        text = parser.parse(file_bytes, file_name)
        parse_latency = time.time() - parse_start
        
        # 2. Chunk
        chunk_start = time.time()
        chunker = ChunkerFactory.get_chunker("recursive")
        chunks = chunker.chunk(text, chunk_size=500, chunk_overlap=50)
        chunk_latency = time.time() - chunk_start
        
        # 3. Embed
        embed_start = time.time()
        embedder = EmbeddingsFactory.get_embeddings()
        vectors = embedder.embed_documents(chunks)
        embed_latency = time.time() - embed_start
        
        # 4. Vector Store Indexing
        db_start = time.time()
        store = VectorStoreFactory.get_vector_store()
        doc_id = str(uuid.uuid4())
        for i, (chunk_text, vec) in enumerate(zip(chunks, vectors)):
            chunk_id = f"{doc_id}_{i}"
            metadata = {
                "source_filename": file_name,
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
            store.add_embeddings(doc_id, chunk_id, vec, chunk_text, metadata)
            
        store.save("./vector_index.pkl")
        db_latency = time.time() - db_start
        
        total_latency = time.time() - start_time
        
        return {
            "document_id": doc_id,
            "filename": file_name,
            "chunks_count": len(chunks),
            "latency": {
                "parse_ms": round(parse_latency * 1000, 2),
                "chunk_ms": round(chunk_latency * 1000, 2),
                "embed_ms": round(embed_latency * 1000, 2),
                "db_ms": round(db_latency * 1000, 2),
                "total_ms": round(total_latency * 1000, 2)
            }
        }

class QueryPipeline:
    @staticmethod
    def query(user_query: str, top_k: int = 5, use_reranker: bool = True) -> Dict[str, Any]:
        start_time = time.time()
        
        # 1. Retrieve
        ret_start = time.time()
        candidates = RetrievalService.retrieve(user_query, top_k=top_k)
        ret_latency = time.time() - ret_start
        
        # 2. Rerank
        rerank_start = time.time()
        if use_reranker and candidates:
            reranker = RerankerFactory.get_reranker()
            candidates = reranker.rerank(user_query, candidates)
        rerank_latency = time.time() - rerank_start
        
        # 3. Construct Prompt
        context_template = PromptLoader.get_context_template()
        context_blocks = []
        for c in candidates:
            block = context_template.format(
                filename=c["metadata"].get("source_filename", "unknown"),
                chunk_id=c["chunk_id"],
                page_or_section=c["metadata"].get("chunk_index", 0),
                score=c["score"],
                text=c["text"]
            )
            context_blocks.append(block)
            
        full_context = "\n".join(context_blocks)
        
        system_instruction = PromptLoader.get_system_prompt()
        answer_template = PromptLoader.get_answer_template()
        formatted_prompt = answer_template.format(
            query=user_query,
            context=full_context
        )
        
        # 4. LLM Generation
        llm_start = time.time()
        llm = LlmFactory.get_llm_client()
        raw_res = llm.generate_response(system_instruction, formatted_prompt)
        llm_latency = time.time() - llm_start
        
        try:
            res_dict = json.loads(raw_res)
        except Exception:
            res_dict = {
                "answer": raw_res,
                "confidence": 0.5,
                "citations": []
            }
            
        total_latency = time.time() - start_time
        
        citations = []
        for c in candidates:
            citations.append({
                "document_name": c["metadata"].get("source_filename", "unknown"),
                "page_number": c["metadata"].get("chunk_index", 0),
                "chunk_id": c["chunk_id"],
                "similarity_score": c["score"]
            })
        
        return {
            "answer": res_dict.get("answer", ""),
            "confidence_score": res_dict.get("confidence", 0.0),
            "citations": citations,
            "latency": {
                "retrieval_ms": round(ret_latency * 1000, 2),
                "rerank_ms": round(rerank_latency * 1000, 2),
                "llm_ms": round(llm_latency * 1000, 2),
                "total_ms": round(total_latency * 1000, 2)
            }
        }
