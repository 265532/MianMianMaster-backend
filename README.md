# MianMianMaster Backend (面面俱到后端)

这是 MianMianMaster（AI模拟面试系统）的后端服务仓库。本项目基于 **Python 3.10+** 和 **FastAPI** 构建，采用了严格的 `Router -> Service -> DB` 分层架构，以确保代码的可维护性与扩展性。

## 🛠️ 技术栈

- **Web 框架**: [FastAPI](https://fastapi.tiangolo.com/)
- **数据库**: PostgreSQL 14+
- **ORM**: SQLAlchemy 2.0 (同步风格)
- **缓存**: Redis 7+
- **鉴权**: JWT + 基于 Redis 缓存的 RBAC
- **安全**: bcrypt (密码哈希)
- **容器化**: Docker & Docker Compose

## 📂 目录结构

```text
MianMianMaster-backend/
├── .trae/rules/         # IDE / AI 代码助手的系统提示词与开发约束
├── docs/                 # 项目内部开发规约、交接文档与知识库
├── src/                 # 核心业务源代码
│   ├── api/             # API 路由层 (Endpoints, Deps)
│   ├── core/            # 核心配置与全局异常、安全工具
│   ├── db/              # 数据库与缓存的连接管理
│   ├── models/          # SQLAlchemy 数据库模型
│   ├── schemas/         # Pydantic 验证模型 (Request/Response)
│   └── services/        # 核心业务逻辑层 (处理所有的数据库操作)
├── tests/               # 测试代码
└── alembic/             # 数据库迁移脚本
```

## 📖 开发规约与文档

本项目有严格的开发规约，请所有开发者（及 AI 助手）在贡献代码前务必阅读：
👉 **[点击查看文档导航中心](./docs/README.md)**

特别是：
- [AI 开发规约合订版](./docs/ai-development-specification.md)（最高准则）

## 🚀 快速启动

*(待补充：本地开发环境搭建、环境变量配置及启动命令...)*

---

*Powered by FastAPI & AI-Assisted Development.*