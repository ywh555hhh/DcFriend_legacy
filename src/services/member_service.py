import discord
from typing import Union

from src.db.models import Member
from src.db.repositories.member_repository import MemberRepository

class MemberService:
    """
    服务层，用于处理与成员相关的业务逻辑。
    """

    def __init__(self, member_repo: MemberRepository):
        """
        初始化 MemberService。

        这种模式被称为“依赖注入”（Dependency Injection）。
        我们不在服务内部创建它的依赖（MemberRepository），而是在创建服务时从外部“注入”它。
        这使得代码解耦，并且非常容易测试。

        Args:
            member_repo: 成员数据仓库的实例。
        """
        self.member_repo = member_repo

    async def get_or_create_member(self, user: Union[discord.User, discord.Member]) -> Member:
        """
        从数据库获取一个成员，如果不存在则创建。

        这个方法是连接 Discord 世界和我们自己数据库的关键桥梁。
        它接收一个来自 discord.py 的原生对象，并调用数据访问层来确保该用户在我们的系统中被记录。

        Args:
            user: 来自 Discord 事件的 discord.User 或 discord.Member 对象。

        Returns:
            与该 Discord 用户对应的数据库中的 Member ORM 对象。
        """
        # 从 discord.User 对象中提取所需的数据，
        # 并调用我们已经编写好的 repository 方法。
        member, was_created = await self.member_repo.get_or_create(
            member_id=user.id,
            name=user.name,
            display_name=user.display_name
        )

        # 在服务层，我们可以根据 was_created 的值执行额外的逻辑，
        # 比如记录日志、触发欢迎消息等。目前，我们只简单地返回成员对象。
        if was_created:
            # 例如：未来可以在这里添加日志记录
            # logger.info(f"新成员已注册：{user.name} (ID: {user.id})")
            pass

        return member