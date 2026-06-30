import abc

class BaseParser(abc.ABC):
    @abc.abstractmethod
    def parse(self, file_bytes: bytes, file_name: str) -> str:
        """
        Parses document bytes and returns clean plain text.
        Preserves structural properties (tables, headers, sections) as text formatting where possible.
        """
        pass
