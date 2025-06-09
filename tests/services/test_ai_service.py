import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

# 确保测试可以找到src目录下的模块
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# 导入我们需要测试和模拟的组件
from src.services.ai_service import AIService
from src.core.character_model import Character, DialogueExample
from src.db.models import Member as MemberModel
from discord import Embed  # 我们需要模拟 Embed，但不需要真的创建它，MagicMock 就够了


# --- 模拟依赖的 Fixtures (基本不变) ---
@pytest.fixture
def mock_llm_client() -> AsyncMock:
    """创建一个模拟的 LLM 客户端。"""
    client = AsyncMock()
    client.generate_text.return_value = "这是来自模拟AI的回复"
    return client


@pytest.fixture
def mock_character_manager() -> AsyncMock:
    """创建一个模拟的角色管理器。"""
    manager = AsyncMock()
    fake_character = Character(
        name="测试看板娘",
        description="我是一个用于测试的看板娘。",
        first_message="你好，测试员！",
        example_dialogue=[DialogueExample(user="问", bot="答")],
        # 使用与实际模板相似的结构
        main_chat_prompt_template="""
角色描述: {persona_description}
用户信息: {user_info}
长期记忆:
{long_term_memory}
---
短期记忆 (聊天历史):
{short_term_memory}
---
当前输入:
{current_input}
        """,
    )
    manager.load_character.return_value = fake_character
    return manager


@pytest.fixture
def mock_member_service() -> AsyncMock:
    """创建一个模拟的成员服务。"""
    service = AsyncMock()
    fake_member = MemberModel(id=123, name="fake_user", display_name="Fake User")
    service.get_or_create_member.return_value = fake_member
    return service


@pytest.fixture
def mock_memory_service() -> AsyncMock:
    """创建一个模拟的记忆服务。"""
    service = AsyncMock()
    service.retrieve_relevant_memories.return_value = ["假的长期记忆1", "假的长期记忆2"]
    return service


# --- 被测试对象的 Fixture (不变) ---
@pytest.fixture
def ai_service(
    mock_llm_client: AsyncMock,
    mock_character_manager: AsyncMock,
    mock_member_service: AsyncMock,
    mock_memory_service: AsyncMock,
) -> AIService:
    """创建一个 AIService 实例，并注入所有模拟的依赖。"""
    return AIService(
        llm_client=mock_llm_client,
        character_manager=mock_character_manager,
        member_service=mock_member_service,
        memory_service=mock_memory_service,
    )


# --- 辅助函数：创建健壮的异步迭代器 Mock ---
def async_iter(items):
    """一个简单的辅助函数，用于创建可以被 `async for` 遍历的 Mock 对象。"""

    async def _async_iter():
        for item in items:
            yield item

    return _async_iter()


# --- 测试用例 ---


@pytest.mark.asyncio
async def test_generate_response_with_simple_text_message(
    ai_service: AIService, mock_llm_client: AsyncMock
):
    """
    【测试用例1】测试处理一个简单的、只包含文本的消息。
    这是为了确保旧功能在重构后依然正常。
    """
    # 1. 准备：创建一个模拟的 discord.Message 对象
    mock_message = MagicMock()
    mock_message.author = MagicMock(display_name="TestUser")
    mock_message.clean_content = "你好，这是一个纯文本测试"
    mock_message.embeds = []  # 明确指定 embeds 为空

    # 模拟频道历史 (也为纯文本)
    mock_history_msg = MagicMock()
    mock_history_msg.author = MagicMock(display_name="HistUser")
    mock_history_msg.clean_content = "这是一条历史消息"
    mock_history_msg.embeds = []

    # 使用辅助函数创建异步迭代器
    mock_message.channel.history.return_value = async_iter([mock_history_msg])

    # 2. 执行
    await ai_service.generate_response(mock_message)

    # 3. 断言
    mock_llm_client.generate_text.assert_awaited_once()
    final_prompt = mock_llm_client.generate_text.call_args[0][0]

    # 检查 prompt 是否正确格式化
    assert "HistUser: 这是一条历史消息" in final_prompt
    assert "TestUser: 你好，这是一个纯文本测试" in final_prompt
    assert "[嵌入内容开始]" not in final_prompt  # 确认没有错误的 embed 标记


@pytest.mark.asyncio
async def test_generate_response_with_embed_message(
    ai_service: AIService, mock_llm_client: AsyncMock
):
    """
    【测试用例2 - 核心】测试处理一个包含 Embed 的复杂消息。
    这是对新功能的核心验证。
    """
    # 1. 准备：创建一个包含模拟 Embed 的消息
    mock_embed = MagicMock(spec=Embed)
    mock_embed.title = "测试标题"
    mock_embed.description = "这是Embed的描述"

    # --- [修改点 1] ---
    # 直接模拟 author 对象和它的 name 属性
    mock_embed.author = MagicMock()
    mock_embed.author.name = "Embed作者"  # 明确设置 .name 属性

    mock_embed.footer = MagicMock()
    mock_embed.footer.text = "这是页脚"

    # 模拟字段 (Fields)
    mock_field1 = MagicMock()
    mock_field1.name = "字段1"
    mock_field1.value = "值1"
    mock_field2 = MagicMock()
    mock_field2.name = "字段2"
    mock_field2.value = "值2"
    mock_embed.fields = [mock_field1, mock_field2]

    # 模拟图片（只需要模拟URL存在即可）
    mock_embed.image = MagicMock()
    mock_embed.image.url = "http://example.com/image.png"
    mock_embed.thumbnail = None  # 假设没有缩略图

    mock_message = MagicMock()
    mock_message.author = MagicMock(display_name="EmbedSender")
    mock_message.clean_content = "看这个酷东西！"  # 消息可以同时有文本和embed
    mock_message.embeds = [mock_embed]

    # 假设历史记录为空，以简化测试
    mock_message.channel.history.return_value = async_iter([])

    # 2. 执行
    await ai_service.generate_response(mock_message)

    # 3. 断言
    mock_llm_client.generate_text.assert_awaited_once()
    final_prompt = mock_llm_client.generate_text.call_args[0][0]

    expected_input_str = """EmbedSender: 看这个酷东西！\n[嵌入内容开始]\n作者：Embed作者\n标题：测试标题\n描述:\n这是Embed的描述\n字段:\n- 字段1: 值1\n- 字段2: 值2\n[提示：消息包含一张主图片]\n页脚：这是页脚\n[嵌入内容结束]"""

    print("\n--- 实际生成的 Prompt ---")
    print(final_prompt)
    print("--------------------------")

    # 断言部分
    current_input_in_prompt = final_prompt.split("当前输入:\n")[1].strip()
    assert current_input_in_prompt == expected_input_str

    # 也可以继续检查其他部分
    assert "我是一个用于测试的看板娘。" in final_prompt
    assert "假的长期记忆1" in final_prompt
