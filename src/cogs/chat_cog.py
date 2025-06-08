import asyncio
import logging

import discord
from discord.ext import commands

# 我们直接从各自的模块导入服务和模型类，用于类型提示和实例化
from src.db.models import Member as MemberModel
from src.services.ai_service import AIService
from src.services.member_service import MemberService

# 获取此模块的日志记录器
logger = logging.getLogger(__name__)


class ChatCog(commands.Cog):
    """
    处理与聊天相关的交互，特别是对机器人的直接提及。
    这个 Cog 的依赖项由其 setup 函数在加载时注入。
    """

    # 构造函数现在非常“干净”，它只接收已经准备好的服务实例。
    # 它不关心这些服务是如何创建的，只关心它们的类型和功能。
    def __init__(
        self,
        bot: commands.Bot,
        member_service: MemberService,
        ai_service: AIService,
    ):
        """
        初始化 ChatCog。

        Args:
            bot (commands.Bot): 当前的机器人实例。
            member_service (MemberService): 用于处理成员数据的服务。
            ai_service (AIService): 用于与大语言模型交互的服务。
        """
        self.bot = bot
        self.member_service = member_service
        self.ai_service = ai_service

        # 可以在这里添加一些断言或类型检查，以确保依赖项被正确传入
        if not isinstance(member_service, MemberService):
            raise TypeError(f"Expected MemberService, but got {type(member_service)}")
        if not isinstance(ai_service, AIService):
            raise TypeError(f"Expected AIService, but got {type(ai_service)}")

        logger.info("ChatCog instance created with explicitly passed service instances.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        监听所有消息，并对提及机器人的消息作出响应。
        """
        # 1. 过滤掉不应处理的消息
        if message.author == self.bot.user or message.author.bot:
            return

        # 2. 检查机器人是否被提及或是否为私聊
        # bot.user.mentioned_in(message) 是一个比字符串检查更可靠的方法
        is_mentioned = self.bot.user.mentioned_in(message)
        is_private_message = isinstance(message.channel, discord.DMChannel)

        if not (is_mentioned or is_private_message):
            return

        logger.info(
            f"Received relevant message from {message.author.name} "
            f"in {'DM' if is_private_message else '#' + message.channel.name}: "
            f"'{message.content}'"
        )

        # 3. 获取或创建数据库中的成员记录
        try:
            db_member: MemberModel = await self.member_service.get_or_create_member(message.author)
            logger.info(f"Ensured member exists in DB: {db_member.name} (ID: {db_member.id})")
        except Exception as e:
            logger.error(f"Error getting/creating member {message.author.name}: {e}", exc_info=True)
            await message.reply("抱歉，我在同步你的信息时遇到了点小麻烦，请稍后再试。")
            return

        # 4. 清理用户输入，移除提及部分
        # 使用 discord.py 提供的工具类来移除提及，更健壮
        user_input = discord.utils.remove_markdown(message.content)
        # 进一步清理可能存在的机器人用户名提及
        user_input = user_input.replace(f'@{self.bot.user.name}', '').strip()

        if not user_input:
            # 如果用户只@了机器人而没说别的话
            await message.reply("你好呀！有什么可以帮你的吗？或者想聊点什么？")
            return

        # 5. 调用 AI 服务并处理响应
        try:
            # 发送 "typing..." 指示器，提升用户体验
            async with message.channel.typing():
                logger.debug(f"Sending to AI service for {db_member.name}: '{user_input}'")
                ai_response = await self.ai_service.get_simple_chat_response(user_input)
                logger.info(f"AI response for {db_member.name}: '{ai_response[:100]}...'")

            # 6. 发送回复
            if ai_response:
                # 处理 Discord 消息长度限制 (2000 字符)
                if len(ai_response) > 2000:
                    logger.warning("AI response is too long, splitting into multiple messages.")
                    # 分多条消息发送
                    for i in range(0, len(ai_response), 2000):
                        await message.reply(ai_response[i:i+2000])
                        await asyncio.sleep(0.5) # 短暂延时以避免速率限制
                else:
                    await message.reply(ai_response)
            else:
                logger.warning("AI service returned an empty or null response.")
                await message.reply("我好像没什么好说的了，换个话题试试？")

        except Exception as e:
            logger.error(f"Error during AI processing or sending reply: {e}", exc_info=True)
            await message.reply("呜...我的大脑好像短路了，暂时不能回复你。请稍后再试试吧！")


async def setup(bot: commands.Bot):
    """
    此函数是 discord.py 加载扩展时的入口点。
    它负责从附加到 bot 的容器中解析服务，并用这些服务来实例化 Cog。
    这是依赖注入发生的核心位置。
    """
    logger.info("Setting up ChatCog...")

    container = bot.container
    if not container:
        raise RuntimeError("Dependency Injection Container has not been attached to the bot instance.")

    try:
        # 从容器中显式地解析（创建）我们需要的服务实例
        member_service_instance = container.member_service()
        ai_service_instance = container.ai_service()

        # 创建 ChatCog 实例，并将解析出的服务作为参数传入
        cog_instance = ChatCog(
            bot=bot,
            member_service=member_service_instance,
            ai_service=ai_service_instance
        )

        # 将完全配置好的 Cog 添加到机器人中
        await bot.add_cog(cog_instance)
        logger.info("ChatCog has been successfully created and added to the bot.")

    except Exception as e:
        # 如果在解析或实例化过程中出现任何问题，我们能在这里捕获到清晰的错误
        logger.critical("Failed to setup ChatCog due to a dependency resolution or instantiation error.", exc_info=e)
        # 重新抛出异常，这将导致 `load_extension` 失败，以便在主日志中清晰地看到问题
        raise