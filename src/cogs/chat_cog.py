# src/cogs/chat_cog.py

import logging
import discord
from discord.ext import commands
from dependency_injector.wiring import inject, Provide
import asyncio

from src.core.container import Container # 引入容器
from src.services.member_service import MemberService
from src.services.ai_service import AIService
from src.db.models import Member as MemberModel # 引入数据库模型以进行类型提示

logger = logging.getLogger(__name__)

class ChatCog(commands.Cog):
    """
    处理与聊天相关的交互，特别是对机器人的直接提及。
    """

    # 关键点 1: 使用 @inject 装饰器注入服务
    # 类型提示要用 Provide[Container.service_name]
    @inject
    def __init__(
        self,
        bot: commands.Bot, # Bot 实例通常由 discord.py 自动传入
        member_service: MemberService = Provide[Container.member_service],
        ai_service: AIService = Provide[Container.ai_service],
    ):
        
        # --- 新增调试日志 ---
        logger.info(f"ChatCog.__init__ called.")
        logger.info(f"  Is 'member_service' a Provide object on entry? {isinstance(member_service, Provide)}") # 更直接的检查
        logger.info(f"  Type of 'member_service' param on entry: {type(member_service)}")
        logger.info(f"  Value of 'member_service' param on entry: {member_service}")
        logger.info(f"  Is 'ai_service' a Provide object on entry? {isinstance(ai_service, Provide)}") # 更直接的检查
        logger.info(f"  Type of 'ai_service' param on entry: {type(ai_service)}")
        # --- 结束新增调试日志 ---

        self.bot = bot
        self.member_service = member_service
        self.ai_service = ai_service
        logger.info("ChatCog initialized with injected services.")

    # 关键点 2: 监听 on_message 事件
    @inject
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        当机器人能看到的任何频道收到消息时调用。
        """
        # 1. 过滤消息：
        #    - 忽略机器人自己发的消息
        #    - 确保消息来自真实用户 (不是其他机器人，可选)
        #    - 检查消息是否是针对本机器人的（例如，以 @机器人 开头）
        if message.author == self.bot.user:
            return # 忽略自己发的消息

        if message.author.bot: # 可选：忽略其他机器人的消息
            # logger.debug(f"Ignoring message from other bot: {message.author.name}")
            return

        # 检查是否提到了机器人
        # bot.user.mention 是 '@机器人昵称' 这种形式
        # message.content.startswith(self.bot.user.mention) 是一个简单有效的检查方式
        # 或者，如果你的机器人有固定的前缀，也可以用那个
        is_mentioned = self.bot.user.mention in message.content.split() # 更准确的提及检查
        is_private_message = isinstance(message.channel, discord.DMChannel)

        if not (is_mentioned or is_private_message):
            # logger.debug(f"Message not for me: '{message.content[:50]}...' by {message.author.name}")
            return # 没有提到机器人，也不是私聊，则忽略

        logger.info(
            f"Received message from {message.author.name} in {'DM' if is_private_message else message.channel.name}: "
            f"'{message.content}'"
        )

        # 2. 获取或创建成员
        try:
            # message.author 可以是 discord.User (DM 中) 或 discord.Member (Guild 中)
            # 我们的 MemberService.get_or_create_member 设计上可以处理这两种情况
            db_member: MemberModel = await self.member_service.get_or_create_member(message.author)
            logger.info(f"Ensured member exists in DB: {db_member.name} (ID: {db_member.member_id})")
        except Exception as e:
            logger.error(f"Error getting or creating member {message.author.name}: {e}", exc_info=True)
            await message.reply("抱歉，我在同步你的信息时遇到了点小麻烦，请稍后再试。")
            return

        # 3. 提取用户输入 (去除提及等)
        user_input = message.content
        if is_mentioned and not is_private_message: # 如果是群聊中的提及
             # 移除所有对本机器人的提及，并去除首尾空格
            user_input = user_input.replace(self.bot.user.mention, "").strip()
       
        if not user_input and is_mentioned: # 如果提及了但没有其他内容
            user_input = "你好" # 或者一个默认的问候语，或者提示用户输入
            # await message.reply("你好呀！有什么可以帮你的吗？")
            # return

        if not user_input: # 经过处理后，如果没有有效输入（比如只有空格或完全是提及）
            logger.debug("Empty user input after stripping mention, ignoring.")
            # 也可以选择回复一个提示，比如 "你@我了，想说什么呢？"
            # await message.reply("你@我了，想说什么呢？如果想聊天，请在@我之后加上你的问题哦。")
            return


        # 4. 调用 AI 服务获取回复
        try:
            # 发送 "typing..." 指示器，让用户知道机器人在处理
            async with message.channel.typing():
                logger.debug(f"Sending to AI service for {db_member.name}: '{user_input}'")
                ai_response = await self.ai_service.get_simple_chat_response(user_input)
                logger.info(f"AI response for {db_member.name}: '{ai_response[:100]}...'")
        except Exception as e:
            logger.error(f"Error getting AI response for '{user_input}': {e}", exc_info=True)
            await message.reply("呜...我的大脑好像短路了，暂时不能回复你。稍后再试试吧！")
            return

        # 5. 发送回复
        if ai_response:
            try:
                # discord 消息长度限制为 2000 字符，需要处理超长回复
                if len(ai_response) > 2000:
                    logger.warning("AI response too long, truncating to 2000 characters.")
                    # 更优雅的处理可以是分多条消息发送
                    for i in range(0, len(ai_response), 2000):
                        await message.reply(ai_response[i:i+2000])
                        if i + 2000 < len(ai_response):
                            await asyncio.sleep(0.5) # 短暂延时避免速率限制
                else:
                    await message.reply(ai_response)
                
                # 可选：未来可以在这里添加 React 表情的逻辑
                # 例如：await message.add_reaction("👍") # 给用户消息点赞
                # 或 await sent_message.add_reaction("💡") # 给自己的回复点赞
                
            except discord.HTTPException as e:
                logger.error(f"Failed to send Discord reply: {e}", exc_info=True)
                # 可能的错误：权限不足、网络问题等
        else:
            logger.warning("AI service returned an empty response.")
            # 可以选择回复一个默认消息，或不回复
            # await message.reply("我好像没什么好说的了...")

# 关键点 3: 定义一个 setup 函数，用于 bot.load_extension
# 这个函数会被 discord.py 调用，当加载 Cog 时
# 它需要接收 bot 实例作为参数，并将 Cog 实例添加到 bot
async def setup(bot: commands.Bot):
    """
    当 Cog 被加载时由 discord.py 调用的入口点。
    它负责创建 Cog 实例并将其添加到机器人。
    依赖注入会在 Cog 实例化时自动发生 (因为我们用了@inject)。
    """
    # 注意：因为 ChatCog 的 __init__ 方法有 @inject 装饰，
    # dependency-injector 会自动处理依赖的注入。
    # 我们不需要手动从 container 中获取服务再传给 ChatCog 的构造函数。
    # bot 实例是 discord.py 自动传入的。
    await bot.add_cog(ChatCog(bot))
    logger.info("ChatCog has been added to the bot.")