# src/core/prompt_manager.py
from pathlib import Path

class PromptManager:
    """
    一个基础的 Prompt 管理器，负责加载和格式化文本文件中的 Prompt。
    """
    def __init__(self, prompts_dir: Path):
        self.prompts_dir = prompts_dir

    def get(self, name: str, **kwargs) -> str:
        """加载并格式化一个 prompt 模板"""
        prompt_path = self.prompts_dir / f"{name}.txt"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt '{name}' not found at {prompt_path}")
        
        template = prompt_path.read_text("utf-8")
        return template.format(**kwargs)