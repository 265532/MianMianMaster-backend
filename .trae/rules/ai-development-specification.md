---
alwaysApply: true
---
# AI 开发规约合订版

> 本文档为 MianMianMasterBackend 后端 项目面向 AI 代码助手（Trae、Cursor、GitHub Copilot 等）的统一开发规约。如有冲突，以此文件为准。

## 1. 架构约束

- **强制 Must**: 采用分层架构（Router -> Service -> DB），禁止在 Router 层编写复杂业务逻辑，所有数据库操作和核心逻辑必须放在 Service 层。
- **推荐 Should**: 依赖注入应在 Router 层完成，向下传递给 Service。
- **可选 May**: 复杂任务可采用 Celery 等后台任务队列处理。

**正例**: `Router` 仅包含 `Depends` 注入和对 `Service` 的调用。
**反例**: 在 `Router` 中直接使用 `db.query()` 进行复杂的数据聚合。
**AI 提示词模板**: `请为 [模块名] 编写一个遵循分层架构的接口，Router 层只做参数校验和依赖注入，具体逻辑放在 Service 层。`

## 2. 技术栈版本

- **强制 Must**:
  - Python >= 3.10
  - FastAPI >= 0.104
  - SQLAlchemy == 2.0.x (同步风格 `db.query()`，不使用 `asyncpg`)
  - PostgreSQL >= 14
  - Redis >= 7
- **强制 Must**: 密码加密必须使用 `bcrypt` 算法，禁用 `passlib` 避免现代 bcrypt 版本引发错误。

**多源冲突裁决说明**:
- *冲突*: `overviewV3.md` 中描述使用 `asyncpg` 和 `redis.asyncio`，但实际项目代码 (`src/db/database.py`, `src/db/redis_client.py`) 均使用同步客户端 (`psycopg2-binary`, 同步 `redis`)。
- *裁决*: 以当前项目生效代码为准，**统一使用同步 SQLAlchemy 2.0 语法及同步 Redis 客户端**。
- *冲突*: `Dockerfile` 中 Python 版本为 `3.12.10-slim`，而文档中多处标为 `3.10+`。
- *裁决*: 统一基线为 `Python 3.10+`，兼容 `3.12`。

**正例**: `def get_user(db: Session, user_id: int): return db.query(User).filter(User.id == user_id).first()`
**反例**: 使用 `async_session` 或 `await db.execute()`。
**AI 提示词模板**: `请使用同步 SQLAlchemy 2.0 语法和 FastAPI 编写查询接口，Python 版本兼容 3.10+。`

## 3. 包管理策略

- **强制 Must**: 使用 `requirements.txt` 管理生产依赖，固定所有包版本（如 `package==x.y.z`）。
- **推荐 Should**: 本地开发和测试依赖可单独维护。

**正例**: `fastapi==0.104.1`
**反例**: `fastapi>=0.104`
**AI 提示词模板**: `如果需要引入新依赖，请在 requirements.txt 中指定明确的版本号（如 ==1.0.0）。`

## 4. 目录命名

- **强制 Must**: 必须遵守以下 `src` 目录结构：
  - `src/api/`：路由与 API 端点
  - `src/core/`：核心配置与工具（如 `config.py`，`exceptions.py`）
  - `src/db/`：数据库连接与 Redis 初始化
  - `src/models/`：SQLAlchemy 模型
  - `src/schemas/`：Pydantic 验证模型
- **强制 Must**: 文件名使用 `snake_case`（如 `user_service.py`），类名使用 `PascalCase`（如 `UserRepository`）。

**多源冲突裁决说明**:
- *冲突*: `overviewV3.md` 描述目录为 `app/`，实际为 `src/`。
- *裁决*: 以实际代码结构 `src/` 为准。

**正例**: 路径 `src/api/v1/auth.py`
**反例**: 路径 `app/api/Auth.py`
**AI 提示词模板**: `请在 src/models/ 目录下新建一个符合 snake_case 命名的模型文件。`

## 5. 代码风格

- **强制 Must**: 必须包含明确的 Python 类型提示（Type Hints）。
- **强制 Must**: 绝对路径导入，以 `src.` 为前缀（如 `from src.core.config import settings`），禁用相对导入（如 `from . import xxx`）。
- **推荐 Should**: 使用 `black`（行宽 100 字符）和 `ruff` 进行格式化与检查。

**正例**: `def get_user(user_id: int) -> User:`
**反例**: `def get_user(user_id):`
**AI 提示词模板**: `请生成包含完整类型提示的 Python 代码，并使用 src. 前缀进行绝对导入。`

## 6. 接口规范

- **强制 Must**: 遵循 RESTful 风格，路径使用名词复数和小写短横线分隔（如 `/api/v1/interview-configs`）。
- **强制 Must**: 所有 API 必须使用统一响应格式（如 `{"code": 200, "message": "success", "data": ...}`）。
- **强制 Must**: Swagger UI 表单登录需保留独立的 `/api/v1/auth/swagger-login` 端点兼容。

