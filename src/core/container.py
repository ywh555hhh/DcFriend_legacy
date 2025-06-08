# src/core/container.py

from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

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

    # --- 1. 核心配置 (Configuration) ---
    # `config` provider 负责管理从 .env 文件加载的配置。
    # 它使得所有其他 provider 都可以通过 `config.some_value` 的方式访问配置项。
    config = providers.Configuration(strict=True)
    # 在容器类定义时，立即从 settings 对象加载配置。
    config.from_pydantic(settings)

    # --- 2. 核心与外部客户端 (Clients & Core Components) ---
    # 这些是独立的、通常与外部 API 或核心功能交互的底层组件。
    # 它们通常是 Singleton，以保证在整个应用生命周期中只有一个实例。

    prompt_manager = providers.Singleton(
        PromptManager,
        # 从配置中读取 prompts 文件夹的路径
        prompts_dir=config.PROJECT_ROOT.provided / "src" / "prompts",
    )

    gemini_client = providers.Singleton(
        GeminiClient,
        api_key=config.GEMINI_API_KEY,
        model_name=config.GEMINI_MODEL_NAME,
    )

    # --- 3. 数据库层 (Database Layer) ---
    # 负责数据库连接和会话管理。

    db_engine = providers.Singleton(
        create_async_engine,
        url=config.DATABASE_URL.as_(str),  # 确保 URL 是字符串
        echo=config.DB_ECHO.as_(bool).optional(),  # echo 是可选配置
    )

    db_session_factory = providers.Singleton(
        async_sessionmaker,
        bind=db_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    # --- 4. 数据仓库层 (Repository Layer) ---
    # 每个 Repository 负责与一个特定的数据模型（表）进行交互。
    # 它们是 `Factory` 类型，意味着每次请求时都会创建一个新的实例，
    # 这有助于确保数据库操作的隔离性。

    member_repo = providers.Factory(
        MemberRepository,
        session_factory=db_session_factory,
    )

    # ... 在这里添加其他 Repositories, 例如：
    # infraction_repo = providers.Factory(...)

    # --- 5. 业务服务层 (Service Layer) ---
    # Service 封装了核心业务逻辑，并编排 Repositories 和其他 Services。
    # 它们通常也是 `Factory` 类型，以确保每次业务操作都是在一个干净的状态下开始。

    member_service = providers.Factory(
        MemberService,
        member_repo=member_repo,  # <- 注入上面定义的 member_repo
    )

    ai_service = providers.Factory(
        AIService,
        client=gemini_client,  # <- 注入底层 gemini_client
        prompts=prompt_manager,  # <- 注入 prompt_manager
        # 如果 AIService 需要其他依赖，在这里继续添加
    )

    # ... 在这里添加其他 Services, 例如：
    # moderation_service = providers.Factory(
    #     ModerationService,
    #     member_repo=member_repo,
    #     infraction_repo=infraction_repo
    # )
