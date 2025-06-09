import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock  # <-- 导入 AsyncMock
from pathlib import Path
import json

# 确保测试可以找到src目录下的模块
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.core.character_manager import CharacterManager
from src.core.character_model import Character, DialogueExample


@pytest.fixture
def mock_characters_dir() -> Path:
    """提供一个假的目录路径"""
    return Path("/fake/characters")


@pytest.fixture
def valid_char_json_str() -> str:
    """提供一个合法的角色JSON字符串"""
    return json.dumps(
        {
            "name": "TestBot",
            "description": "A test bot.",
            "first_message": "Hello!",
            "example_dialogue": [{"user": "hi", "bot": "hello"}],
            "main_chat_prompt_template": "template: {persona_description}",
        }
    )


@pytest_asyncio.fixture
async def char_manager(mock_characters_dir: Path) -> CharacterManager:
    """使用 pytest-asyncio 的 fixture 创建可重用的 CharacterManager 实例"""
    with patch("pathlib.Path.exists", return_value=True):
        return CharacterManager(mock_characters_dir)


@pytest.mark.asyncio
async def test_load_character_success(
    char_manager: CharacterManager, mock_characters_dir: Path, valid_char_json_str: str
):
    """
    【单元测试】测试当角色文件存在且内容合法时，能否成功加载。
    """
    char_name = "test_bot"

    # 【核心修正】创建一个支持异步上下文管理器的 AsyncMock
    mock_file = AsyncMock()
    # 模拟 aenter 返回一个对象，这个对象的 read 方法是另一个 AsyncMock
    mock_file.__aenter__.return_value.read = AsyncMock(return_value=valid_char_json_str)

    # 使用这个新的异步mock来 patch aiofiles.open
    with patch("aiofiles.open", return_value=mock_file) as mock_aio_open:
        character = await char_manager.load_character(char_name)

        # 【断言】
        assert isinstance(character, Character)
        assert character.name == "TestBot"

        # 验证 aiofiles.open 是否被正确调用
        mock_aio_open.assert_called_once_with(
            mock_characters_dir / f"{char_name}.json", mode="r", encoding="utf-8"
        )


@pytest.mark.asyncio
async def test_load_character_not_found(char_manager: CharacterManager):
    """
    【单元测试】测试当角色文件不存在时，是否能正确抛出 FileNotFoundError。
    """
    # 【核心修正】模拟 aiofiles.open 直接抛出 FileNotFoundError
    # 这里的 side_effect 可以是同步异常，因为 patch 会捕获它
    with patch("aiofiles.open", side_effect=FileNotFoundError) as mock_aio_open:
        with pytest.raises(
            FileNotFoundError, match="Character card 'non_existent.json' not found"
        ):
            await char_manager.load_character("non_existent")

        # 验证尝试打开了正确的文件路径
        mock_aio_open.assert_called_once()


@pytest.mark.asyncio
async def test_load_character_invalid_json(char_manager: CharacterManager):
    """
    【单元测试】测试当JSON文件内容不合法时，是否能正确抛出 ValueError。
    """
    invalid_json_str = '{"name": "TestBot", "description":}'  # 无效JSON

    # 【核心修正】与成功案例类似，创建一个支持异步的mock
    mock_file = AsyncMock()
    mock_file.__aenter__.return_value.read = AsyncMock(return_value=invalid_json_str)

    with patch("aiofiles.open", return_value=mock_file):
        with pytest.raises(
            ValueError, match="Error parsing character card 'invalid.json'"
        ):
            await char_manager.load_character("invalid")
