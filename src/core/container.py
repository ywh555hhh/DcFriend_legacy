# src/core/container.py

from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.core.config import settings
from src.core.prompt_manager import PromptManager
from src.db.repositories.member_repository import MemberRepository
from src.services.member_service import MemberService
from src.services.gemini_client import GeminiClient
from src.services.ai_service import AIService

class Container(containers.DeclarativeContainer):
    """
    项目的依赖注入容器。
    所有依赖关系在此处声明。
    我们采用手动织入 (wiring) 的方式，在应用主入口 (main.py) 控制织入时机。
    """
    
    # -------------------- 【关键修复】 --------------------
    # 移除或注释掉 wiring_config，以禁用自动织入。
    # 这可以避免在容器初始化过程中因循环导入而导致的织入失败。
    # 我们将在 main.py 中手动、显式地调用 container.wire()。
    #
    # wiring_config = containers.WiringConfiguration(
    #     packages=[
    #         "src.api",
    #         "src.cogs",
    #     ]
    # )
    # --------------------------------------------------------

    # --- 核心配置 ---
    config = providers.Configuration()
    # (确保从 settings 加载配置)
    config.from_pydantic(settings)

    # --- 服务提供者 (Providers) ---

    prompt_manager = providers.Singleton(
        PromptManager,
        prompts_dir=settings.PROJECT_ROOT / "src" / "prompts"
    )
    
    gemini_client = providers.Singleton(
        GeminiClient,
        api_key=settings.GEMINI_API_KEY,
        model_name=settings.GEMINI_MODEL_NAME,
    )

    db_engine = providers.Singleton(
        create_async_engine,
        url=str(settings.DATABASE_URL), # 确保 URL 是字符串
        echo=getattr(settings, 'DB_ECHO', False),
    )

    db_session_factory = providers.Singleton(
        async_sessionmaker,
        bind=db_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    member_repo = providers.Factory(
        MemberRepository,
        session_factory=db_session_factory,
    )

    member_service = providers.Factory(
        MemberService,
        member_repo=member_repo,
    )
    
    ai_service = providers.Factory(
        AIService,
        client=gemini_client,
        prompts=prompt_manager,
    )