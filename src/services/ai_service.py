# src/services/ai_service.py
from src.core.prompt_manager import PromptManager
from src.services.gemini_client import GeminiClient

class AIService:
    """
    高级 AI 服务，封装了所有与 AI 相关的业务逻辑。
    """
    def __init__(self, client: GeminiClient, prompts: PromptManager):
        self.client = client
        self.prompts = prompts

    async def get_simple_chat_response(self, user_input: str) -> str:
        """
        获取一个简单的、无上下文的聊天回应。
        """
        # 1. 使用 PromptManager 格式化 prompt
        final_prompt = self.prompts.get("simple_chat", user_input=user_input)

        # 2. 调用底层客户端生成文本
        response_text = await self.client.generate_text(final_prompt)
        
        return response_text