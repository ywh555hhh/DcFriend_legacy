import pytest
from unittest.mock import MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# 确保能找到 src 目录
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# 导入组件
from src.services.member_service import MemberService
from src.db.repositories.member_repository import MemberRepository
from src.db.models import Member


# --- Fixtures ---
@pytest.fixture
def member_repo(db_session: AsyncSession) -> MemberRepository:
    """创建连接到测试数据库的 MemberRepository。依赖 conftest.py 的 db_session。"""
    return MemberRepository(session_factory=lambda: db_session)


@pytest.fixture
def member_service(member_repo: MemberRepository) -> MemberService:
    """创建注入了测试仓库的 MemberService。"""
    return MemberService(member_repo=member_repo)


# --- 测试用例 ---
@pytest.mark.asyncio
async def test_get_or_create_member_creates_new_user(
    member_service: MemberService, db_session: AsyncSession
):
    """测试当用户首次出现时，能否正确创建新用户。"""
    mock_discord_member = MagicMock()
    mock_discord_member.id = 12345
    mock_discord_member.name = "new_user"
    mock_discord_member.display_name = "Newbie"

    db_member = await member_service.get_or_create_member(mock_discord_member)

    assert db_member.id == 12345
    assert db_member.name == "new_user"

    # 直接从 db_session 验证数据库状态
    result = await db_session.execute(select(Member).where(Member.id == 12345))
    assert result.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_get_or_create_member_retrieves_and_updates_existing_user(
    member_service: MemberService, db_session: AsyncSession
):
    """测试当用户已存在时，能否正确获取并更新其信息。"""
    # 准备：先在数据库里创建一个老用户
    existing_member = Member(id=67890, name="old_user", display_name="Veteran")
    db_session.add(existing_member)
    await db_session.commit()

    # 准备：创建新的 discord.Member 对象
    mock_discord_member = MagicMock()
    mock_discord_member.id = 67890
    mock_discord_member.name = "old_user"
    mock_discord_member.display_name = "Arch-Veteran"

    # 执行
    db_member = await member_service.get_or_create_member(mock_discord_member)

    assert db_member.id == 67890
    assert db_member.display_name == "Arch-Veteran"

    # 验证数据库总数仍然是 1
    all_members = await db_session.execute(select(Member))
    assert len(all_members.scalars().all()) == 1
