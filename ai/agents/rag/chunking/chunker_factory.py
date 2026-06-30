from .chunker_interface import BaseChunker
from .fixed_chunker import FixedSizeChunker
from .recursive_chunker import RecursiveCharacterChunker
from .semantic_chunker import SemanticChunker

class ChunkerFactory:
    _chunkers = {
        "fixed": FixedSizeChunker(),
        "recursive": RecursiveCharacterChunker(),
        "semantic": SemanticChunker()
    }
    
    @staticmethod
    def get_chunker(strategy: str = "recursive") -> BaseChunker:
        chunker = ChunkerFactory._chunkers.get(strategy.lower())
        if not chunker:
            return ChunkerFactory._chunkers["recursive"]
        return chunker
