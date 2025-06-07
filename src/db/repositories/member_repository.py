# src/db/repositories/member_repository.py
from typing import Callable, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db.models import Member

class MemberRepository:
    """封装了所有与 Member 模型相关的数据库操作。"""
    def __init__(self, session_factory: Callable[[], AsyncSession]):
        self._session_factory = session_factory

    async def get_by_id(self, member_id: int) -> Optional[Member]:
        """通过 Discord ID 获取成员。"""
        async with self._session_factory() as session:
            stmt = select(Member).where(Member.id == member_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_or_create(self, member_id: int, name: str, display_name: Optional[str] = None) -> tuple[Member, bool]:
        """
        获取一个成员，如果不存在则创建。
        如果存在，则更新其 name 和 display_name (如果发生了变化)。
        返回 (成员对象，是否是新创建的布尔值)。
        """
        async with self._session_factory() as session:
            # 尝试获取成员
            member = await self.get_by_id(member_id)
            
            if member:
                # 如果成员存在，检查是否需要更新信息
                needs_update = False
                if member.name != name:
                    member.name = name
                    needs_update = True
                if member.display_name != display_name:
                    member.display_name = display_name
                    needs_update = True
                
                if needs_update:
                    session.add(member)
                    await session.commit()
                    await session.refresh(member)
                return member, False
            
            # 如果成员不存在，则创建
            new_member = Member(id=member_id, name=name, display_name=display_name)
            session.add(new_member)
            await session.commit()
            await session.refresh(new_member)
            return new_member, True