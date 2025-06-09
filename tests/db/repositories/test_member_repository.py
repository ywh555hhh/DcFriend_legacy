import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# 确保能找到 src 目录
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.db.repositories.member_repository import MemberRepository
from src.db.models import Member


@pytest.fixture
def member_repo(db_session: AsyncSession) -> MemberRepository:
    """创建一个 MemberRepository 实例，注入来自 conftest.py 的 db_session。"""
    # MemberRepository 需要一个 session_factory，我们用 lambda 适配
    return MemberRepository(session_factory=lambda: db_session)


@pytest.mark.asyncio
async def test_get_or_create_creates_new_member(
    member_repo: MemberRepository, db_session: AsyncSession
):
    """测试创建新用户的行为。"""
    member, created = await member_repo.get_or_create(
        member_id=123, name="Newbie", display_name="New Guy"
    )
    # commit 是必要的，因为 repo 内部可能只做了 add 和 flush
    await db_session.commit()

    assert created is True
    assert member.id == 123
    assert member.name == "Newbie"


@pytest.mark.asyncio
async def test_get_or_create_retrieves_and_updates_member(
    member_repo: MemberRepository, db_session: AsyncSession
):
    """测试获取并更新已存在用户的行为。"""
    # 准备：在数据库里创建一个用户
    existing_member = Member(id=456, name="Oldbie", display_name="Old Timer")
    db_session.add(existing_member)
    await db_session.commit()  # 提交初始状态

    # 执行：用新信息再次调用
    member, created = await member_repo.get_or_create(
        member_id=456, name="Oldbie", display_name="Veteran"
    )
    await db_session.commit()  # 提交更新

    assert created is False
    assert member.id == 456
    assert member.display_name == "Veteran"
