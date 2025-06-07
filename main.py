# main.py

import asyncio
import logging
import sys

import discord
from discord.ext import commands # <--- 确保导入 commands

from src.core.config import settings
from src.core.container import Container

# -------------------- 日志配置 (推荐) --------------------
# 配置基础日志记录器
logging.basicConfig(
    # 设置日志级别，优先从 settings 中读取，否则默认为 INFO
    level=settings.LOG_LEVEL if hasattr(settings, 'LOG_LEVEL') else logging.INFO,
    # 日志格式：时间 [级别] 名称：消息
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    # 时间格式
    datefmt="%Y-%m-%d %H:%M:%S",
    # 日志输出流，默认为标准输出 (控制台)
    stream=sys.stdout,
)
# 获取当前模块的 logger 实例
logger = logging.getLogger(__name__)


# -------------------- Bot Intents (机器人意图) --------------------
# Intents 用于声明你的机器人需要从 Discord 网关接收哪些事件。
# 默认情况下，大多数特权 Intents (privileged intents) 是关闭的。
intents = discord.Intents.default()  # 获取默认的 Intents 集合
intents.message_content = True       # 启用消息内容 Intent，允许机器人读取消息内容 (特权)
intents.members = True               # 启用服务器成员 Intent，允许机器人接收成员加入/离开/更新等事件 (特权)
# 注意：特权 Intents (message_content, members, presence) 需要在 Discord Developer Portal 中为你的应用开启。


# -------------------- Bot 初始化 (确保使用 commands.Bot) --------------------
# 使用 discord.ext.commands.Bot 类来创建机器人实例，它提供了命令处理框架。
bot = commands.Bot(
    # command_prefix 是传统文本命令的前缀。
    # commands.when_mentioned_or("!") 允许机器人响应提及 (@BotName) 或 "!" 作为命令前缀。
    # 如果你的 Cog 主要依赖事件监听器 (如 on_message) 和/或应用命令 (斜杠命令)，
    # 并且不使用传统文本命令，可以将 command_prefix 设置为一个几乎不会被用户触发的值，
    # 或者根据需要选择合适的前缀。
    command_prefix=commands.when_mentioned_or("!"),
    intents=intents,  # 传递配置好的 Intents
    description="DcFriend Legacy Bot (using commands.Bot)", # 机器人的描述，可选
    # help_command=None, # 如果你想完全自定义帮助命令，可以设置为 None，然后自己实现。
)
# 重要说明：discord.py v2.x 中，discord.ext.commands.Bot 已经能够很好地处理 Cogs 和应用命令。
# 使用 commands.Bot 不会影响你使用这些现代功能。

# -------------------- 依赖注入容器初始化 --------------------
container = Container() # 实例化依赖注入容器
# 从 Pydantic Settings 模型 (settings) 加载配置到容器的配置提供者中
# settings.model_dump() 将 Pydantic 模型转换为字典
container.config.from_dict(settings.model_dump())

# -------------------- 关键：连接容器 (Wiring) --------------------
# `container.wire()` 是 `dependency-injector` 库的核心步骤。
# 它会扫描指定的模块和包，查找 `@inject` 装饰器和 `Provide` 占位符。
# 当找到时，它会将 `Provide` 占位符“连接”到容器中相应的服务实例。
# - `modules=[__name__]`: 将当前模块 (main.py) 添加到扫描列表。
#   如果 main.py 中有函数或类使用了 @inject，这将确保它们被正确处理。
# - `packages=["src.cogs"]`: 将 `src.cogs` 包添加到扫描列表。
#   这意味着 `src.cogs` 目录下的所有模块 (如 `chat_cog.py`) 都会被扫描。
#   这对于 Cogs 中的 `__init__` 方法或命令方法中通过 `@inject` 注入依赖至关重要。
# 此步骤必须在加载 Cogs (extensions) 之前完成，因为 Cogs 的初始化过程可能就需要注入的依赖。
# 如果不调用 .wire()，ChatCog 在实例化时接收到的 member_service 将是
# 一个 Provide 对象，而不是 MemberService 的实例，从而导致 AttributeError。

import src.cogs.chat_cog # <--- 显式导入，确保模块先被加载
container.wire(modules=[src.cogs.chat_cog]) # <--- 直接 wire 模块对象本身

# -------------------- Cog (扩展模块) 发现与加载 --------------------
# INITIAL_EXTENSIONS 列出了机器人启动时需要加载的 Cog 的模块路径。
# 路径格式是相对于项目根目录的点分路径，例如 "src.cogs.chat_cog" 指向 src/cogs/chat_cog.py。
INITIAL_EXTENSIONS = [
    "src.cogs.chat_cog",
    # "src.cogs.another_cog", # 如果有其他 Cog，也在这里添加
]

async def load_extensions():
    """异步函数，用于加载所有在 INITIAL_EXTENSIONS 中定义的 Cog。"""
    for extension_path in INITIAL_EXTENSIONS:
        try:
            # `bot.load_extension()` 异步加载指定的 Cog。
            # Cog 内部通常有一个名为 `setup(bot)` 的函数，用于将 Cog 注册到机器人。
            await bot.load_extension(extension_path)
            logger.info(f"成功加载扩展：{extension_path}")
        except commands.ExtensionError as e:
            # 如果加载过程中发生错误 (如 Cog 不存在、setup 函数错误等)，则记录错误。
            logger.error(f"加载扩展 {extension_path} 失败：{e}", exc_info=True)

# -------------------- Bot 事件处理 --------------------
@bot.event
async def on_ready():
    """当机器人成功连接到 Discord 并准备就绪时触发此事件。"""
    logger.info(f"机器人已登录为 {bot.user.name} (ID: {bot.user.id})")
    logger.info(f"已连接到 {len(bot.guilds)} 个服务器。")
    logger.info(f"Discord.py 版本：{discord.__version__}")
    logger.info("DcFriend Legacy 已准备就绪！")
    # 设置机器人的在线状态和正在玩的游戏/活动
    await bot.change_presence(activity=discord.Game(name="with your legacy"))

# -------------------- 主程序执行逻辑 --------------------
async def main_async():
    """主异步函数，负责初始化和启动机器人。"""
    await load_extensions() # 首先加载所有定义的 Cogs
    # 使用从 settings 中获取的 BOT_TOKEN 启动机器人并连接到 Discord
    await bot.start(settings.BOT_TOKEN)

def run_bot():
    """同步的启动函数，用于运行异步的 main_async 函数。"""
    try:
        # `asyncio.run()` 是在同步代码中运行异步函数的标准方式。
        asyncio.run(main_async())
    except KeyboardInterrupt:
        # 当用户按下 Ctrl+C 时，优雅地关闭机器人。
        logger.info("用户请求关闭机器人。正在退出...")
    except Exception as e:
        # 捕获并记录在机器人运行过程中发生的任何未处理的顶层异常。
        logger.error(f"发生未处理的异常：{e}", exc_info=True)

if __name__ == "__main__":
    # Python 脚本的入口点。
    # 当直接运行此文件时 (python main.py)，`__name__` 的值为 "__main__"，
    # 从而执行 run_bot() 函数启动机器人。
    run_bot()