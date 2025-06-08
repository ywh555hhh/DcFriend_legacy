import asyncio
import logging
import discord
from discord.ext import commands

# 我们只需要导入 AIService 的类型提示，因为这是我们唯一的直接依赖
from src.services.ai_service import AIService

# 获取此模块的日志记录器
logger = logging.getLogger(__name__)


class ChatCog(commands.Cog):
    """
    【交互层】处理与聊天相关的交互，特别是对机器人的直接提及。

    这个 Cog 的核心职责是作为 Discord 事件与内部服务之间的“桥梁”。
    它监听 `on_message` 事件，进行最基本的过滤，然后将 `discord.Message` 对象
    直接传递给 `AIService` 进行处理。它不包含任何复杂的业务逻辑。
    """

    # 构造函数非常“干净”，它只接收已经准备好的 AIService 实例。
    def __init__(self, bot: commands.Bot, ai_service: AIService):
        """
        初始化 ChatCog。

        Args:
            bot (commands.Bot): 当前的机器人实例。
            ai_service (AIService): 用于处理所有 AI 相关业务逻辑的核心服务。
        """
        self.bot = bot
        self.ai_service = ai_service
        logger.info(
            "ChatCog instance has been successfully created and wired with AIService."
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        监听所有消息，并对提及机器人的消息作出响应。
        """
        # 1. 【过滤】快速过滤掉无需处理的消息，避免不必要的计算。
        # - 忽略机器人自身或其他机器人发出的消息。
        # - 只响应在频道中被明确 @提及 的消息。
        if message.author.bot or not self.bot.user.mentioned_in(message):
            return

        # 日志记录：记录收到了需要处理的消息
        logger.info(
            f"Received mention from '{message.author.name}' in channel '{message.channel}': '{message.clean_content[:100]}'"
        )

        # 2. 【委派】将任务完全委托给核心服务层。
        # 我们将整个 `message` 对象传递过去，因为服务层需要从中提取
        # 作者信息、频道历史（短期记忆）等多种上下文。
        try:
            # 发送 "typing..." 指示器，提升用户体验
            async with message.channel.typing():
                # 调用核心 AI 服务来生成回复
                ai_response = await self.ai_service.generate_response(message)
                logger.info(
                    f"AI response generated for '{message.author.name}': '{ai_response[:100]}...'"
                )

            # 3. 【回复】处理并发送 AI 服务的返回结果。
            if ai_response:
                # 优雅地处理 Discord 消息长度限制 (2000 字符)
                if len(ai_response) > 2000:
                    logger.warning(
                        "AI response is too long, splitting into multiple messages."
                    )
                    # 分多条消息发送
                    for i in range(0, len(ai_response), 2000):
                        await message.reply(ai_response[i : i + 2000])
                        # 在消息之间添加一个短暂延时，可以改善阅读体验并避免潜在的速率限制
                        await asyncio.sleep(0.5)
                else:
                    await message.reply(ai_response)
            else:
                # 如果 AI 服务因某种原因返回了空响应，也给用户一个反馈
                logger.warning("AI service returned an empty or null response.")
                await message.reply("我好像没什么好说的了，换个话题试试？")

        except Exception as e:
            # 捕获服务层可能抛出的任何异常，并向用户发送友好的错误消息
            logger.error(
                f"An uncaught exception occurred while processing message from '{message.author.name}': {e}",
                exc_info=True,
            )
            await message.reply(
                "呜...我的大脑好像短路了，暂时不能回复你。请稍后再试试吧！"
            )


async def setup(bot: commands.Bot):
    """
    【依赖注入入口】此函数是 discord.py 加载扩展时的入口点。

    它负责从附加到 bot 的容器中解析出 `AIService`，并用它来实例化 `ChatCog`。
    这是我们项目中“手动依赖注入”模式的核心实践。
    """
    logger.info("Setting up ChatCog...")

    # 从 bot 对象上获取在 main.py 中附加的全局容器
    container = bot.container
    if not container:
        raise RuntimeError("Dependency Injection Container not found on bot instance.")

    try:
        # 从容器中显式地解析（创建）我们需要的 AIService 实例
        ai_service_instance = container.ai_service()

        # 将完全配置好的 Cog 添加到机器人中
        await bot.add_cog(ChatCog(bot=bot, ai_service=ai_service_instance))
        logger.info("ChatCog has been successfully set up and added to the bot.")

    except Exception as e:
        # 如果在解析或实例化过程中出现任何问题，我们能在这里捕获到清晰的错误
        logger.critical(
            f"Failed to setup ChatCog due to a dependency resolution or instantiation error.",
            exc_info=True,
        )
        # 重新抛出异常，这将导致 `load_extension` 失败，以便在主日志中清晰地看到问题
        raise
