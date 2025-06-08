from typing import List
from .abstract_memory_service import AbstractMemoryService


class HardcodedMemoryService(AbstractMemoryService):
    async def retrieve_relevant_memories(
        self, user_id: int, query_text: str
    ) -> List[str]:
        print(
            f"DEBUG: HardcodedMemoryService called for user {user_id}. Returning predefined memories."
        )
        return [
            "看板娘记得上次和用户 A 讨论过 Python 协程。",
            "看板娘知道用户 B 最喜欢的游戏是《赛博朋克 2077》。",
            "看板娘被设定为喜欢喝电子羊奶，对猫薄荷过敏。",
        ]
