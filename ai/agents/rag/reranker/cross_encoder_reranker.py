import re
from typing import List, Dict, Any
from .reranker_interface import BaseReranker

class TokenCrossEncoderReranker(BaseReranker):
    def rerank(self, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not candidates or not query:
            return candidates
            
        query_words = set(re.findall(r'\w+', query.lower()))
        if not query_words:
            return candidates
            
        reranked = []
        for cand in candidates:
            text = cand["text"].lower()
            text_words = set(re.findall(r'\w+', text))
            
            intersection = query_words.intersection(text_words)
            union = query_words.union(text_words)
            jaccard_score = len(intersection) / len(union) if union else 0.0
            
            # Combine semantic similarity and token match scores
            new_score = (0.6 * cand["score"]) + (0.4 * jaccard_score)
            
            cand_copy = cand.copy()
            cand_copy["score"] = round(new_score, 4)
            cand_copy["metadata"]["jaccard_overlap"] = len(intersection)
            reranked.append(cand_copy)
            
        reranked.sort(key=lambda x: x["score"], reverse=True)
        return reranked
