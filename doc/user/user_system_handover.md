# 基础用户系统交接文档

## 1. 概述
本项目（MianMianMasterBackend）已经完成基础用户系统的设计与开发。该模块提供完整的用户注册、登录（密码及手机验证码）、密码找回、重置功能，以及基于 RBAC 的动态权限管理机制。

## 2. 数据库设计
数据库脚本存放在 `doc/database/init.sql`，支持 PostgreSQL 最佳实践。主要涉及以下核心表：
- `users`: 存储用户基本信息、密码哈希、手机号等。
- `roles`: 角色表，支持通过 `parent_id` 实现角色继承。
- `permissions`: 权限表，使用 `resource` 和 `action` 进行精细化权限定义。
- `user_roles`: 用户与角色的多对多关联。
- `role_permissions`: 角色与权限的多对多关联。
- `sms_verifications`: 手机验证码表，记录发送的验证码、有效期及使用状态。

## 3. 核心功能实现
### 3.1 密码加密与安全
- **加密算法**: 使用标准的 `bcrypt` 算法进行密码哈希处理。
- **密码强度验证**: 在注册和重置密码时，强制要求密码至少包含8个字符，且必须包含大写字母、小写字母、数字和特殊字符。
- **密码重置令牌**: 使用基于 `jose` 的 JWT 生成有效期15分钟的重置令牌，确保重置流程安全。

### 3.2 接口兼容性
- **Swagger登录兼容**: 默认的 `/api/v1/auth/login` 接口被设计为接收 JSON 格式 (`application/json`) 数据。为兼容 FastAPI 内置的 Swagger UI "Authorize" 按钮，单独提供了 `/api/v1/auth/swagger-login` 接口接收表单数据。

### 3.3 手机验证码功能
- **验证码发送**: 实现了发送接口 `/api/v1/auth/sms/send`，结合 Redis 缓存实现了 60 秒防刷机制。
- **验证码登录**: 实现了 `/api/v1/auth/sms/login`，验证码为 6 位数字，有效期 5 分钟，验证成功即失效，并返回 JWT 访问令牌。
- **手机号验证**: 使用 Pydantic 的 `field_validator` 支持中国大陆手机号正则验证。

### 3.4 角色鉴权（RBAC）业务
- **角色继承**: 获取权限时支持自动递归加载父角色权限（见 `src/api/deps.py` 中的 `get_role_permissions`）。
- **权限拦截**: 使用依赖注入方式 `@router.get(..., dependencies=[Depends(check_permissions("resource", "action"))])` 实现方法级别权限控制。
- **权限缓存**: 权限验证时通过 Redis 缓存用户的权限列表，过期时间 1 小时，角色/权限更新时自动清除缓存，支持动态权限加载。
- **管理接口**: 提供了角色创建、权限分配、用户角色分配接口（位于 `/api/v1/rbac/` 路由下）。

## 4. 技术规范与标准
- **RESTful API**: 各模块 API 接口完全遵循 RESTful 风格设计。
- **统一响应格式**: 所有 API 统一返回 `ResponseModel` 格式：`{"code": 200, "message": "success", "data": ...}`。
- **全局异常处理**: 覆盖 `BusinessException`、`HTTPException` 和 `RequestValidationError`，将业务错误包装为统一 JSON 返回。
- **测试覆盖率**: 在 `tests/test_api.py` 中补充了针对 Auth 的单元测试（基于内存 SQLite 和 Mocker），满足核心功能的测试要求。
- **文档**: 启动服务后可访问 `/docs` 查阅自动生成的 Swagger/OpenAPI 文档。

## 5. 部署与运维监控建议
- **依赖说明**: 确保 PostgreSQL (或兼容 SQL) 及 Redis 服务正常运行，在生产环境应配置对应环境变量（如 `REDIS_HOST`, `SQLALCHEMY_DATABASE_URI` 等）。
- **监控方案**: 建议接入 Prometheus + Grafana 或 ELK Stack，利用系统内预留的 `AuditLog` 和全局错误日志来追踪业务异常及接口性能（`X-Process-Time`）。
- **安全防范**: 
  - 防止 SQL 注入：全面采用 SQLAlchemy ORM。
  - 防止 XSS：采用 FastAPI + Pydantic 数据验证，拒绝非法输入。
  - 接口限流：核心接口（如验证码）已做 Redis 级别速率限制。

## 6. 后续待优化项
- 实际对接真实的短信服务提供商。
- 完善发送密码重置邮件的实际逻辑（目前返回 Token 用于测试）。
- 根据业务需要编写更全面的集成测试和性能压测报告（可通过 Locust 或 JMeter 补充）。
