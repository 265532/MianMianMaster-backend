---
alwaysApply: false
description: 项目总览规约
---
# 项目后台管理模块开发规约 v1.0

## 1. 项目概述

- **项目名称**：AI模拟面试系统 - 后台管理模块（MianMianMasterBackend）
- **技术栈**：Python 3.10+、FastAPI、PostgreSQL、Redis
- **核心职责**：提供管理端API、数据看板、配置管理、Agent调度监控、用户权限控制
- **AI辅助开发原则**：所有AI生成代码必须经过人工审查，遵循本规约，且不得引入安全漏洞或性能隐患

***

## 2. 项目结构规范

```
backend-admin/
├── src/                 # 源代码根目录
│   ├── api/                 # API路由层
│   │   ├── deps.py          # 公共依赖项（如数据库会话、当前用户）
│   │   └── v1/              # API版本v1
│   │       ├── __init__.py
│   ├── core/                # 核心配置、安全、异常处理
│   │   ├── config.py        # 配置管理（pydantic-settings）
│   │   ├── security.py      # JWT、密码哈希、权限校验
│   │   └── exceptions.py    # 全局业务异常定义
│   ├── models/              # SQLAlchemy ORM模型
│   ├── schemas/             # Pydantic模型（请求/响应结构）
│   ├── services/            # 业务逻辑层 (Router将请求转发至此)
│   ├── db/                  # 数据库与缓存客户端连接
│   │   ├── database.py      # SQLAlchemy 同步引擎配置
│   │   └── redis_client.py  # 同步 Redis 客户端
│   └── main.py              # FastAPI应用入口
├── tests/                   # 单元测试、集成测试
├── alembic/                 # 数据库迁移脚本
├── .env.example             # 环境变量模板
├── requirements.txt         # 生产依赖
└── README.md
```

***

## 3. 命名规范

| 类型    | 规范          | 示例                      |
| :---- | :---------- | :---------------------- |
| 文件名   | 小写 + 下划线    | `user_service.py`       |
| 类名    | 大驼峰         | `UserRepository`        |
| 函数/方法 | 小写 + 下划线    | `get_user_by_id`        |
| 常量    | 大写 + 下划线    | `MAX_RETRY_COUNT`       |
| 环境变量  | 大写 + 下划线    | `DATABASE_URL`          |
| API路径 | 小写 + 连字符    | `/api/v1/user-profiles` |
| 数据库表名 | 小写 + 下划线，复数 | `users`                 |
| 模型类名  | 单数，与表名对应    | `User`                  |

***

## 4. 代码风格与质量

- **格式化**：使用 `black`，行宽 100 字符
- **排序导入**：使用 `isort`，配置兼容 black
- **类型注解**：所有函数必须包含完整的类型注解（包括返回值）
- **Linter**：使用 `ruff` 替代 flake8，启用以下规则：
  - `E`、`F`、`W`、`I`、`N`、`UP`、`B`、`SIM`
- **预提交钩子**：使用 `pre-commit` 运行格式化与检查

**AI工具注意**：生成代码后必须运行 `black` 和 `ruff` 进行自动修正。

***

## 5. FastAPI 开发规范

### 5.1 路由层

- 每个模块的路由应组织在 `v1/` 下，使用 `APIRouter`
- 路由函数仅负责参数解析、依赖注入（如鉴权和数据库会话）、调用 service、返回响应，禁止在 Router 层编写复杂业务逻辑或直接操作数据库（`db.query` / `db.add`）
- 使用 `deps.py` 中定义的公共依赖项（如 `get_db`、`check_permissions`）

```python
# 示例
@router.get("/{user_id}", response_model=ResponseModel[UserResponse], dependencies=[Depends(check_permissions("user", "read"))])
def get_user(
    user_id: int,
    db: Session = Depends(get_db)
) -> Any:
    data = user_service.get_user_by_id(db, user_id)
    return ResponseModel(data=data)
```

### 5.2 异常处理

- 统一在 `core/exceptions.py` 中定义自定义异常（如 `BusinessException`）
- 使用全局异常处理器将异常映射为统一的 HTTP 响应格式
- API 返回结构统一使用 `src.schemas.system.ResponseModel`：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

### 5.3 依赖注入

- 数据库会话、缓存客户端、配置对象均通过依赖注入传递
- 禁止在 service 或 repository 中直接实例化外部依赖

***

## 6. 数据库规范（PostgreSQL）

### 6.1 模型定义

- 所有模型继承自 `Base`（由 `declarative_base` 生成）
- 每个模型必须包含：
  - `id` 主键（自增整数或 UUID）
  - `created_at`（`DateTime(timezone=True)`，默认 `func.now()`）
  - `updated_at`（自动更新）