**正例**: `GET /api/v1/users/{user_id}`
**反例**: `POST /api/v1/getUser`
**AI 提示词模板**: `请设计一个 RESTful API，路径使用短横线分隔，并返回统一的 JSON 响应格式。`

## 7. 数据库规约

- **强制 Must**: 模型继承自 `src.db.database.Base`，表名统一为复数。
- **强制 Must**: 必须包含 `id`、`created_at` 等公共字段。
- **强制 Must**: 每次修改模型后，严禁由 AI 直接操作数据库，必须生成 Alembic 迁移脚本提示。

**正例**: `class User(Base): __tablename__ = "users"`
**反例**: `class user(Base): __tablename__ = "user"`
**AI 提示词模板**: `请基于 SQLAlchemy 编写模型，表名为复数形式，并提供 Alembic 迁移命令提示。`

## 8. 测试策略

- **强制 Must**: 核心业务逻辑（Service层）行覆盖率 ≥ 85%，关键路径（如认证）需 100% 覆盖。
- **推荐 Should**: 使用 `pytest` 编写单元测试和集成测试，测试文件存放在 `tests/` 目录下。

**正例**: 在 `tests/` 下使用 `TestClient` 编写 API 测试。
**反例**: 未经测试直接提交包含核心状态机流转的代码。
**AI 提示词模板**: `请为刚才编写的 Service 逻辑补充基于 pytest 的单元测试，确保分支覆盖率。`

## 9. 日志规约

- **强制 Must**: 日志需包含 `timestamp`、`level`、`module` 等关键信息。敏感字段（如手机号、密码）必须脱敏。
- **推荐 Should**: 使用 JSON 格式记录关键流程日志，便于云端采集。

**正例**: `logger.info("User logged in", extra={"user_id": 123})`
**反例**: `logger.info(f"User password is {password}")`
**AI 提示词模板**: `请在关键业务节点添加 INFO 级别的日志，确保敏感信息已脱敏。`

## 10. 安全规约

- **强制 Must**: 禁止在代码中硬编码任何密钥或密码，必须通过 `pydantic-settings` 及 `.env` 环境变量读取（使用 `src.core.config.settings`）。
- **强制 Must**: 所有管理端 API 必须通过 `Depends(check_permissions("resource", "action"))` 进行 RBAC 权限拦截。

**多源冲突裁决说明**:
- *冲突*: `overviewV3.md` 中说明“未使用 dotenv 依赖”，而实际使用了 `python-dotenv`。
- *裁决*: 以 `src/core/config.py` 为准，允许并推荐使用 `.env` 及 `load_dotenv()` 管理本地环境变量。
- *冲突*: `overviewV3.md` 中规定使用 `Casbin`。
- *裁决*: 实际代码采用了基于 Redis 缓存的递归角色权限查询（`check_permissions`），以实际代码实现为准。

**正例**: `from src.core.config import settings; db_url = settings.SQLALCHEMY_DATABASE_URI`
**反例**: `db_url = "postgresql://admin:password@localhost/db"`
**AI 提示词模板**: `请为该接口添加基于 check_permissions 的 RBAC 权限校验，并从 settings 读取配置。`

## 11. 性能规约

- **强制 Must**: 高频查询（如用户权限）必须使用 Redis 缓存。
- **强制 Must**: 列表查询接口必须实现分页机制（`limit`/`offset`）。
- **推荐 Should**: 数据库查询使用 `selectinload` 避免 N+1 问题。

**正例**: `db.query(User).options(selectinload(User.roles)).limit(10).offset(0)`
**反例**: 在循环中触发懒加载导致的 N+1 查询。
**AI 提示词模板**: `请优化这段 ORM 查询，使用 selectinload 解决 N+1 问题，并加入 Redis 缓存逻辑。`

## 12. 部署规约

- **强制 Must**: 使用 Docker 容器化部署，`Dockerfile` 必须基于 `python:*-slim` 镜像。
- **强制 Must**: 启动前必须通过 `alembic upgrade head` 执行数据库迁移。

**正例**: Docker Compose 文件中将 `db` 依赖置于 `api` 服务之前。
**反例**: 将带有开发工具和缓存库的庞大镜像直接用于生产。
**AI 提示词模板**: `请生成一份适用于生产环境的 Dockerfile，基于 slim 镜像并去除多余缓存。`

## 13. 回滚规约

- **强制 Must**: Alembic 迁移脚本必须包含完整的 `upgrade()` 和 `downgrade()` 逻辑。
- **可选 May**: 业务部署应支持通过回退镜像版本实现快速回滚。

**正例**: `def downgrade(): op.drop_table('users')`
**反例**: `def downgrade(): pass`
**AI 提示词模板**: `请生成完整的 Alembic 迁移脚本，务必包含正确的 downgrade 逻辑以支持回滚。`

## 14. 异常处理

- **强制 Must**: 统一在 `src/core/exceptions.py` 定义业务异常（如 `BusinessException`）。
- **强制 Must**: 路由层捕获并转换为统一 JSON 结构，标准 HTTP 错误使用 `fastapi.HTTPException`。

