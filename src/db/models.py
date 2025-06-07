# src/db/models.py

import datetime
from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    String,
    Text
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship
)
from sqlalchemy.sql import func

# 1. 定义一个所有模型都会继承的基类
class Base(DeclarativeBase):
    pass

# 2. 定义 members 表的模型
class Member(Base):
    __tablename__ = "members"

    # 字段定义
    # 用户的 Discord ID，作为主键。使用 BigInteger 因为 Discord ID 很大。
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    
    # 用户的 Discord 名字 (例如 "username#1234")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # 用户在服务器的昵称
    display_name: Mapped[str] = mapped_column(String(255), nullable=True)

    # 记录创建和更新时间，使用数据库服务器的当前时间作为默认值
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 定义关系：一个 Member 可以有多个 Event
    # back_populates="author" 会在 Event 模型中创建一个反向关系，名为 "author"
    events: Mapped[list["Event"]] = relationship("Event", back_populates="author")

    def __repr__(self) -> str:
        return f"<Member(id={self.id}, name='{self.name}')>"

# 3. 定义 events 表的模型
class Event(Base):
    __tablename__ = "events"

    # 字段定义
    # 使用一个自增的整数作为代理主键
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # 事件的 Discord ID (例如消息 ID)，应该是唯一的
    event_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    
    # 事件类型，例如 'message', 'reaction_add'
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # 事件内容，使用 Text 类型以存储长文本
    content: Mapped[str] = mapped_column(Text, nullable=True)
    
    # 事件发起者的 ID，外键关联到 members.id
    # 当一个 member 被删除时，相关的 event 也应该被处理 (这里设置为 SET NULL)
    author_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("members.id", ondelete="SET NULL"), nullable=True)
    
    # 频道和服务器的 ID
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=True)

    # 事件发生的时间
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # 定义关系：一个 Event 属于一个 Member
    author: Mapped["Member"] = relationship("Member", back_populates="events")

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, type='{self.event_type}', author_id={self.author_id})>"