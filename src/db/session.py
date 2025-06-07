# src/db/session.py

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.core.config import settings

# 1. 创建一个异步引擎实例
#    这个引擎是整个 SQLAlchemy 应用的连接来源。
#    echo=False 在生产环境中是好的，如果需要调试 SQL，可以设为 True
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# 2. 创建一个异步会话工厂 (Session Factory)
#    - expire_on_commit=False 防止在提交事务后，对象实例过期，
#      这样我们在提交后仍然可以访问对象的属性，这在 Web 应用和机器人中很方便。
#    - class_=AsyncSession 指定我们要使用异步会话。
AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)

# 可选的辅助函数，用于依赖注入（我们将在第 3 步用到）
# async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
#     async with AsyncSessionFactory() as session:
#         yield session