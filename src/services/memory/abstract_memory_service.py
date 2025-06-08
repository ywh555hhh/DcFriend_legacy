from abc import ABC, abstractmethod
from typing import List


class AbstractMemoryService(ABC):
    @abstractmethod
    async def retrieve_relevant_memories(
        self, user_id: int, query_text: str
    ) -> List[str]:
        pass
