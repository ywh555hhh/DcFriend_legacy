# DcFriend Legacy

## 项目简介

DcFriend Legacy 是一个 Discord 聊天机器人项目，旨在构建一个智能、记忆型数字伙伴，支持社群互动和数据管理。🚀📝

## 技术栈
- Discord.py（交互层）
- SQLAlchemy 和 Alembic（数据层）
- Dependency Injector（依赖注入与解耦）
- Google Generative AI（AI 功能）

## 快速安装与运行
1. 确保安装 UV：如果未安装，请根据官方文档（https://github.com/astral-sh/uv）安装。
2. 克隆仓库：`git clone <您的仓库地址>`
3. 安装依赖：`uv sync`
4. 配置环境：复制 `.env.example` 为 `.env` 并填写密钥。
5. 初始化数据库：运行 `uv run alembic revision --autogenerate` 生成迁移脚本，然后运行 `uv run alembic upgrade head` 应用脚本（确保 Alembic 已配置正确）。
6. 启动机器人：`uv run main.py`

## 贡献指南
请参考相关 DEVELOPMENT.md 以获取详细开发规范和最佳实践。🤖🔧

---

Made with ❤️ by DcFriend Team