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
    level=getattr(settings, "LOG_LEVEL", "INFO"),
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
    此函数负责初始化所有组件、配置并启动机器人。
    """
    logger.info("开始初始化机器人...")

    # 步骤 1: 创建依赖注入容器实例。
    # 容器负责管理我们应用中所有服务的生命周期和依赖关系。
    # 它在 src/core/container.py 中定义。
    logger.info("创建依赖注入容器...")
    container = Container()

    # 【架构核心】我们不使用 @inject 自动织入 (wiring)。
    # 而是采用更健壮的手动注入模式，详见步骤 4 和各个 Cog 的 setup 函数。

    # 步骤 2: (信息) 配置加载。
    # pydantic-settings 会在导入 `src.core.config.settings` 时自动从 .env 文件加载配置。
    # 我们的容器 (`Container`) 内部已经配置为直接使用这个 settings 对象。
    # 因此，此处无需进行显式的配置加载操作。

    # 步骤 3: 定义并创建机器人实例。
    logger.info("定义机器人意图 (Intents)...")
    intents = discord.Intents.default()
    intents.message_content = True  # 订阅消息内容事件，以便机器人能读取消息
    intents.members = True  # 订阅服务器成员事件，例如新成员加入

    logger.info("创建 commands.Bot 实例...")
    bot = commands.Bot(
        # 设置命令前缀，这里是 "!" 或 @机器人
        command_prefix=commands.when_mentioned_or("!"),
        intents=intents,
        description="一个拥有长期记忆的社群伙伴。",
    )

    # 步骤 4: 【关键】将容器附加到 bot 实例上。
    # 这是实现我们“手动注入”模式的桥梁。
    # 它使得在每个 Cog 的 setup 函数中，我们都可以通过 `bot.container` 访问到唯一的容器实例，
    # 从而解析出该 Cog 所需的服务。
    bot.container = container
    logger.info("依赖注入容器已附加到 bot 实例。")

    # 步骤 5: 启动机器人，并使用 `async with` 来优雅地处理其生命周期。
    # `async with bot:` 会自动处理登录、连接保持和最终的登出清理。
    async with bot:
        # 定义需要加载的扩展模块 (Cogs) 列表。
        # 添加新功能模块时，只需在此列表中增加其路径即可。
        extensions_to_load = [
            "src.cogs.chat_cog"
            # 例如："src.cogs.admin_cog", "src.cogs.music_cog"
        ]

        logger.info(f"准备加载扩展模块：{extensions_to_load}")
        # 循环加载所有定义的扩展。
        for extension in extensions_to_load:
            try:
                # `load_extension` 会导入模块并调用其 `setup` 函数。
                # 在我们的架构中，每个 Cog 的 `setup` 函数负责从 `bot.container`
                # 解析依赖并实例化该 Cog。
                await bot.load_extension(extension)
                logger.info(f"成功加载扩展模块：{extension}")
            except Exception as e:
                # 如果某个 Cog 加载失败，记录详细错误但不会让整个程序崩溃，
                # 以便调试和不影响其他功能的运行。
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
        # 捕获特定的登录失败异常，给出更明确、可操作的错误信息。
        logger.critical(
            "机器人 Token 无效或不正确，登录失败。请检查你的 .env 文件中的 BOT_TOKEN。"
        )
        sys.exit(1)
    except Exception as e:
        # 捕获在主函数之外发生的、未被处理的严重异常，确保问题能被记录。
        logger.critical(f"在启动过程中发生未处理的严重异常。", exc_info=e)
        sys.exit(1)
