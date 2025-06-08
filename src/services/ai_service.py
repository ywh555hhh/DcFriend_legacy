import discord
from typing import Dict, Any

from .member_service import MemberService
from .memory.abstract_memory_service import AbstractMemoryService
from .gemini_client import GeminiClient
from ..core.character_manager import CharacterManager
from ..core.character_model import Character


class AIService:
    def __init__(
        self,
        llm_client: GeminiClient,
        character_manager: CharacterManager,
        member_service: MemberService,
        memory_service: AbstractMemoryService,
    ):
        self.llm_client = llm_client
        self.character_manager = character_manager
        self.member_service = member_service
        self.memory_service = memory_service
        self.active_character: Character | None = None

    async def _load_active_character(self):
        if self.active_character is None:
            self.active_character = await self.character_manager.load_character(
                "kanban_musume"
            )

    def _format_example_dialogue(self, character: Character) -> str:
        return "\n".join(
            [
                f"User: {ex.user}\n{character.name}: {ex.bot}"
                for ex in character.example_dialogue
            ]
        )

    async def _gather_context(self, message: discord.Message) -> Dict[str, Any]:
        member = await self.member_service.get_or_create_member(message.author)
        user_info = f"User '{member.name}' (ID: {member.id})"
        history = [
            f"{msg.author.name}: {msg.clean_content}"
            async for msg in message.channel.history(limit=10)
        ]
        short_term_memory = "\n".join(reversed(history))
        long_term_memories_list = await self.memory_service.retrieve_relevant_memories(
            member.id, message.clean_content
        )
        long_term_memory = (
            "\n".join([f"- {mem}" for mem in long_term_memories_list])
            if long_term_memories_list
            else "无相关记忆"
        )

        return {
            "user_info": user_info,
            "short_term_memory": short_term_memory,
            "long_term_memory": long_term_memory,
            "current_input": message.clean_content,
        }

    async def generate_response(self, message: discord.Message) -> str:
        await self._load_active_character()
        character = self.active_character
        context = await self._gather_context(message)

        final_prompt = character.main_chat_prompt_template.format(
            persona_description=character.description,
            example_dialogue=self._format_example_dialogue(character),
            long_term_memory=context["long_term_memory"],
            short_term_memory=context["short_term_memory"],
            user_info=context["user_info"],
            current_input=context["current_input"],
            bot_name=character.name,
        )

        print("=" * 20 + " FINAL PROMPT TO LLM " + "=" * 20)
        print(final_prompt)
        print("=" * 60)

        return await self.llm_client.get_text_response(final_prompt)
