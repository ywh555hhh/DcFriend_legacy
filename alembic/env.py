# alembic/env.py

import asyncio

import sys
from pathlib import Path

# ... (其他 import 和代码保持不变) ...
from logging.config import fileConfig

# ！！！新添加的 import！！！
from sqlalchemy.ext.asyncio import create_async_engine

from sqlalchemy.pool import NullPool
from alembic import context

# ... (导入 settings 和 Base 保持不变) ...
from src.core.config import settings
from src.db.models import Base


# ... (config, target_metadata, run_migrations_offline 保持不变) ...
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    # ... (这部分保持不变) ...
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# vvvvvv 这里是我们需要修改的地方 vvvvvv
def run_migrations_online() -> None:
    """在 'online' 模式下运行迁移。"""
    
    async def run_async_migrations():
        """一个包含所有异步操作的内部函数。"""
        
        # 【错误点】engine_from_config 创建的是同步引擎。
        # connectable = engine_from_config(
        #     config.get_section(config.config_ini_section, {}),
        #     prefix="sqlalchemy.",
        #     poolclass=NullPool,
        #     url=settings.DATABASE_URL 
        # )

        # 【修正】直接使用 create_async_engine 创建一个真正的异步引擎。
        # 它知道如何处理 'sqlite+aiosqlite' 这样的异步 DSN。
        connectable = create_async_engine(
            settings.DATABASE_URL,
            poolclass=NullPool,
        )

        # 后续的异步代码是完全正确的，无需改动！
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
        
        await connectable.dispose()

    def do_run_migrations(connection):
        """一个包含所有同步 Alembic 操作的内部函数。"""
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

    asyncio.run(run_async_migrations())
# ^^^^^^ 修改结束 ^^^^^^


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()