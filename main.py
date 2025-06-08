# main.py

import asyncio
import logging
import sys

import discord
from discord.ext import commands

# 导入我们自己编写的核心模块
from src.core.config import settings
from src.core.container import Container

# -------------------- 1. 日志系统设置 (Logging Setup) --------------------
# 配置一个专业的日志系统，以便在控制台看到清晰、格式化的日志输出。
# 这对于调试和监控机器人的运行状态至关重要。
logging.basicConfig(
    # 设置日志级别，可以从配置中读取，如果配置中没有则默认为 INFO
    level=getattr(settings, 'LOG_LEVEL', 'INFO'),
    # 设置日志格式：时间 [日志级别] 模块名：日志消息
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    # 设置时间格式
    datefmt="%Y-%m-%d %H:%M:%S",
    # 将日志输出到标准输出（控制台）
    stream=sys.stdout,
)
# 获取一个针对当前文件 (__main__) 的日志记录器实例
logger = logging.getLogger(__name__)


# -------------------- 2. 主执行函数 (Main Execution Function) --------------------
async def main():
    """
    机器人主程序入口。
    严格遵循 dependency-injector 和 discord.py 的官方最佳实践。
    """
    logger.info("开始初始化机器人...")

    # 步骤 1: 创建依赖注入容器实例。
    # 容器负责管理我们应用中所有服务的生命周期和依赖关系。
    logger.info("创建依赖注入容器...")
    container = Container()
    
    # 根据 dependency-injector 文档，如果容器类中定义了 wiring_config，
    # 实例化容器时会自动触发 .wire()。但如果没有定义，或者需要更灵活的控制，
    # 手动调用 .wire() 是必须的。我们的场景需要在加载 Cogs 前手动调用。
    # 我们将在加载扩展前进行此操作。

    # 步骤 2: 从我们的配置系统加载配置到容器中。
    # (这一步在你的 container.py 中已经通过 pydantic-settings 自动完成了)
    # 如果你的 container.py 依赖于外部调用，可以取消下面这行注释：
    # logger.info("从 settings 加载配置到容器...")
    # container.config.from_pydantic(settings)

    # 步骤 3: 定义并创建机器人实例。
    logger.info("定义机器人意图 (Intents)...")
    intents = discord.Intents.default()
    intents.message_content = True  # 订阅消息内容事件，以便机器人能读取消息
    intents.members = True          # 订阅服务器成员事件，例如新成员加入

    logger.info("创建 commands.Bot 实例...")
    bot = commands.Bot(
        command_prefix=commands.when_mentioned_or("!"),
        intents=intents,
        description="一个拥有长期记忆的社群伙伴。"
    )

    # 步骤 4 (可选但推荐): 将容器附加到 bot 实例上。
    # 这使得在项目的任何地方（特别是测试和 Cogs 中）都可以通过 `bot.container` 方便地访问到容器。
    # 这是一种服务定位器模式的便利补充，但不替代依赖注入。
    bot.container = container
    logger.info("容器已附加到 bot 实例。")

    # 步骤 5: 启动机器人，并使用 `async with` 来优雅地处理其生命周期。
    # `async with bot:` 会自动处理登录、连接保持和最终的登出清理。
    async with bot:
        # 定义需要加载的扩展模块 (Cogs) 列表。
        extensions_to_load = [
            "src.cogs.chat_cog"
            # 未来有更多 Cogs, 在这里添加它们的路径，例如："src.cogs.admin_cog"
        ]
        
        # -------------------- 【关键修复点：执行织入 (Wiring)】 --------------------
        # 在加载任何 Cog 之前，必须先调用 `container.wire()`。
        # 这个操作会遍历指定的模块（这里是 `extensions_to_load` 列表中的模块），
        # 找到所有被 `@inject` 装饰的函数/方法，并修改它们，
        # 使得 `Provide[...]` 占位符在函数被调用时能被替换成真正的服务实例。
        # 如果不执行这一步，Cog 在初始化时接收到的将是 `Provide` 对象本身，而不是服务。
        logger.info(f"正在为模块 {extensions_to_load} 执行依赖注入织入 (wiring)...")
        container.wire(modules=extensions_to_load)
        logger.info("织入操作完成。现在可以安全加载扩展了。")
        # --------------------------------------------------------------------------

        logger.info(f"准备加载扩展模块：{extensions_to_load}")
        # 循环加载所有定义的扩展。
        for extension in extensions_to_load:
            try:
                # `load_extension` 会导入模块并调用其 `setup` 函数。
                # 由于我们已经完成了 wiring，`setup` 函数在创建 Cog 实例时，
                # 依赖项将被正确注入。
                await bot.load_extension(extension)
                logger.info(f"成功加载扩展模块：{extension}")
            except Exception as e:
                # 如果某个 Cog 加载失败，记录详细错误但不会让整个程序崩溃。
                logger.error(f"加载扩展模块失败 {extension}.", exc_info=e)
        
        logger.info("所有扩展已加载。准备启动并连接到 Discord...")
        # 启动机器人并使用从 settings 中读取的 token 进行连接。
        await bot.start(settings.BOT_TOKEN)

# -------------------- 3. 程序入口点 (Script Entrypoint) --------------------
if __name__ == "__main__":
    try:
        # 使用 asyncio.run() 启动异步主函数，这是现代 Python 的标准做法。
        asyncio.run(main())
    except KeyboardInterrupt:
        # 优雅地处理用户通过 Ctrl+C 终止程序的情况。
        logger.info("用户请求关闭机器人。程序已终止。")
        sys.exit(0)
    except discord.LoginFailure:
        # 捕获特定的登录失败异常，给出更明确的错误信息。
        logger.critical("机器人 Token 无效或不正确，登录失败。请检查你的 .env 文件中的 BOT_TOKEN。")
        sys.exit(1)
    except Exception as e:
        # 捕获在主函数之外发生的、未被处理的严重异常。
        logger.critical(f"在启动过程中发生未处理的严重异常。", exc_info=e)
        sys.exit(1)