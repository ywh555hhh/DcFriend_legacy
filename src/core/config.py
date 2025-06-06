# src/core/config.py
import sys
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# 定义一个 Pydantic 设置类，它会自动从 .env 文件和环境变量中读取配置
class Settings(BaseSettings):
    # model_config 用于配置 Pydantic 的行为
    model_config = SettingsConfigDict(
        # 指定 .env 文件的路径和编码
        # 我们假设 .env 文件在项目的根目录，即 src/ 的上一级
        env_file=Path(__file__).resolve().parent.parent.parent / '.env',
        env_file_encoding='utf-8',
        # extra='ignore' 允许 .env 文件中有额外的变量而不会报错
        extra='ignore' 
    )

    # --- Discord 配置 ---
    # 定义 DISCORD_BOT_TOKEN 为一个必需的字符串字段
    DISCORD_BOT_TOKEN: str

    # --- Google AI 配置 ---
    # 定义 GOOGLE_AI_KEY 为一个必需的字符串字段
    GOOGLE_AI_KEY: str
    
    # 定义 GOOGLE_AI_MODEL_NAME 为一个可选的字符串字段，并提供默认值
    GOOGLE_AI_MODEL_NAME: str = "models/gemini-1.5-flash-latest"

    # --- 数据库配置 ---
    # 定义 DATABASE_URL，并提供一个默认的 SQLite 路径
    DATABASE_URL: str = f"sqlite+aiosqlite:///{Path(__file__).resolve().parent.parent.parent / 'user_data/memory.db'}"


# 创建一个全局唯一的 settings 实例
# 当这个文件被导入时，Pydantic 会自动读取 .env 文件并填充这个对象
try:
    settings = Settings()
except Exception as e:
    # 如果因为 .env 文件没配置好等原因导致初始化失败，打印清晰的错误信息
    print(f"错误：无法加载配置。请确保项目根目录存在 .env 文件，并且包含了所有必要的变量。详细信息：{e}", file=sys.stderr)
    sys.exit(1)