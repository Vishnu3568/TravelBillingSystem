import abc

class BaseLlmClient(abc.ABC):
    @abc.abstractmethod
    def generate_response(self, system_instruction: str, prompt: str) -> str:
        """
        Invokes LLM with custom system instructions and prompt.
        Returns a raw response string.
        """
        pass
