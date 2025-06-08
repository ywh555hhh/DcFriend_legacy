# src/core/config.py (最终权威版本)

import os
import sys
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    一个智能的、符合最佳实践的配置管理器。
    """

    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # 不区分大小写
        extra="ignore",
    )

    # Python 内部我们叫它 BOT_TOKEN
    # 但它会去 .env 文件里找一个叫 DISCORD_BOT_TOKEN 的变量
    BOT_TOKEN: str = Field(..., alias="DISCORD_BOT_TOKEN")

    # Python 内部我们叫它 GEMINI_API_KEY
    # 但它会去 .env 文件里找一个叫 GOOGLE_AI_KEY 的变量
    GEMINI_API_KEY: str = Field(..., alias="GOOGLE_AI_KEY")

    GEMINI_MODEL_NAME: str = "models/gemini-2.5-flash-preview-05-20"
    DB_ECHO: bool = Field(default=False, alias="DATABASE_ECHO")
    LOG_LEVEL: str = Field(default="INFO", alias="APP_LOG_LEVEL")

    @property
    def DATA_DIR(self) -> Path:
        return self.PROJECT_ROOT / "data"

    @property
    def DATABASE_URL(self) -> str:
        db_path = self.DATA_DIR / "dcfriend.db"
        return f"sqlite+aiosqlite:///{db_path.as_posix()}"


try:
    settings = Settings()
    os.makedirs(settings.DATA_DIR, exist_ok=True)
except Exception as e:
    print(
        f"FATAL: Could not load configuration. Please ensure a .env file exists in the project root and contains all required variables. Details: {e}",
        file=sys.stderr,
    )
    sys.exit(1)
