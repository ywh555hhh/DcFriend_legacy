# tests/conftest.py (最终健壮版)
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.db.models import Base


@pytest_asyncio.fixture(scope="session")
async def async_engine():
    """整个测试会话共享一个内存数据库引擎。"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database(async_engine):
    """
    在会话开始时创建所有表。autouse=True 确保它会自动运行。
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    【核心修正】为每个测试函数提供一个在嵌套事务中运行的会话。
    这能确保测试内部的 commit 不会影响测试的隔离性。
    """
    # 1. 创建一个到引擎的连接
    async with async_engine.connect() as connection:
        # 2. 在这个连接上开始一个可以嵌套的事务
        async with connection.begin() as transaction:
            # 3. 基于这个连接创建一个会话
            async_session_factory = async_sessionmaker(bind=connection)
            async with async_session_factory() as session:
                # 4. 将这个会话提供给测试函数
                yield session

            # 5. 测试结束后，无论测试内部是否 commit，
            #    我们回滚最外层的这个事务，撤销所有更改。
            await transaction.rollback()
