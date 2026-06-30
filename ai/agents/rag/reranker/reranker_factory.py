from .reranker_interface import BaseReranker
from .cross_encoder_reranker import TokenCrossEncoderReranker

class RerankerFactory:
    _instance = TokenCrossEncoderReranker()
    
    @staticmethod
    def get_reranker() -> BaseReranker:
        return RerankerFactory._instance
