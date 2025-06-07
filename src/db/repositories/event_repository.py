# src/db/repositories/event_repository.py
from typing import Callable, Sequence, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db.models import Event

class EventRepository:
    """封装了所有与 Event 模型相关的数据库操作。"""
    def __init__(self, session_factory: Callable[[], AsyncSession]):
        self._session_factory = session_factory

    async def create_event(
        self, 
        event_id: int, 
        event_type: str, 
        author_id: int,
        content: Optional[str] = None, 
        channel_id: Optional[int] = None, 
        guild_id: Optional[int] = None
    ) -> Event:
        """创建一个新的事件并存入数据库。"""
        new_event = Event(
            event_id=event_id,
            event_type=event_type,
            author_id=author_id,
            content=content,
            channel_id=channel_id,
            guild_id=guild_id
        )
        async with self._session_factory() as session:
            session.add(new_event)
            await session.commit()
            await session.refresh(new_event)
            return new_event

    async def get_recent_dialogue_events(self, limit: int = 10) -> Sequence[Event]:
        """获取最近的对话事件，用于构建上下文。"""
        async with self._session_factory() as session:
            stmt = (
                select(Event)
                .where(Event.event_type == 'dialogue') # 假设对话事件类型为'dialogue'
                .order_by(Event.created_at.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            # 返回的是一个序列，我们需要反转它，让最早的在前面
            events = result.scalars().all()
            return events[::-1]