**正例**: `raise BusinessException(code=400, message="Invalid user status")`
**反例**: 直接返回 `return {"error": "..."}` 且状态码为 200。
**AI 提示词模板**: `请在出现逻辑错误时，抛出系统中统一封装的 BusinessException。`

## 15. 国际化

- **推荐 Should**: 前端展示和错误信息提示宜预留国际化方案支持（使用翻译键值对而非硬编码中文字符串）。
- **可选 May**: API 响应中的 `message` 字段可支持基于 `Accept-Language` 头的多语言切换。

**正例**: `{"message": "USER_NOT_FOUND"}`
**反例**: `{"message": "找不到该用户"}`
**AI 提示词模板**: `请将返回的错误信息替换为标准错误码（如 USER_NOT_FOUND），以便前端支持国际化。`

## 16. 监控告警

- **推荐 Should**: 记录接口耗时（`X-Process-Time`）并在超时或出现 500 级别错误时，输出 ERROR 级别日志以便外部系统监控。
- **可选 May**: 后续可接入 Prometheus + Grafana。

**正例**: 在 Middleware 中记录 `process_time` 并通过 `logger.warning` 记录慢查询。
**反例**: 吞没 500 异常导致无任何监控报警输出。
**AI 提示词模板**: `请为该核心链路增加日志埋点，以便于后续接入监控系统追踪性能。`

## 17. 分支与提交信息

- **强制 Must**: 分支命名遵循 `feature/xxx`, `bugfix/xxx`, `hotfix/xxx` 规范。
- **强制 Must**: 提交信息必须遵循 Conventional Commits 规范（如 `feat: add user login`, `fix: resolve db leak`）。

**正例**: `feat(auth): 增加基于 Redis 的短信防刷机制`
**反例**: `update code`
**AI 提示词模板**: `请为刚才的代码修改生成符合 Conventional Commits 规范的 Git 提交信息。`

## 18. CodeReview 门禁

- **强制 Must**: 所有 AI 生成代码合入前必须经过风格检查（0 警告 0 错误）和安全扫描。
- **强制 Must**: 必须通过所有预提交钩子（`pre-commit`，含 `black`, `ruff`）。

**正例**: 提交前本地运行 `pytest` 和 `ruff check .`。
**反例**: 未运行测试直接将 AI 生成代码推送到 `main` 分支。
**AI 提示词模板**: `在提供最终代码前，请自行核对是否符合 ruff 和 black 的格式规范，并确认无安全漏洞。`

## 19. 依赖升级策略

- **强制 Must**: 禁止在未经充分测试的情况下盲目升级大版本（尤其是 FastAPI、SQLAlchemy、Pydantic）。
- **推荐 Should**: 安全漏洞补丁小版本应及时通过 `pip install --upgrade` 升级并更新 `requirements.txt`。

**正例**: 升级 `pydantic` 从 `2.5.2` 到 `2.5.3`。
**反例**: 直接将 `SQLAlchemy` 升级到 3.x（假设存在）而不做兼容性测试。
**AI 提示词模板**: `请分析升级 [包名] 到 [版本号] 可能带来的 Breaking Changes，并给出升级建议。`

## 20. 冲突裁决策略

- **强制 Must**: 遇到多源文档对同一主题描述不一致时，**永远以当前项目正在生效的最新代码（`src/` 目录下的实现）为最高准则**。
- **推荐 Should**: 发现文档与代码冲突时，AI 助手应在响应中显式指出冲突，并说明裁决依据。

**正例**: “文档说明使用 `asyncpg`，但检测到 `src/db/database.py` 使用同步引擎，因此为您生成同步代码。”
**反例**: 忽略现有代码上下文，强行按照旧文档生成导致无法运行的异步代码。
**AI 提示词模板**: `如果在阅读上下文时发现规约文档与 src/ 代码存在冲突，请以实际代码为准并告诉我。`

## 21. AI 记忆与交接规约

- **强制 Must**: 每次完成特定业务模块的开发、重构或复杂 Debug 后，AI 助手**必须**在 `docs/` 目录下的对应模块子目录中（如 `docs/auth/handover.md`）生成或更新**模块交接文档**。
- **强制 Must**: 交接文档内容必须包含：当前已实现的核心功能清单、未完成的 Todo 事项、关键技术决策说明、以及下一步开发的建议上下文，以便在下一次开启全新对话时，新的 AI 助手能快速恢复上下文。

**正例**: 在完成登录模块重构后，主动更新 `docs/auth/handover.md`，记录 JWT 过期时间的配置位置和当前的 RBAC 进度。
**反例**: 完成了大量修改后直接结束对话，导致下一次对话中 AI 助手丢失对刚完成工作的上下文感知。
**AI 提示词模板**: `请根据刚才完成的 [模块名] 开发工作，在 docs/[模块名]/ 目录下生成/更新一份 handover.md 交接文档，记录当前进度、关键设计和待办事项。`
