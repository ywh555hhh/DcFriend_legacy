# src/main.py

import asyncio
import logging
import sys

import discord
from discord.ext import commands # <--- 确保导入 commands

from src.core.config import settings
from src.core.container import Container

# -------------------- Logging Setup (推荐) --------------------
logging.basicConfig(
    level=settings.LOG_LEVEL if hasattr(settings, 'LOG_LEVEL') else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


# -------------------- Bot Intents --------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True


# -------------------- Bot Initialization (确保使用 commands.Bot) --------------------
# 使用 discord.ext.commands.Bot
# command_prefix 是传统命令的前缀。如果你的 Cog 主要依赖监听器 (on_message)
# 和未来的应用命令 (slash commands)，你可以将 command_prefix 设置为一个几乎不会用到的值，
# 或者使用 commands.when_mentioned_or(...) 如果你希望机器人能响应提及作为前缀。
# 对于你当前的 ChatCog，它监听 on_message 并且检查提及，所以 command_prefix 的直接影响不大，
# 但对于 commands.Bot 的标准初始化，它通常是需要的。
bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"), # 或者 "!" , "$" 等，或一个你不会用的前缀
    intents=intents,
    description="DcFriend Legacy Bot (using commands.Bot)" # 可选
    # help_command=None, # 如果要自定义帮助命令
)
# 重要：在 discord.py v2.x 中，discord.ext.commands.Bot 已经能够很好地处理 Cogs 和应用命令。
# 你不需要担心因为用了 commands.Bot 而失去这些功能。

# -------------------- Container Initialization --------------------
container = Container()
container.config.from_dict(settings.model_dump())

# -------------------- Cog Discovery and Loading --------------------
INITIAL_EXTENSIONS = [
    "src.cogs.chat_cog",
]

async def load_extensions():
    for extension_path in INITIAL_EXTENSIONS:
        try:
            await bot.load_extension(extension_path)
            logger.info(f"Successfully loaded extension: {extension_path}")
        except commands.ExtensionError as e:
            logger.error(f"Failed to load extension {extension_path}: {e}", exc_info=True)

# -------------------- Bot Events --------------------
@bot.event
async def on_ready():
    logger.info(f"Bot logged in as {bot.user.name} (ID: {bot.user.id})")
    logger.info(f"Connected to {len(bot.guilds)} guilds.")
    logger.info(f"Discord.py version: {discord.__version__}")
    logger.info("DcFriend Legacy is ready to serve!")
    await bot.change_presence(activity=discord.Game(name="with your legacy"))

# -------------------- Main Execution --------------------
async def main_async():
    await load_extensions()
    await bot.start(settings.BOT_TOKEN)

def run_bot():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user. Exiting...")
    except Exception as e:
        logger.error(f"An unhandled exception occurred: {e}", exc_info=True)

if __name__ == "__main__":
    run_bot()