- 使用 `Mapped` 注解形式（SQLAlchemy 2.0 风格）

### 6.2 迁移管理

- 所有表结构变更必须通过 Alembic 生成迁移脚本
- 迁移脚本必须包含 `upgrade()` 和 `downgrade()` 逻辑

### 6.3 查询优化

- 使用 `selectinload` 预加载关联对象，避免 N+1 查询
- 大数据量查询必须使用分页（`limit/offset` 或游标分页）

### 6.4 事务管理

- 所有写操作在 service 层显式使用 `db.begin()` 或依赖 FastAPI 的自动提交
- 避免在 repository 中开启长事务

***

## 7. Redis 使用规范

### 7.1 使用场景

- 缓存高频查询数据（如 Agent 配置、面试题目列表）
- 分布式锁
- 临时数据存储（如验证码、登录态）

### 7.2 Key 命名

- 格式：`{项目}:{模块}:{业务}:{标识}`
- 示例：`ai_interview:agent:config:123`

### 7.3 过期时间

- 所有写入缓存的数据必须设置合理的过期时间（`expire`）

### 7.4 客户端封装

- 使用同步的 `redis.Redis` 客户端（在 `src/db/redis_client.py` 中封装），通过依赖注入或直接获取单例提供给服务层

***

## 8. AI 辅助开发专项规范

### 8.1 代码生成限制

- 禁止AI生成以下内容（必须由人工实现）：
  - 认证与鉴权核心逻辑
  - 数据库迁移脚本
  - 支付、密钥管理等敏感操作
  - 高并发下的分布式锁与事务边界

### 8.2 AI生成代码审查清单

- 是否包含安全漏洞（SQL注入、硬编码凭证、越权风险）
- 是否正确处理了异步上下文（`async/await`）
- 是否存在内存泄漏（如未释放数据库连接、循环引用）
- 类型注解是否完整且正确
- 是否包含必要的错误处理

### 8.3 提示词使用规范

- 向AI提问时，必须附带：
  - 明确的输入输出结构（Pydantic模型）
  - 依赖关系（需要哪些外部服务）
  - 异常场景处理说明

***

## 9. 安全规范

### 9.1 认证与授权

- 使用 JWT（Bearer Token）进行身份认证，Access Token 有效期 30 分钟，Refresh Token 有效期 7 天
- 所有管理端 API 必须通过权限校验（基于角色的访问控制 RBAC）
- 密码存储使用 `bcrypt` 或 `argon2`

### 9.2 数据安全

- 敏感字段（如手机号、邮箱）在日志中脱敏
- 所有 API 输入必须使用 Pydantic 进行校验

### 9.3 网络安全

- 生产环境强制 HTTPS
- 使用 CORS 中间件限制可信来源
- 密码加密强制使用 `bcrypt` 库，禁用 `passlib` 避免现代 bcrypt 版本的包装兼容错误。

***

## 10. 日志与监控

### 10.1 日志级别

- `DEBUG`：开发环境详细调试信息
- `INFO`：关键业务流程（如用户登录、任务创建）
- `WARNING`：可恢复的错误
- `ERROR`：需要关注的异常

### 10.2 日志格式

- JSON 格式，便于 ELK 或云日志服务采集
- 必须包含：`timestamp`、`level`、`module`、`request_id`（链路追踪）

### 10.3 链路追踪

- 使用 `correlation-id` 中间件，在请求入口生成唯一 ID，传递至所有日志

***

## 11. 测试规范

### 11.1 测试类型

- **单元测试**：覆盖 service、repository 层，使用 `pytest` + `pytest-asyncio`
- **集成测试**：测试 API 接口与数据库交互，使用 `TestClient`
- **数据库测试**：使用 `pytest-postgresql` 或事务回滚机制保证隔离

### 11.2 覆盖率要求

- 核心业务逻辑行覆盖率 ≥ 85%
- 关键路径（认证、支付、调度）必须 100% 覆盖

***

## 12. 部署与配置

### 12.1 环境变量

- 所有配置通过环境变量注入，禁止在代码中硬编码
- 使用 `pydantic-settings` 进行配置管理与校验

### 12.2 容器化

- 提供 `Dockerfile` 与 `docker-compose.yml` 用于本地开发
- 生产镜像基于 `python:3.10-slim`，并去除编译工具

***

本规约自发布之日起生效，所有后台模块代码必须严格遵守。如有特殊场景需要偏离，须在代码评审中说明并获得基础架构组批准。
