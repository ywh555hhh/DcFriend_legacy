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
# 这是专业的应用开发中的良好实践。
# 它能让我们在控制台看到清晰、格式化的日志输出，而不是简单的 print()。
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


# -------------------- 2. 定义机器人的意图 (Bot Intents) --------------------
# Intents 像是一份“订阅清单”，我们告诉 Discord 我们关心哪些类型的事件。
# 如果不订阅，Discord 就不会把相应的事件推送给我们，以节省资源。
intents = discord.Intents.default()
# 订阅“消息内容”事件。这是让机器人能够读取消息文本所必需的，需要在开发者门户网站手动开启。
intents.message_content = True
# 订阅“服务器成员”事件。这有助于机器人获取成员加入/离开/更新等信息。
intents.members = True


# -------------------- 3. 初始化机器人核心 (Bot Initialization) --------------------
# 我们使用 `commands.Bot`，这是 `discord.py` 提供的功能更全面的客户端类。
# 它不仅能处理事件，还内置了对命令（传统命令和应用命令）的支持。
bot = commands.Bot(
    # 设置命令前缀。即使我们主要使用事件监听器，这也是一个好的实践。
    # `when_mentioned_or` 允许用户通过 @机器人 或者 "!" 来触发命令。
    command_prefix=commands.when_mentioned_or("!"),
    intents=intents,
    description="一个拥有长期记忆的社群伙伴。"
)


# -------------------- 4. 依赖注入容器的初始化与接线 (DI Container & Wiring) --------------------
# 这是我们整个架构的灵魂所在，连接后端服务与 Discord 前端的桥梁。

# 步骤 4a: 创建容器实例。这是我们所有服务的“总装车间”。
container = Container()

# 步骤 4b: 执行“接线”(Wiring)。这是整个 DI 流程中最关键的一步。
# 它告诉容器：“请扫描以下模块，并准备好为其中被 @inject 装饰的函数/方法提供依赖。”
# 这个操作必须在加载这些模块 (`load_extension`) 之前完成。
container.wire(modules=[
    "src.cogs.chat_cog",
    # 如果未来有更多 cogs，在这里添加它们的路径，例如："src.cogs.admin_cog"
])

# 步骤 4c: 将容器实例附加到 bot 对象上。
# 这是一个非常优雅的技巧，使得我们可以在任何能访问到 `bot` 对象的地方
# (比如在 Cog 的 setup 函数中) 轻松地取回我们的容器。
bot.container = container


# -------------------- 5. 加载扩展模块 (Cogs) --------------------
# Cogs 是 `discord.py` 用来组织代码的最佳方式。我们将不同的功能放在不同的 Cog 文件中。

# 定义一个初始要加载的 Cog 列表。
INITIAL_EXTENSIONS = [
    "src.cogs.chat_cog",
]

async def load_extensions():
    """一个异步函数，负责加载所有在 INITIAL_EXTENSIONS 中定义的 Cog。"""
    for extension_path in INITIAL_EXTENSIONS:
        try:
            # `bot.load_extension` 会导入指定的模块，并调用其底部的 `setup` 函数。
            await bot.load_extension(extension_path)
            logger.info(f"成功加载扩展模块：{extension_path}")
        except commands.ExtensionError as e:
            # 如果加载失败，打印详细的错误信息，但程序不会崩溃。
            logger.error(f"加载扩展模块失败 {extension_path}: {e}", exc_info=True)


# -------------------- 6. 定义机器人的核心事件回调 (Bot Events) --------------------

@bot.event
async def on_ready():
    """当机器人成功连接到 Discord 并准备好工作时，这个事件会被触发。"""
    logger.info(f"机器人已登录：{bot.user.name} (ID: {bot.user.id})")
    logger.info(f"已连接到 {len(bot.guilds)} 个服务器。")
    logger.info(f"discord.py 版本：{discord.__version__}")
    logger.info("看板娘已准备就绪，开始服务！")
    # 设置机器人的“正在玩”状态
    await bot.change_presence(activity=discord.Game(name="观察世界"))


# -------------------- 7. 主程序执行入口 (Main Execution) --------------------

async def main_async():
    """异步主函数，封装了启动逻辑。"""
    # 在启动机器人之前，先加载所有扩展模块。
    await load_extensions()
    # 使用从 settings 中读取的 token 来启动机器人。
    # 这会开始连接到 Discord 的 WebSocket，并进入事件监听循环。
    await bot.start(settings.BOT_TOKEN)

def run_bot():
    """同步的启动器函数，负责运行异步主函数并处理异常。"""
    try:
        # 运行异步主程序
        asyncio.run(main_async())
    except KeyboardInterrupt:
        # 优雅地处理用户按 Ctrl+C 的情况
        logger.info("用户请求关闭机器人。正在退出...")
    except Exception as e:
        # 捕获其他所有意外的错误，并记录日志。
        logger.critical(f"发生未处理的严重异常：{e}", exc_info=True)

# 经典的 Python 入口点检查
if __name__ == "__main__":
    run_bot()