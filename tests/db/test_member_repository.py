# tests/db/test_member_repository.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# 导入你要测试的类和它依赖的模型
from db.repositories.member_repository import MemberRepository
from db.models import Member

# pytest 会自动发现标记了 @pytest.mark.asyncio 的测试函数
@pytest.mark.asyncio
async def test_create_new_member(db_session: AsyncSession):
    """
    测试 get_or_create 方法在用户不存在时的行为。
    `db_session` 参数是由 conftest.py 提供的 fixture。
    """
    # 1. 准备 (Arrange)
    # 我们需要一个 session_factory，但我们的 fixture 直接提供了 session
    # 所以我们创建一个简单的 lambda 函数来包装它
    session_factory = lambda: db_session
    repo = MemberRepository(session_factory=session_factory)
    
    discord_id = 12345
    name = "Newbie"
    display_name = "The New Guy"

    # 2. 执行 (Act)
    member, created = await repo.get_or_create(
        member_id=discord_id, 
        name=name, 
        display_name=display_name
    )

    # 3. 断言 (Assert)
    assert created is True
    assert member is not None
    assert member.id == discord_id
    assert member.name == name
    assert member.display_name == display_name


@pytest.mark.asyncio
async def test_get_existing_member(db_session: AsyncSession):
    """测试 get_or_create 方法在用户已存在时的行为。"""
    # 1. 准备 (Arrange)
    # 先在数据库里手动创建一个用户
    existing_id = 54321
    existing_name = "Oldbie"
    existing_member = Member(id=existing_id, name=existing_name)
    db_session.add(existing_member)
    await db_session.commit() # 提交到当前事务

    session_factory = lambda: db_session
    repo = MemberRepository(session_factory=session_factory)
    
    # 2. 执行 (Act)
    # 再次调用 get_or_create，但使用不同的名字来测试更新逻辑
    updated_name = "Oldbie_Updated"
    member, created = await repo.get_or_create(
        member_id=existing_id,
        name=updated_name
    )

    # 3. 断言 (Assert)
    assert created is False
    assert member is not None
    assert member.id == existing_id
    assert member.name == updated_name # 名字应该被更新了