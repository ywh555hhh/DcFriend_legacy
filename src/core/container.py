from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.core.config import settings

from src.core.prompt_manager import PromptManager # <--- 新增
from src.db.repositories.member_repository import MemberRepository
from src.services.member_service import MemberService
from src.services.gemini_client import GeminiClient # <--- 新增
from src.services.ai_service import AIService # <--- 新增

class Container(containers.DeclarativeContainer):
    """
    项目的依赖注入容器 (模仿官方 FastAPI 示例)。
    这是一个单一、扁平的容器，负责定义所有组件及其依赖关系。
    """
    # 关键点 1: wiring_config 指向我们即将创建的 endpoints 模块
    wiring_config = containers.WiringConfiguration(modules=["src.api.endpoints"])

    # --- 核心配置 ---
    config = providers.Configuration()

    # --- 2. 在这里添加新的 providers ---

    # Prompt 管理器
    prompt_manager = providers.Singleton(
        PromptManager,
        prompts_dir=settings.PROJECT_ROOT / "src" / "prompts"
    )
    
    # 底层 Gemini 客户端
    gemini_client = providers.Singleton(
        GeminiClient,
        api_key=settings.GEMINI_API_KEY,
        model_name=settings.GEMINI_MODEL_NAME,
    )

    # --- 数据库层 (DB) ---
    db_engine = providers.Singleton(
        create_async_engine,
        url=settings.DATABASE_URL, # <--- 从智能的 settings 对象获取 URL
        echo=True, # 直接硬编码为 True，或者也可以从 settings 获取
    )

    db_session_factory = providers.Singleton(
        async_sessionmaker,
        bind=db_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    # --- 数据仓库层 (Repository) ---
    member_repo = providers.Factory(
        MemberRepository,
        session_factory=db_session_factory,
    )

    # --- 业务服务层 (Service) ---
    # 关键点 2: 直接在顶层定义 service，并从同级获取依赖
    member_service = providers.Factory(
        MemberService,
        member_repo=member_repo,
    )
    
        # 新增 AI 服务
    ai_service = providers.Factory(
        AIService,
        client=gemini_client,
        prompts=prompt_manager,
    )