import discord
from typing import Dict, Any

# 导入相关的服务和模型
from .member_service import MemberService
from .memory.abstract_memory_service import AbstractMemoryService
from .gemini_client import GeminiClient
from ..core.character_manager import CharacterManager
from ..core.character_model import Character


class AIService:
    """
    AI 服务类，负责处理所有与大型语言模型 (LLM) 相关的交互。
    它整合了角色管理、记忆、上下文处理和响应生成。
    """

    def __init__(
        self,
        llm_client: GeminiClient,
        character_manager: CharacterManager,
        member_service: MemberService,
        memory_service: AbstractMemoryService,
    ):
        """
        初始化 AI 服务。

        Args:
            llm_client: 用于与 LLM API (如 Gemini) 通信的客户端。
            character_manager: 管理 AI 角色的加载和信息。
            member_service: 管理用户信息。
            memory_service: 管理 AI 的长期和短期记忆。
        """
        self.llm_client = llm_client
        self.character_manager = character_manager
        self.member_service = member_service
        self.memory_service = memory_service
        self.active_character: Character | None = None

    async def _load_active_character(self):
        """如果当前没有激活的角色，则加载默认角色。"""
        if self.active_character is None:
            # 确保在需要时角色信息已经被加载
            self.active_character = await self.character_manager.load_character(
                "kanban_musume"
            )

    def _format_example_dialogue(self, character: Character) -> str:
        """格式化角色的示例对话，用于构建 few-shot prompt。"""
        return "\n".join(
            [
                f"User: {ex.user}\n{character.name}: {ex.bot}"
                for ex in character.example_dialogue
            ]
        )

    # =================================================================================
    # ✨ [核心升级] 新增的辅助函数，用于深度解析 Discord 消息 ✨
    # =================================================================================
    def _format_message_for_llm(self, message: discord.Message) -> str:
        """
        将一个 discord.Message 对象格式化为对 LLM 友好的、包含文本和 Embed 信息的字符串。
        这是让 AI 能够“读懂”富文本消息的关键。

        Args:
            message: 来自 discord.py 的消息对象。

        Returns:
            一个格式化后的字符串，准备好被送入 LLM。
        """
        # 优先使用服务器昵称 (display_name)，如果不在服务器中则使用用户名
        author_name = message.author.display_name

        # 提取消息的纯文本内容，并去除首尾空格
        content_text = message.clean_content.strip()

        # --- 处理 Embeds ---
        embed_texts = []
        if message.embeds:
            for embed in message.embeds:
                # 使用列表来收集单个 embed 的所有文本部分，便于格式化
                single_embed_parts = ["[嵌入内容开始]"]

                # 提取作者、标题和描述
                if embed.author and embed.author.name:
                    single_embed_parts.append(f"作者：{embed.author.name}")
                if embed.title:
                    single_embed_parts.append(f"标题：{embed.title}")
                if embed.description:
                    single_embed_parts.append(f"描述:\n{embed.description.strip()}")

                # 核心：提取所有字段 (Fields)，这是很多机器人信息卡片的主要内容
                if embed.fields:
                    field_texts = [
                        f"- {field.name}: {field.value}" for field in embed.fields
                    ]
                    single_embed_parts.append("字段:\n" + "\n".join(field_texts))

                # 关键：用文字告诉 AI 图片的存在，但暂时不处理图片内容本身
                # 这是为未来多模态输入做准备的第一步
                if embed.image and embed.image.url:
                    single_embed_parts.append("[提示：消息包含一张主图片]")
                if embed.thumbnail and embed.thumbnail.url:
                    single_embed_parts.append("[提示：消息包含一张缩略图]")

                # 提取页脚信息
                if embed.footer and embed.footer.text:
                    single_embed_parts.append(f"页脚：{embed.footer.text}")

                single_embed_parts.append("[嵌入内容结束]")

                # 将这个 embed 的所有部分合并成一个字符串
                embed_texts.append("\n".join(single_embed_parts))

        # --- 组合最终输出 ---
        final_message_parts = []
        # 只有在文本内容确实存在时才添加
        if content_text:
            final_message_parts.append(content_text)
        # 如果有解析出的 embed 文本，也添加进来
        if embed_texts:
            # 使用分隔符，以防一条消息有多个 embed
            final_message_parts.append("\n---\n".join(embed_texts))

        # 如果消息既没有文本也没有可解析的 embed（例如，只有文件附件），提供一个默认文本
        if not final_message_parts:
            return f"{author_name}: [发送了一个空消息或仅包含附件]"

        # 最终格式："作者：文本内容\n<格式化后的 embeds>"
        return f"{author_name}: {'\n'.join(final_message_parts)}"

    # =================================================================================
    # ✨ [核心升级] 重构上下文获取逻辑 ✨
    # =================================================================================
    async def _gather_context(self, message: discord.Message) -> Dict[str, Any]:
        """
        收集并构建用于生成响应的所有上下文信息。
        这包括用户信息、短期记忆 (最近的聊天记录) 和长期记忆。

        Args:
            message: 用户当前发送的消息对象。

        Returns:
            一个包含所有上下文信息的字典。
        """
        # 获取用户信息
        member = await self.member_service.get_or_create_member(message.author)
        user_info = f"User '{member.name}' (ID: {member.id}, Display Name: {message.author.display_name})"

        # --- 短期记忆 (聊天历史) ---
        # 使用 `before=message` 可以精确获取此消息之前的历史，避免重复
        history_iterator = message.channel.history(limit=10, before=message)
        # 调用新的辅助函数来格式化每一条历史消息
        history_formatted = [
            self._format_message_for_llm(msg) async for msg in history_iterator
        ]
        # history API 返回的是从新到旧的消息，我们需要反转它以符合对话的时间顺序
        short_term_memory = "\n".join(reversed(history_formatted))

        # --- 长期记忆检索 ---
        # 为了进行有效的记忆检索，我们需要一个简洁的查询字符串
        # 优先使用消息的文本内容
        query_for_memory = message.clean_content.strip()
        # 如果文本为空（例如，用户只发了一张图），则尝试使用 embed 的描述或标题作为查询
        if not query_for_memory and message.embeds:
            first_embed = message.embeds[0]
            if first_embed.description:
                query_for_memory = first_embed.description
            elif first_embed.title:
                query_for_memory = first_embed.title
            else:
                # 如果都没有，给一个通用描述
                query_for_memory = "用户发送的嵌入式内容"

        long_term_memories_list = await self.memory_service.retrieve_relevant_memories(
            member.id, query_for_memory
        )
        long_term_memory = (
            "\n".join([f"- {mem}" for mem in long_term_memories_list])
            if long_term_memories_list
            else "无相关记忆"
        )

        # --- 当前输入 ---
        # 同样使用新的辅助函数来格式化当前用户输入的消息
        current_input_formatted = self._format_message_for_llm(message)

        return {
            "user_info": user_info,
            "short_term_memory": short_term_memory,
            "long_term_memory": long_term_memory,
            "current_input": current_input_formatted,  # 使用格式化后的完整内容
        }

    async def generate_response(self, message: discord.Message) -> str:
        """
        生成 AI 的最终响应。

        这个方法是整个流程的协调者：
        1. 加载角色。
        2. 收集上下文。
        3. 构建最终的 prompt。
        4. 调用 LLM 客户端获取响应。

        Args:
            message: 用户发送的原始消息对象。

        Returns:
            一个由 LLM 生成的字符串响应。
        """
        # 确保角色已加载
        await self._load_active_character()
        character = self.active_character

        # 收集所有上下文信息
        context = await self._gather_context(message)

        # 使用模板和收集到的上下文，构建最终要发送给 LLM 的 prompt
        final_prompt = character.main_chat_prompt_template.format(
            persona_description=character.description,
            example_dialogue=self._format_example_dialogue(character),
            long_term_memory=context["long_term_memory"],
            short_term_memory=context["short_term_memory"],
            user_info=context["user_info"],
            current_input=context["current_input"],  # 这里现在包含了丰富的信息
            bot_name=character.name,
        )

        # (调试用) 打印最终的 prompt，这对于调试 prompt engineering 非常有用
        print("=" * 20 + " FINAL PROMPT TO LLM " + "=" * 20)
        print(final_prompt)
        print("=" * 60)

        # 调用 LLM 客户端并返回生成的文本
        return await self.llm_client.generate_text(final_prompt)
