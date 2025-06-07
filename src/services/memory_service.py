# src/services/memory_service.py

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import discord

from src.db.models import Member, Event # 确保 Event 也被导入

class MemoryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_member(self, user: discord.User | discord.Member) -> Member:
        """
        根据 discord.User 或 discord.Member 对象，获取或创建数据库中的成员记录。
        这是确保每个与机器人互动的用户都在数据库中有记录的关键方法。
        """
        # 检查数据库中是否已存在该成员
        stmt = select(Member).where(Member.id == user.id)
        result = await self.session.execute(stmt)
        db_member = result.scalar_one_or_none()

        if db_member:
            # 如果找到了成员，检查他们的名字或昵称是否需要更新
            current_name = str(user)
            current_display_name = getattr(user, 'display_name', user.name)

            should_update = False
            if db_member.name != current_name:
                db_member.name = current_name
                should_update = True
            
            if db_member.display_name != current_display_name:
                db_member.display_name = current_display_name
                should_update = True
            
            # 只有在信息有变动时才提交，减少数据库写入
            if should_update:
                await self.session.commit()
                await self.session.refresh(db_member)

            return db_member
        else:
            # 如果没找到，创建一个新的 Member 实例
            print(f"INFO: Creating new member in DB for {user.name} ({user.id})")
            new_member = Member(
                id=user.id,
                name=str(user),
                display_name=getattr(user, 'display_name', user.name),
            )
            self.session.add(new_member)
            await self.session.commit()
            await self.session.refresh(new_member)
            return new_member

    # vvvvvvvvvv 新增的方法 vvvvvvvvvv
    async def add_message_event(self, message: discord.Message) -> Event:
        """
        将一条 discord.Message 记录为数据库中的一个 'message'类型的 Event。
        """
        # 1. 首先，确保消息的作者存在于数据库中
        #    这里复用了我们刚才写好的方法，体现了服务内部方法调用的优势
        author_member = await self.get_or_create_member(message.author)

        # 2. 创建一个新的 Event 对象
        print(f"INFO: Recording message from {author_member.name} in DB.")
        new_event = Event(
            event_id=message.id,
            event_type='message',
            content=message.content,
            author_id=author_member.id, # 关联到作者
            channel_id=message.channel.id,
            guild_id=message.guild.id if message.guild else None,
            created_at=message.created_at # 使用 discord 消息自带的精确时间
        )

        # 3. 将新事件添加到会话并提交到数据库
        self.session.add(new_event)
        await self.session.commit()
        await self.session.refresh(new_event)

        return new_event
    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^   