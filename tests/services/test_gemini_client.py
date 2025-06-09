import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock

# 确保测试可以找到src目录下的模块
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.services.gemini_client import GeminiClient, LLMClientError


# 使用 pytest fixture 来创建一个可重用的 GeminiClient 实例
# scope="module" 表示这个 fixture 在整个测试文件中只运行一次，提高效率
@pytest.fixture(scope="module")
def gemini_client() -> GeminiClient:
    """提供一个 GeminiClient 的实例用于测试。"""
    # 在测试中，API Key 可以是任何假的字符串
    return GeminiClient(api_key="fake-api-key", model_name="fake-model")


@pytest.mark.asyncio
async def test_generate_text_success(gemini_client: GeminiClient):
    """
    测试当 Gemini API 成功返回时，方法能否正确解析并返回文本。
    """
    prompt = "Hello, world!"
    expected_text = "Hello to you too!"

    # 创建一个模拟的 API 响应对象
    mock_api_response = AsyncMock()
    # 关键：google-generativeai 返回的响应对象有一个 .text 属性
    mock_api_response.text = expected_text

    # 使用 patch 来模拟 'generate_content_async' 方法
    # 让它在被调用时，返回我们上面创建的模拟响应
    with patch(
        "google.generativeai.GenerativeModel.generate_content_async",
        new=AsyncMock(return_value=mock_api_response),
    ) as mock_generate:
        # 调用被测试的方法
        result = await gemini_client.generate_text(prompt)

        # 断言结果是否符合预期
        assert result == expected_text

        # 断言模拟的API方法是否被以正确的参数调用了一次
        mock_generate.assert_awaited_once_with(prompt)


@pytest.mark.asyncio
async def test_generate_text_api_error(gemini_client: GeminiClient):
    """
    测试当 Gemini API 抛出异常时，方法能否捕获并重新抛出自定义的 LLMClientError。
    """
    prompt = "This will fail."
    original_error = ValueError("Invalid API Key")  # 模拟一个底层的库异常

    # 模拟 'generate_content_async' 方法，让它在被调用时抛出我们预设的异常
    with patch(
        "google.generativeai.GenerativeModel.generate_content_async",
        new=AsyncMock(side_effect=original_error),
    ) as mock_generate:
        # 使用 pytest.raises 来断言一个特定的异常是否被抛出
        with pytest.raises(LLMClientError) as excinfo:
            await gemini_client.generate_text(prompt)

        # (可选) 断言我们的自定义异常是否包含了原始异常的信息
        assert "Gemini API call failed" in str(excinfo.value)
        assert excinfo.value.__cause__ is original_error

        # 断言模拟的API方法被调用了
        mock_generate.assert_awaited_once_with(prompt)
