欢迎来到 **DcFriend Legacy** (看板娘) 项目！

本指南旨在为所有参与本项目的开发者提供一个清晰的路线图，帮助你快速理解我们的架构、理念和开发流程。无论你是想修复一个 bug，还是想添加一个全新的功能，这里都是你的起点。

## 目录

1. [项目愿景与理念](https://www.notion.so/Developer-Guide-20b30a943d8a80519915d4d0281a911c?pvs=21)
2. [技术栈概览](https://www.notion.so/Developer-Guide-20b30a943d8a80519915d4d0281a911c?pvs=21)
3. [架构深度解析](https://www.notion.so/Developer-Guide-20b30a943d8a80519915d4d0281a911c?pvs=21)
4. [开发流程](https://www.notion.so/Developer-Guide-20b30a943d8a80519915d4d0281a911c?pvs=21)
5. [接口与代码规范](https://www.notion.so/Developer-Guide-20b30a943d8a80519915d4d0281a911c?pvs=21)
6. [附录：架构决策记录](https://www.notion.so/Developer-Guide-20b30a943d8a80519915d4d0281a911c?pvs=21)

---

## 1. 项目愿景与理念

### 项目愿景

我们正在构建的，**不仅仅是一个 Discord 聊天机器人，而是一个有生命、有记忆、能与社群共同成长的数字伙伴**。她的核心身份是社群历史的见证者、成员关系的连接者和集体智慧的沉淀者。
她将通过长期的记忆、深度的交互和主动的融入，成为社群独一 - 无二的文化符号。

### 设计理念

- **服务化 (Everything as a Service)**: 项目的所有核心功能，无论是数据库操作、AI 调用还是复杂的业务逻辑，都被封装成独立的、可重用的“服务”。
- **高内聚，低耦合 (High Cohesion, Low Coupling)**: 每个模块只做一件事，并把它做好（高内聚）。模块之间通过清晰的接口（而不是混乱的实现细节）进行通信（低耦合）。
- **可测试性优先 (Testability First)**: 架构的设计必须保证每一个独立的业务逻辑单元都可以被独立地进行单元测试，无需依赖外部系统（如数据库或实时 API）。

### 架构理念

- **依赖倒置原则 (Dependency Inversion Principle)**: 高层模块不应该依赖低层模块的实现细节，两者都应该依赖于“抽象”（在我们的项目中，体现为 Service/Repository 的公共方法）。
- **单向数据流**: 严格遵循 `交互层 -> 服务层 -> 数据层` 的单向调用链，杜绝反向或跨层调用，保证系统的可预测性。
- **配置与代码分离**: 所有的敏感信息（密钥）和环境相关配置（数据库地址）都必须通过 `.env` 文件进行管理，代码本身不包含任何硬编码的配置。

---

## 2. 技术栈概览

本项目的技术栈是为了实现上述理念而精心选择的一套现代化 Python 方案。

| 层次 | 核心职责 | 技术选型 |
| --- | --- | --- |
| **交互层** | 与世界沟通 | `discord.py`, `FastAPI` (可选的调试 API) |
| **应用逻辑** | 组织与调度 | `dependency-injector` (依赖注入核心) |
| **业务服务** | 处理核心逻辑 | 自定义服务类 (e.g., `AIService`) |
| **数据访问** | 与数据库对话 | `SQLAlchemy 2.0 (ORM)`, `Alembic` (数据库迁移) |
| **数据存储** | 永久保存记忆 | `SQLite` (开发), `PostgreSQL` (生产) |
| **AI 与智能** | 提供“思考”能力 | `google-generativeai`, 自定义`PromptManager` |
| **开发与测试** | 保证项目质量 | `uv`, `pytest`, `pre-commit` |

---

## 3. 架构深度解析

### 架构分层图

```
+--------------------------------+
|      交互层 (Interface)        |
| (src/cogs/*, main.py)          |
+--------------------------------+
                |
                V (在 Cog 的 setup 函数中, 通过 DI 容器解析依赖)
+--------------------------------------------------------------------+
|                应用逻辑层 / 服务层 (Services)                     |
| (src/services/ai_service.py, src/services/member_service.py)       |
| <--- Services 之间可以互相调用 --->                                |
+--------------------------------------------------------------------+
                                |
                                V (通过方法调用)
+--------------------------------------------------------------------+
|            数据与智能层 (Data & Intelligence)                      |
| (src/db/repositories/*, src/services/*_client.py, src/core/*)      |
+--------------------------------------------------------------------+
                                |
                                V (通过驱动/API)
+--------------------------------------------------------------------+
|                   持久化层 (Persistence)                           |
| (SQLite/PostgreSQL, VectorDB, src/prompts/*.txt)                   |
+--------------------------------------------------------------------+

```

### 核心：依赖注入容器 (`container.py`)

`src/core/container.py` 是整个应用的“灵魂”和“总装配图”。

- **它的职责**: 定义项目中的所有核心组件（我们称之为 `Provider`），并声明它们之间的依赖关系。
- **它是如何工作的**: 我们采用一种清晰且健壮的**两步注入模式**：
    1. **启动时注册**: 在 `main.py` 启动时，我们会创建一个全局的 `Container` 实例，并将其“附加”到 `discord.py` 的 `bot` 对象上（即 `bot.container = container`）。这就像是给机器人背上了一个装满所有工具的“工具背包”。
    2. **加载时解析**: 当一个 `Cog`（如 `ChatCog`）需要被加载时，它的 `setup(bot)` 函数会被调用。在这个函数内部，我们通过 `bot.container` 访问到那个“工具背包”，然后从中**显式地、手动地**取出需要的所有“工具”（即服务实例，如 `container.member_service()`）。最后，我们将这些准备好的工具作为普通参数传递给 `Cog` 的构造函数。
- **为什么它重要**: 这种模式让我们获得了依赖注入的所有核心好处（解耦、可测试性、集中管理），同时又避免了在与 `discord.py` 集成时可能出现的“自动注入”不稳定的问题。它让依赖关系变得**极其明确**：你只需查看一个 `Cog` 的 `setup` 函数，就能知道它需要的所有服务。这使得替换实现（比如把 `GeminiClient` 换成 `OpenAIClient`）和进行单元测试变得极其简单。

### 各层职责详解

- **`src/cogs`**: 只处理与 Discord 的直接交互（监听事件、注册命令）。**绝对不包含业务逻辑**。它的工作是接收 Discord 的信息，然后调用相应的 Service，最后将 Service 返回的结果格式化并发送回 Discord。
- **`src/services`**: 包含项目的核心业务逻辑。`_service.py` 文件定义了高级业务流程（如 `AIService`），而 `_client.py` 文件定义了与外部 API（如 `GeminiClient`）通信的底层逻辑。
- **`src/db/repositories`**: 数据仓库层。每个`repository`对应一个数据库模型，封装了对该模型的所有增删改查（CRUD）操作。**Service 层通过调用 Repository 来与数据库交互，而不是直接执行 SQL 或 ORM 查询。**
- **`src/core`**: 存放项目的核心组件和配置，如 `container.py`, `config.py`, `prompt_manager.py`。
- **`src/api`**: (可选) 存放用于调试的 FastAPI 端点，它和 `cogs` 层是平级的，都是服务层的“消费者”。

---

[架构说明](https://www.notion.so/20c30a943d8a8014a11ac64a1626fd98?pvs=21)

## 4. 开发流程

### 环境搭建

1. 克隆仓库：`git clone ...`
2. 创建虚拟环境：`python -m venv .venv`
3. 激活虚拟环境：`source .venv/bin/activate` (Linux/macOS) 或 `.venv\\Scripts\\activate` (Windows)
4. 安装依赖：`uv pip install -r requirements.txt` (或 `uv pip install -e .[dev]` 如果有 `pyproject.toml`)
5. 创建配置文件：复制 `.env.example` 为 `.env`，并填入必要的密钥 (`BOT_TOKEN`, `GEMINI_API_KEY`)。
6. 初始化数据库：`uv run init_db.py` (运行一次性数据库创建脚本)。如果使用 Alembic，则运行 `alembic upgrade head`。

### 如何添加一个新功能（标准流程）

这是一个自下而上的标准开发流程，以添加“每日摘要”功能为例：

1. **[可选] 数据库建模**: 如果新功能需要新的数据表（比如 `summaries` 表），先在 `src/db/models.py` 中定义新的 `SummaryModel`。然后运行数据库初始化/迁移脚本。
2. **[可选] 创建 Repository**: 在 `src/db/repositories/` 下创建 `summary_repository.py`，封装对 `summaries` 表的数据库操作。
3. **创建 Service**: 在 `src/services/` 下创建 `summary_service.py`。这个 `SummaryService` 可能会依赖 `EventRepository` (获取数据) 和 `AIService` (进行总结)。
4. **注册到容器**: 打开 `src/core/container.py`，将新的 `SummaryRepository` 和 `SummaryService` 注册为 `Provider`，并正确声明它们的依赖关系。
5. **暴露功能**: 在 `src/cogs/` 下创建 `summary_cog.py`，并按照下一节的指导实现它。
6. **编写测试**: 在 `tests/` 目录下为你的新 Service 和 Repository 编写单元测试。

### 如何添加一个新的 Discord 交互

这是本项目的核心开发模式，请严格遵循。

1. **在 `src/cogs/` 目录下创建一个新的 `your_cog.py` 文件。**
2. **创建 Cog 类，并定义一个“干净”的 `__init__` 方法。**
它接收 `bot` 实例，以及所有它需要的服务作为普通参数。**不要在这里使用 `@inject` 装饰器**。
    
    ```python
    # src/cogs/your_cog.py
    from discord.ext import commands
    from src.services.service_a import ServiceA
    from src.services.service_b import ServiceB
    
    class YourCog(commands.Cog):
        def __init__(self, bot: commands.Bot, service_a: ServiceA, service_b: ServiceB):
            self.bot = bot
            self.service_a = service_a
            self.service_b = service_b
    
    ```
    
3. **在文件底部，实现 `async def setup(bot: commands.Bot):` 函数。**
这是依赖注入的**核心位置**。
    
    ```python
    # src/cogs/your_cog.py (续)
    async def setup(bot: commands.Bot):
        # 1. 从 bot 对象获取容器
        container = bot.container
    
        # 2. 从容器中解析需要的服务实例
        service_a_instance = container.service_a()
        service_b_instance = container.service_b()
    
        # 3. 创建 Cog 实例并传入依赖，然后注册到 bot
        await bot.add_cog(
            YourCog(
                bot=bot,
                service_a=service_a_instance,
                service_b=service_b_instance
            )
        )
    
    ```
    
4. **实现你的事件监听器或命令。**
在这些方法内部，通过 `self.service_a` 来使用你注入的服务。
    
    ```python
    # src/cogs/your_cog.py (续)
    class YourCog(commands.Cog):
        # ... __init__ ...
    
        @commands.Cog.listener()
        async def on_some_event(self, ...):
            await self.service_a.do_something()
    
        @commands.command()
        async def mycommand(self, ctx):
            result = await self.service_b.get_data()
            await ctx.send(result)
    
    ```
    
5. **在 `main.py` 的 `extensions_to_load` 列表中，添加你的新 Cog 的路径。**
    
    ```python
    # main.py
    ...
    async def main():
        ...
        async with bot:
            extensions_to_load = [
                "src.cogs.chat_cog",
                "src.cogs.your_cog"  # <-- 在这里添加
            ]
            for extension in extensions_to_load:
                await bot.load_extension(extension)
    ...
    
    ```
    

---

## 5. 接口与代码规范

### 服务层接口规范

- Service 的公共方法应该面向**业务领域**，而不是技术实现。例如，方法名应该是 `get_chat_response`，而不是 `call_gemini_and_format_prompt`。
- Service 的输入和输出，应该尽可能使用**领域对象**（如 `discord.Message`）或 Pydantic 模型，而不是零散的基本类型。
- Service **不应该**抛出与数据库或外部 API 相关的底层异常，而应该捕获它们，并返回一个友好的结果或抛出一个自定义的业务异常。

### 数据仓库层接口规范

- Repository 的方法应该清晰地描述其对数据库的操作，如 `get_by_id`, `create`, `get_or_create`, `list_by_channel`。
- Repository 的输入通常是基本数据类型（如 `id: int`），输出是数据库模型对象（如 `Member`）或其列表。
- Repository 是唯一允许直接使用 SQLAlchemy ORM 进行查询的地方。

### 代码风格

- 遵循 **PEP 8** 规范。
- 使用 **Type Hinting** 对所有函数签名和变量进行类型注解。
- 使用 **f-string** 进行字符串格式化。
- 在提交代码前，运行 `pre-commit run --all-files` 来自动格式化和检查代码。

---

## 6. 附录：架构决策记录

### 关于 Discord 交互层依赖注入的架构决策

- **背景**: 在项目初期，我们曾尝试使用 `dependency-injector` 的 `@inject` 装饰器直接对 `discord.py` Cogs 的 `__init__` 方法进行自动依赖注入。
- **问题**: 实践证明，该方案在与 `discord.py` 的扩展加载机制结合时表现不稳定。由于 `discord.py` 内部对 Cog 的元类处理，可能会干扰 `@inject` 装饰器的正常工作，导致依赖注入失败，难以调试。
- **决策**: 我们决定采用一种更明确、更健壮的注入模式：**在 `main.py` 中将容器实例附加到 `bot` 对象上，然后在每个 Cog 的 `setup` 函数中手动从容器解析依赖，并将其传递给 Cog 的构造函数。**
- **理由**: 此模式虽然需要在每个 Cog 的 `setup` 函数中增加几行样板代码，但它带来了极高的**清晰性、健壮性和可测试性**。它完全消除了对框架间复杂交互的依赖，让代码的执行路径变得透明。该模式被确立为本项目的**依赖注入最佳实践**。