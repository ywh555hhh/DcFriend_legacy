import uvicorn
from fastapi import FastAPI

from src.core.container import Container
from src.core.config import Settings
from src.api import endpoints

def create_app() -> FastAPI:
    """
    应用工厂，负责创建和配置 FastAPI 应用实例。
    """
    # 关键点 5: 在工厂函数内部创建和配置容器
    container = Container()
    container.config.from_pydantic(Settings())

    app = FastAPI(
        title="看板娘调试 API 服务器",
        description="一个用于在开发环境中独立调试和测试核心服务的 API 服务器。",
        version="0.1.0"
    )
    # 关键点 6: 将容器实例附加到 app 对象上，方便测试时使用
    app.container = container
    # 关键点 7: 将路由模块包含进来
    app.include_router(endpoints.router)
    return app

# 关键点 8: 创建全局的 app 实例，供 uvicorn 使用
app = create_app()

if __name__ == "__main__":
    uvicorn.run("debug_api_server:app", host="127.0.0.1", port=8000, reload=True)