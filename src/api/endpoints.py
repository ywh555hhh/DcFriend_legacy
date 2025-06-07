from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from dependency_injector.wiring import inject, Provide

from src.core.container import Container
from src.db.models import Member
from src.services.member_service import MemberService

import datetime

# ---- API 数据模型 ----
class GetOrCreateMemberRequest(BaseModel):
    user_id: int = Field(..., description="Discord 用户的 ID", example=123456789012345678)
    name: str = Field(..., description="用户的 Discord 名称", example="testuser")
    display_name: str | None = Field(None, description="用户在服务器的昵称", example="测试用户")

class MemberResponse(BaseModel):
    """
    一个智能的、符合最佳实践的成员信息响应体。
    """
    # 关键修复 1: 使用 Field(alias='id') 解决字段名不匹配的问题。
    # 这告诉 Pydantic：这个叫 discord_id 的字段，它的数据应该从源对象的 'id' 属性来获取。
    discord_id: int = Field(alias='id')
    
    name: str
    display_name: str | None
    
    # 关键修复 2: 将字段类型从 str 改为 datetime.datetime。
    # 这让 Pydantic 知道我们期望接收的是 datetime 对象。
    # FastAPI 的默认 JSON 编码器非常智能，它会自动将 datetime 对象转换为
    # 符合 ISO 8601 标准的字符串（例如 "2025-06-07T12:39:53.872000"），
    # 这正是前端最需要的格式。
    created_at: datetime.datetime
    updated_at: datetime.datetime
    
    # from_attributes = True (旧称 orm_mode) 保持不变，它允许 Pydantic 从对象的属性读取数据。
    class Config:
        from_attributes = True

# ---- API 路由 ----
# 关键点 3: 使用 APIRouter 来组织路由
router = APIRouter()

@router.post("/members/get_or_create", response_model=MemberResponse, tags=["Member Service"])
@inject
async def get_or_create_member_endpoint(
    request_data: GetOrCreateMemberRequest,
    # 关键点 4: 使用官方推荐的 Annotated 语法进行注入
    member_service: Annotated[
        MemberService, Depends(Provide[Container.member_service])
    ],
):
    class MockDiscordUser:
        def __init__(self, user_id, name, display_name):
            self.id = user_id
            self.name = name
            self.display_name = display_name

    mock_user = MockDiscordUser(
        user_id=request_data.user_id,
        name=request_data.name,
        display_name=request_data.display_name,
    )

    member_orm: Member = await member_service.get_or_create_member(mock_user)
    return MemberResponse.model_validate(member_orm)