import abc
from typing import List

class BaseChunker(abc.ABC):
    @abc.abstractmethod
    def chunk(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """
        Splits text into chunks of specified size and overlap.
        """
        pass
