# src/services/gemini_client.py
import google.generativeai as genai
import logging

# 设置一个日志记录器
logger = logging.getLogger(__name__)

class GeminiClient:
    """
    一个封装了 Google Gemini API 调用的底层客户端。
    """
    def __init__(self, api_key: str, model_name: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        logger.info(f"GeminiClient initialized with model: {model_name}")

    async def generate_text(self, prompt: str) -> str:
        """根据给定的 prompt 生成文本"""
        try:
            # 使用异步方法
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}", exc_info=True)
            return "抱歉，我的大脑好像短路了，稍后再试吧！"