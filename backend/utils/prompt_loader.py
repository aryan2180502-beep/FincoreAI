import os

class PromptLoader:
    def __init__(self, prompts_dir="backend/prompts"):
        self.prompts_dir = prompts_dir
        self._cache = {}

    def load(self, agent: str, role: str, **kwargs) -> str:
        """
        Loads a prompt file from the prompts directory and formats it with kwargs.
        Example: loader.load("agents/loan", "system") loads backend/prompts/agents/loan/system.txt
        """
        key = f"{agent}/{role}.txt"
        if key not in self._cache:
            file_path = os.path.join(self.prompts_dir, key)
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Prompt file not found: {file_path}")
            with open(file_path, "r") as f:
                self._cache[key] = f.read()
        
        return self._cache[key].format_map(kwargs)
