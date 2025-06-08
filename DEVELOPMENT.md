# **【开发者指南 v3.2 - 终极版】DcFriend Legacy - 从基石到智能** 📝🚀🛠️

欢迎来到 **DcFriend Legacy** (看板娘) 项目！ 📝

本指南旨在为所有参与本项目的开发者提供一个清晰的路线图，帮助你快速理解我们的架构、理念和开发流程。无论你是想修复一个 bug，还是想添加一个全新的功能，这里都是你的起点。 🚀🔧🤖

## 目录

1.  [项目愿景与理念](#1-项目愿景与理念)
2.  [技术栈概览](#2-技术栈概览)
3.  [架构深度解析](#3-架构深度解析)
4.  [开发流程：从环境搭建到功能实现](#4-开发流程从环境搭建到功能实现)
5.  [接口与代码规范](#5-接口与代码规范)
6.  [附录：踩坑记录与架构决策](#6-附录踩坑记录与架构决策) 📝🚀

---

## 1. 项目愿景与理念

### 项目愿景

我们正在构建的，**不仅仅是一个 Discord 聊天机器人，而是一个有生命、有记忆、能与社群共同成长的数字伙伴**。她的核心身份是社群历史的见证者、成员关系的连接者和集体智慧的沉淀者。
她将通过长期的记忆、深度的交互和主动的融入，成为社群独一无二的文化符号。 📝🚀🤖

### 设计理念

-   **服务化 (Everything as a Service)**: 项目的所有核心功能，无论是数据库操作、AI 调用还是复杂的业务逻辑，都被封装成独立的、可重用的"服务"。
-   **高内聚，低耦合 (High Cohesion, Low Coupling)**: 每个模块只做一件事，并把它做好（高内聚）。模块之间通过清晰的接口（而不是混乱的实现细节）进行通信（低耦合）。
-   **可测试性优先 (Testability First)**: 架构的设计必须保证每一个独立的业务逻辑单元都可以被独立地进行单元测试，无需依赖外部系统（如数据库或实时 API）。 🔧🛠️🚀

### 架构理念

-   **依赖倒置原则 (Dependency Inversion Principle)**: 高层模块不应该依赖低层模块的实现细节，两者都应该依赖于"抽象"（在我们的项目中，体现为 Service/Repository 的公共方法）。
-   **单向数据流**: 严格遵循 `交互层 -> 服务层 -> 数据层` 的单向调用链，杜绝反向或跨层调用，保证系统的可预测性。
-   **配置与代码分离**: 所有的敏感信息（密钥）和环境相关配置（数据库地址）都必须通过 `.env` 文件进行管理，代码本身不包含任何硬编码的配置。

---

## 2. 技术栈概览

本项目的技术栈是为了实现上述理念而精心选择的一套现代化 Python 方案。 📝🔧

| 层次 | 核心职责 | 技术选型 |
| :--- | :--- | :--- |
| **交互层** | 与世界沟通 | `discord.py`, `FastAPI` (可选的调试 API) |
| **应用逻辑** | 组织与调度 | `dependency-injector` (依赖注入核心) |
| **业务服务** | 处理核心逻辑 | 自定义服务类 (e.g., `AIService`) |
| **数据访问** | 与数据库对话 | `SQLAlchemy 2.0 (ORM)`, `Alembic` (数据库迁移) |
| **数据存储** | 永久保存记忆 | `SQLite` (开发), `PostgreSQL` (生产) |
| **AI 与智能** | 提供"思考"能力 | `google-generativeai`, 自定义`PromptManager` |
| **开发与测试** | 保证项目质量 | `uv`, `pytest`, `pre-commit` | 🚀🤖🛠️

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
| (SQLite/PostgreSQL, VectorDB, data/characters/*.json)              |  <-- 【v3.1 更新】
+--------------------------------------------------------------------+
```

### 核心：依赖注入容器 (`container.py`)

`src/core/container.py` 是整个应用的"灵魂"和"总装配图"。

-   **它的职责**: 定义项目中的所有核心组件（我们称之为 `Provider`），并声明它们之间的依赖关系。
-   **它是如何工作的**: 我们采用一种清晰且健壮的**两步注入模式**：
    1.  **启动时注册**: 在 `main.py` 启动时，我们会创建一个全局的 `Container` 实例，并将其"附加"到 `discord.py` 的 `bot` 对象上（即 `bot.container = container`）。这就像是给机器人背上了一个装满所有工具的"工具背包"。
    2.  **加载时解析**: 当一个 `Cog`（如 `ChatCog`）需要被加载时，它的 `setup(bot)` 函数会被调用。在这个函数内部，我们通过 `bot.container` 访问到那个"工具背包"，然后从中**显式地、手动地**取出需要的所有"工具"（即服务实例，如 `container.member_service()`）。最后，我们将这些准备好的工具作为普通参数传递给 `Cog` 的构造函数。
-   **为什么它重要**: 这种模式让我们获得了依赖注入的所有核心好处（解耦、可测试性、集中管理），同时又避免了在与 `discord.py` 集成时可能出现的"自动注入"不稳定的问题。它让依赖关系变得**极其明确**：你只需查看一个 `Cog` 的 `setup` 函数，就能知道它需要的所有服务。这使得替换实现（比如把 `GeminiClient` 换成 `OpenAIClient`）和进行单元测试变得极其简单。

### 各层职责详解

-   **`src/cogs`**: 只处理与 Discord 的直接交互（监听事件、注册命令）。**绝对不包含业务逻辑**。它的工作是接收 Discord 的信息，然后调用相应的 Service，最后将 Service 返回的结果格式化并发送回 Discord。
-   **`src/services`**: 包含项目的核心业务逻辑。`_service.py` 文件定义了高级业务流程（如 `AIService`），而 `_client.py` 文件定义了与外部 API（如 `GeminiClient`）通信的底层逻辑。
-   **`src/db/repositories`**: 数据仓库层。每个`repository`对应一个数据库模型，封装了对该模型的所有增删改查（CRUD）操作。**Service 层通过调用 Repository 来与数据库交互，而不是直接执行 SQL 或 ORM 查询。**
-   **`src/core`**: 存放项目的核心组件和配置，如 `container.py`, `config.py`, `character_manager.py`。
-   **`src/api`**: (可选) 存放用于调试的 FastAPI 端点，它和 `cogs` 层是平级的，都是服务层的"消费者"。

---

## 4. 开发流程：从环境搭建到功能实现

### 4.1 环境搭建

1.  **克隆仓库**:
    ```bash
    git clone <您的项目 Git 仓库地址>
    cd <项目目录>
    ```

2.  **配置环境变量**:
    复制 `.env.example` (如果存在) 为 `.env`，并填入所有必要的密钥和配置。这是**必须**的一步。
    ```bash
    cp .env.example .env
    # 然后用编辑器打开 .env 文件并修改
    ```

3.  **安装依赖**:
    我们使用 `uv` 进行快速、可靠的依赖管理。只需运行：
    ```bash
    uv sync
    ```
    *(如果项目使用 `requirements.txt`，则运行 `uv pip install -r requirements.txt`)*

4.  **初始化数据库**:
    这是**首次搭建**或**模型变更后**的关键步骤。Alembic 管理数据库的"版本"，你需要先生成版本文件，再应用它。

    *   **第一步：生成迁移脚本** (`revision`)
        此命令会检测 `src/db/models.py` 中的模型与数据库的差异，并生成一个迁移脚本。
        ```bash
        uv run alembic revision --autogenerate -m "描述你的变更，例如：Initial schema"
        ```
    *   **第二步：应用迁移** (`upgrade`)
        此命令会执行所有尚未应用的迁移脚本，真正在数据库中创建或修改表。
        ```bash
        uv run alembic upgrade head
        ```

5.  **【v3.1 新增】验证环境 (可选但强烈推荐)**
    在启动主程序之前，运行完整的测试套件，以确保你的环境、依赖和配置都是正确的。
    ```bash
    uv run pytest
    ```
    **如果所有测试都通过**，说明你的本地环境已经完美就绪。如果出现错误，请根据错误提示解决，或参考附录中的踩坑记录。

6.  **运行项目**:
    ```bash
    uv run main.py
    ```
    如果一切顺利，你的机器人将成功启动并连接到 Discord。

### 4.2 如何添加一个新功能（标准流程）

这是一个自下而上的标准开发流程，以添加"每日摘要"功能为例：

1.  **[DB 层] 建模**: 如果需要新表，在 `src/db/models.py` 定义新模型。然后运行 `alembic revision` 和 `alembic upgrade`。
2.  **[DB 层] 创建 Repository**: 在 `src/db/repositories/` 下创建 `summary_repository.py`，封装对新表的操作。
3.  **[Service 层] 创建 Service**: 在 `src/services/` 下创建 `summary_service.py`，实现业务逻辑。
4.  **[Core 层] 注册到容器**: 在 `src/core/container.py` 中注册新的 Repository 和 Service，并声明依赖。
5.  **[Cogs 层] 暴露功能**: 在 `src/cogs/` 下创建 `summary_cog.py`，并按照下一节的指导实现它。
6.  **[测试] 编写测试**: 在 `tests/` 目录下，遵循**镜像结构**，为新 Service 和 Repository 编写单元/集成测试。

### 4.3 如何添加一个新的 Discord 交互 (核心模式)

这是本项目的**核心开发模式**，请严格遵循。

1.  **在 `src/cogs/` 目录下创建一个新的 `your_cog.py` 文件。**

2.  **创建 Cog 类，并定义一个"干净"的 `__init__` 方法。**
    它接收 `bot` 实例，以及所有它需要的服务作为普通参数。**不要在这里使用 `@inject` 装饰器**。

    ```python
    # src/cogs/your_cog.py
    from discord.ext import commands
    from src.services.service_a import ServiceA

    class YourCog(commands.Cog):
        def __init__(self, bot: commands.Bot, service_a: ServiceA):
            self.bot = bot
            self.service_a = service_a
    ```

3.  **在文件底部，实现 `async def setup(bot: commands.Bot):` 函数。**
    这是依赖注入的**核心位置**。

    ```python
    # src/cogs/your_cog.py (续)
    async def setup(bot: commands.Bot):
        # 1. 从 bot 对象获取容器
        container = bot.container

        # 2. 从容器中解析需要的服务实例
        service_a_instance = container.service_a()

        # 3. 创建 Cog 实例并传入依赖，然后注册到 bot
        await bot.add_cog(
            YourCog(
                bot=bot,
                service_a=service_a_instance
            )
        )
    ```
    **【v3.1 新增】注意：** 如果你的 Cog 非常简单，**不依赖于任何自定义服务**（比如一个只回复固定文本的 `!help` 命令），那么它的 `setup` 函数会更简单，你不需要从容器中解析任何东西：
    ```python
    # 一个无依赖 Cog 的 setup 示例
    async def setup(bot: commands.Bot):
        await bot.add_cog(YourSimpleCog(bot))
    ```

4.  **实现你的事件监听器或命令。**
    在这些方法内部，通过 `self.service_a` 来使用你注入的服务。

5.  **在 `main.py` 的 `extensions_to_load` 列表中，添加你的新 Cog 的路径。**

---

## 5. 接口与代码规范

### 服务层接口规范

-   Service 的公共方法应该面向**业务领域**，而不是技术实现。例如，方法名应该是 `get_chat_response`，而不是 `call_gemini_and_format_prompt`。
-   Service 的输入和输出，应该尽可能使用**领域对象**（如 `discord.Message`）或 Pydantic 模型，而不是零散的基本类型。
-   Service **不应该**抛出与数据库或外部 API 相关的底层异常，而应该捕获它们，并返回一个友好的结果或抛出一个自定义的业务异常（如 `LLMClientError`）。

### 数据仓库层接口规范

-   Repository 的方法应该清晰地描述其对数据库的操作，如 `get_by_id`, `create`, `get_or_create`, `list_by_channel`。
-   Repository 的输入通常是基本数据类型（如 `id: int`），输出是数据库模型对象（如 `Member`）或其列表。
-   Repository 是唯一允许直接使用 SQLAlchemy ORM 进行查询的地方。

### 代码风格

-   遵循 **PEP 8** 规范。
-   使用 **Type Hinting** 对所有函数签名和变量进行类型注解。
-   使用 **f-string** 进行字符串格式化。
-   在提交代码前，运行 `pre-commit run --all-files` 来自动格式化和检查代码。

---

## 6. 附录：踩坑记录与架构决策

### 6.1 DI 踩坑：`@inject` vs 手动注入

-   **背景**: 在项目初期，我们曾尝试使用 `dependency-injector` 的 `@inject` 装饰器直接对 `discord.py` Cogs 的 `__init__` 方法进行自动依赖注入。
-   **踩坑记录**: 实践证明，该方案在与 `discord.py` 的扩展加载机制结合时表现**不稳定**。具体表现为，尽管在 `main.py` 中正确调用了 `container.wire()`，但在 `Cog` 的 `__init__` 方法中接收到的依然是 `Provide` 对象，而不是真正的服务实例。
-   **原理解析**: 这很可能是由于 `discord.py` 内部对 Cog 的元类处理，干扰了 `@inject` 装饰器的正常工作，导致注入失败。这是一个框架间的兼容性边缘案例，难以调试。
-   **最终决策**: 我们决定采用一种更明确、更健壮的注入模式：**在 `main.py` 中将容器实例附加到 `bot` 对象上，然后在每个 Cog 的 `setup` 函数中手动从容器解析依赖，并将其传递给 Cog 的构造函数。**
-   **结论**: 此模式虽然需要在每个 Cog 的 `setup` 函数中增加几行样板代码，但它带来了极高的**清晰性、健总不变性和可测试性**。它完全消除了对框架间复杂交互的依赖，让代码的执行路径变得透明。该模式被确立为本项目的**依赖注入最佳实践**。

### 6.2 数据库初始化踩坑：`upgrade` vs `revision`

-   **背景**: 在初次搭建环境时，尝试直接运行 `alembic upgrade head` 来创建数据库表。
-   **踩坑记录**: 命令成功执行，但数据库中**没有任何表被创建**。
-   **原理解析**: `alembic upgrade` 命令的作用是**执行已经存在**的迁移脚本（位于 `alembic/versions/` 目录下）。而 `alembic revision --autogenerate` 的作用才是**检测模型变更并创建**新的迁移脚本。如果 `versions` 目录是空的，`upgrade` 自然无事可做。
-   **最终决策**: 数据库初始化的标准流程被确立为**两步**：先用 `alembic revision --autogenerate` 生成脚本，再用 `alembic upgrade head` 应用脚本。这一流程已被固化到本文档的"环境搭建"部分。

### **【v3.1 新增】6.3 测试踩坑：`fixture not found` 与测试隔离性**

-   **背景**: 在为多个不同的模块（如 `repositories` 和 `services`）编写数据库测试时，遇到了 `fixture 'db_session' not found` 错误，或者一个测试的数据库操作"污染"了下一个测试，导致 `AssertionError: assert 2 == 1`。
-   **踩坑记录**:
    1.  **Fixture Not Found**: 原因是 `conftest.py` 文件被放在了子目录（如 `tests/db/`）下，导致其定义的 fixture 无法被平级目录（如 `tests/services/`）中的测试文件访问。
    2.  **测试污染**: 原因是 `db_session` fixture 的实现没有使用正确的事务管理，导致上一个测试 `commit` 的数据遗留到了下一个测试中。
-   **原理解析**:
    1.  `pytest` 的 `conftest.py` 文件对其**所在目录及所有子目录**生效。为了让 fixture 全局可用，它**必须位于 `tests/` 根目录**。
    2.  可靠的数据库测试依赖于**完美的事务隔离**。每个测试都应该在一个独立的事务中运行，并在测试结束后**回滚**该事务，而不是提交。
-   **最终决策**: 我们在 `tests/conftest.py` 中实现了一个**生产级别的 `db_session` fixture**。它使用了**嵌套事务 (nested transaction)** 的模式：在测试开始时开启一个外层事务，测试结束后无论内部是否 `commit`，都回滚这个外层事务。这从根本上保证了每个测试函数都运行在一个绝对干净的数据库环境中。