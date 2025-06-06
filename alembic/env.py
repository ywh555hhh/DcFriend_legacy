# alembic/env.py
import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# 使用 insert(0, ...) 比 append 更优先，可以避免路径冲突

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy.pool import NullPool
from alembic import context

# 现在导入应该能成功
from src.core.config import settings
from src.db.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    # ... (这部分保持不变) ...
    url = settings.DATABASE_URL # 从我们的 settings 获取 URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    # ... (这部分保持不变) ...
    connectable = engine_from_config(
        {"sqlalchemy.url": settings.DATABASE_URL},
        prefix="sqlalchemy.",
        poolclass=NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()