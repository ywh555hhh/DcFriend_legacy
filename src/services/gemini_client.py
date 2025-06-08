# src/services/gemini_client.py (升级版)
import google.generativeai as genai
import logging

logger = logging.getLogger(__name__)


# 【新增】在这里定义自定义异常
class LLMClientError(Exception):
    """当与 LLM 客户端交互失败时抛出的通用异常。"""

    pass


class GeminiClient:
    """
    一个封装了 Google Gemini API 调用的底层客户端。
    """

    def __init__(self, api_key: str, model_name: str):
        # 这部分保持不变
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        logger.info(f"GeminiClient initialized with model: {model_name}")

    async def generate_text(self, prompt: str) -> str:
        """
        根据给定的 prompt 生成文本。
        如果成功，返回文本字符串。
        如果失败，抛出 LLMClientError。
        """
        try:
            response = await self.model.generate_content_async(prompt)
            # Gemini 有时可能返回空内容或有安全阻断，这里做个简单检查
            if not response.text:
                raise LLMClientError("Gemini API returned an empty response.")
            return response.text
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}", exc_info=True)
            # 【关键变更】抛出自定义异常，而不是返回字符串
            # 我们将原始异常包装起来，方便追溯问题
            raise LLMClientError(f"Gemini API call failed: {e}") from e
