# tests/db/conftest.py
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator

# 使用内存数据库进行测试，这样速度快，且每次测试都是干净的环境
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(scope="session")
async def async_engine():
    """创建一个只在整个测试会话期间存在一次的异步引擎。"""
    engine = create_async_engine(TEST_DATABASE_URL)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def setup_database(async_engine):
    """
    在测试会 - 话开始时创建所有表，结束时虽然内存数据库会消失，
    但这是一个好的实践模式。
    """
    from db.models import Base # 延迟导入以确保路径正确
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # yield 关键字在这里表示，在它之前的代码是“设置”，之后的代码是“拆卸”
    # 对于内存数据库，我们不需要拆卸
    yield
    # 如果是文件数据库，可以在这里添加删除文件的代码
    # async with async_engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(async_engine, setup_database) -> AsyncGenerator[AsyncSession, None]:
    """
    为每一个测试函数提供一个独立的、干净的数据库会话和事务。
    这是最重要的 Fixture。
    """
    # 每个测试都从一个干净的数据库开始
    async_session_factory = async_sessionmaker(bind=async_engine, expire_on_commit=False)
    
    async with async_session_factory() as session:
        # 开启一个事务，测试将在这个事务中运行
        await session.begin()
        yield session
        # 测试结束后，回滚事务，确保测试之间互不影响
        await session.rollback()