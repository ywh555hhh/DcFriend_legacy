# src/core/container.py

from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# 直接从 settings 导入配置，这是最直接、最可靠的方式
from src.core.config import settings
from src.core.prompt_manager import PromptManager
from src.db.repositories.member_repository import MemberRepository
from src.services.member_service import MemberService
from src.services.gemini_client import GeminiClient
from src.services.ai_service import AIService

# ... 在这里导入所有需要被容器管理的其他类 ...


class Container(containers.DeclarativeContainer):
    """
    项目的核心依赖注入 (DI) 容器。

    这个容器使用 `dependency-injector` 库来管理整个应用中所有组件的生命周期和依赖关系。
    它像一个中央装配图，声明了“谁需要什么”以及“如何创建它们”。

    【架构模式】:
    我们不使用 @inject 装饰器或 wiring 功能。
    取而代之的是一种更明确、更健壮的模式：
    1. 在 `main.py` 中，创建此 `Container` 的唯一实例。
    2. 将此实例附加到 `bot.container` 属性上。
    3. 在每个 Cog 的 `setup()` 函数中，通过 `bot.container` 访问容器，并手动解析出该 Cog 所需的服务。

    这种方法避免了与 discord.py 扩展系统可能发生的冲突，并使依赖关系更加清晰。
    """

    # ------------------- 1. 外部依赖与核心客户端 -------------------
    # 这一部分定义了与外部世界直接交互的客户端，或者不依赖于本项目其他组件的核心工具。
    # 它们通常是 Singleton，以保证在整个应用生命周期中只有一个实例，避免重复创建连接或加载模型。

    prompt_manager = providers.Singleton(
        PromptManager,
        # 【实现说明】: 此处直接使用从 `src.core.config` 模块导入的 `settings` 对象。
        # 在程序加载时，`settings.PROJECT_ROOT` 已经是一个具体的 pathlib.Path 对象，
        # 因此可以安全地进行路径拼接操作。
        prompts_dir=settings.PROJECT_ROOT / "src" / "prompts",
    )

    gemini_client = providers.Singleton(
        GeminiClient,
        api_key=settings.GEMINI_API_KEY,
        model_name=settings.GEMINI_MODEL_NAME,
    )

    # ------------------- 2. 数据库层 -------------------
    # 这一部分负责建立和管理与数据库的连接。

    db_engine = providers.Singleton(
        create_async_engine,
        url=str(settings.DATABASE_URL),  # 确保 URL 是字符串
        echo=getattr(settings, "DB_ECHO", False),
    )

    db_session_factory = providers.Singleton(
        async_sessionmaker,
        bind=db_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    # ------------------- 3. 数据仓库层 (Repository) -------------------
    # Repository 封装了对特定数据表的数据库操作 (CRUD)。
    # 它们依赖于 `db_session_factory` 来获取数据库会话。
    # 使用 `Factory` 模式意味着每次请求服务时，都会创建一个新的 Repository 实例。

    member_repo = providers.Factory(
        MemberRepository,
        session_factory=db_session_factory,
    )

    # ... 在此添加其他 Repository 定义 ...

    # ------------------- 4. 业务服务层 (Service) -------------------
    # Service 包含了核心业务逻辑，并负责编排 Repositories 和其他 Services。
    # 它们的依赖项（如 `member_repo`）由容器根据上面的定义自动注入。
    # 同样使用 `Factory` 模式，确保业务操作的独立性。

    member_service = providers.Factory(
        MemberService,
        member_repo=member_repo,  # <- 注入上面定义的 member_repo
    )

    ai_service = providers.Factory(
        AIService,
        client=gemini_client,  # <- 注入底层 gemini_client
        prompts=prompt_manager,  # <- 注入 prompt_manager
    )

    # ... 在此添加其他 Service 定义 ...

    # ------------------- 5. 配置提供者 (可选) -------------------
    # 【说明】: `dependency-injector` 提供了一个专门的 `Configuration` provider。
    # 在当前项目中，我们直接使用导入的 `settings` 对象来配置其他 provider，这种方式更直接。
    # 保留这个 `config` provider 是为了未来可能的扩展，例如在测试中需要动态覆盖 (override) 配置。
    config = providers.Configuration()
    config.from_pydantic(settings)
