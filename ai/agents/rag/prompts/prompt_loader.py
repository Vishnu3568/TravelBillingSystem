import os

class PromptLoader:
    _dir = os.path.dirname(__file__)

    @staticmethod
    def load_prompt(name: str) -> str:
        path = os.path.join(PromptLoader._dir, f"{name}.txt")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    @staticmethod
    def get_system_prompt() -> str:
        return PromptLoader.load_prompt("system")

    @staticmethod
    def get_context_template() -> str:
        return PromptLoader.load_prompt("context")

    @staticmethod
    def get_answer_template() -> str:
        return PromptLoader.load_prompt("answer")
