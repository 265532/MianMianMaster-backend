---
alwaysApply: false
description: 项目开发、业务功能开发、调试、文档生成等规范文档
---
# MianMianMasterBackend - 面向 AI 的开发规约文档 (AI Coding Guidelines)

本文档旨在为 AI 代码助手（如 Trae, Cursor, GitHub Copilot 等）提供明确的开发规范与上下文指南。在本项目（**MianMianMasterBackend**）中生成或修改代码时，请**严格遵守**以下规约。

## 1. 项目概览与技术栈

- **项目名称**: MianMianMasterBackend
- **框架**: FastAPI (Python 3.10+)
- **数据库**: PostgreSQL (同步驱动 psycopg2)
- **ORM**: SQLAlchemy (2.0 同步风格语法 `db.query`)
- **数据库迁移**: Alembic
- **缓存**: Redis (同步客户端 `redis.Redis`)
- **数据验证**: Pydantic v2
- **认证**: JWT (基于 `python-jose` 和 `bcrypt`，禁用 `passlib`)

## 2. 目录结构规范

严格保持当前的目录结构划分，切勿将不同职责的代码混淆。

```text
src/
├── api/          # 路由与API端点 (按版本划分，如 v1)
│   ├── deps.py   # FastAPI 依赖注入 (数据库 Session, 当前用户, 权限校验等)
│   └── v1/       # v1 版本路由 (如 auth.py, business.py)
├── core/         # 核心配置与工具 (Config, Security, Exceptions)
├── db/           # 数据库连接与 Redis 客户端初始化 (同步)
├── models/       # SQLAlchemy 数据库模型 (ORM)
├── schemas/      # Pydantic 验证模型 (Request/Response)
├── services/     # 核心业务逻辑与数据库操作层
└── main.py       # FastAPI 应用入口
alembic/          # 数据库迁移脚本
tests/            # 测试用例
```

## 3. 代码风格与命名规范

1. **类型提示 (Type Hints)**: 所有函数、方法、变量**必须**包含明确的 Python 类型提示。
2. **命名规范**:
   - 变量与函数：`snake_case`
   - 类名 (Models/Schemas/Services)：`PascalCase`
   - 常量：`UPPER_SNAKE_CASE`
3. **导入顺序**:
   - 标准库导入
   - 第三方库导入 (FastAPI, SQLAlchemy, Pydantic)
   - 本地模块导入 (以 `src.` 为前缀，**绝对路径导入**，禁用相对导入 `.`)

## 4. 数据库与 ORM 规范 (models)

1. **基类**: 必须继承自 `src.db.database.Base`。
2. **表名**: 统一使用复数形式，如 `__tablename__ = "users"`。
3. **列定义**: 使用 SQLAlchemy 标准语法（如 `Column(Integer, primary_key=True)`）。
4. **关系定义**: 建立清晰的 `relationship` 和外键，注意配置 `back_populates`。
5. **模型迁移**: 每次修改 `models` 后，**禁止**由 AI 直接操作数据库，必须生成并提示用户执行 Alembic 迁移命令。

## 5. 数据验证规范 (schemas)

1. **分层定义**: 每个业务实体通常包含三个基础 Schema：
   - `XxxBase`: 包含公共字段
   - `XxxCreate`: 用于创建时的输入验证
   - `Xxx`: 用于响应返回（包含 `id`、`created_at`，且需配置 `model_config = {"from_attributes": True}` 以支持 ORM 转换）
2. **Pydantic v2 兼容**:
   - 使用 `model_config` 替代旧版的 `class Config:`。
   - 注意命名空间冲突，如遇到 `model_` 前缀的字段，需添加 `model_config = {'protected_namespaces': ()}`。

## 6. 路由与 API 规范 (api)

1. **RESTful 风格**: 遵循标准 HTTP 动词 (`GET`, `POST`, `PUT`, `DELETE`)，路径使用名词复数，小写短横线分隔（如 `/api/v1/interview-configs`）。
2. **统一响应**: 所有接口必须使用 `src.schemas.system.ResponseModel` 进行返回值封装，确保外层结构为 `{"code": 200, "message": "success", "data": ...}`。
3. **依赖注入与鉴权**:
   - 必须通过 `Depends(get_db)` 获取数据库 Session。
   - 所有的管理端业务接口必须通过 `Depends(check_permissions("resource", "action"))` 进行 RBAC 权限拦截。
4. **严格分层 (Router -> Service -> DB)**: Router 层**禁止**直接操作数据库（禁止写 `db.query()`, `db.add()` 等）。Router 仅负责参数解析、鉴权、依赖注入和响应封装，所有实际的业务逻辑和数据库操作必须下沉至 `src/services/` 层。

## 7. 错误处理与异常规范

1. 统一使用 `fastapi.HTTPException` 进行业务错误抛出。
2. 标准 HTTP 状态码规范：
   - 400 Bad Request：客户端参数或逻辑错误
   - 401 Unauthorized：未登录或 Token 无效
   - 403 Forbidden：权限不足
   - 404 Not Found：资源不存在
3. 全局异常可查阅并添加至 `src/core/exceptions.py`。

## 8. AI 交互与生成准则

- **只做最小必要修改**: 不要重构未涉及的模块。
- **环境兼容性**: 当增加新依赖时，请确保使用 `pip install` 并在 `requirements.txt` 中固定版本号（格式 `package==x.y.z`）。
- **代码完整性**: 返回的代码片段必须是完整的，不可使用 `// ... existing code ...` 等省略号，除非上下文明确支持替换块操作。
- **注释与文档**: 为复杂的业务逻辑和公开的 API 端点添加 Docstring 注释。
- **模块交接文档 (Mandatory)**: 每次完成特定业务模块的开发、重构或 Debug 之后，**必须**在 `doc/` 目录下（或该模块专属的子目录中，如 `doc/auth/`、`doc/business/`）生成或更新一份该模块的**交接文档**（如 `handover.md`）。文档内容需包含：当前模块的核心实现思路、未解决的问题（Todo）、关键的依赖关系、以及下一步的开发建议。这有助于后续 AI 会话快速恢复上下文。

