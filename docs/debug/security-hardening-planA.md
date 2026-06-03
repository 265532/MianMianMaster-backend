# 安全加固实施经验总结 (PlanA A1-A7)

> 实施日期: 2026-05-12
> 涉及任务: A1(CORS) A2(JWT双Token) A3(RBAC) A4(自动建表) A5(登录锁定) A6(重置Token) A7(SMS安全)

---

## 一、变更总览

### 修改文件清单

| 文件 | 变更类型 | 涉及任务 |
|------|---------|---------|
| src/core/config.py | 修改 | A1 A2 A4 |
| src/main.py | 修改 | A1 A4 |
| src/core/security.py | 重写 | A2 A6 |
| src/api/deps.py | 重写 | A2 A3 |
| src/schemas/user.py | 修改 | A2 |
| src/services/auth_service.py | 重写 | A2 A5 A6 A7 |
| src/api/v1/auth.py | 重写 | A2 A5 A7 |
| Dockerfile | 修改 | A4 |
| docker-compose.yml | 修改 | A4 |
| .env.example | 新建 | A1 A2 A4 |

---

## 二、各任务实施要点与坑点

### A1: CORS 安全配置修复

**要点**:
- `ALLOWED_ORIGINS` 使用逗号分隔字符串，便于环境变量配置
- `cors_origins_list` 属性自动解析为列表
- `allow_methods` 和 `allow_headers` 收紧为实际使用值

**坑点**: 无

### A2: JWT 双 Token 机制

**要点**:
- Access Token 有效期从 11520 分钟(8天)缩短为 30 分钟
- JWT payload 新增 `type`(access/refresh/reset) 和 `jti`(UUID) 字段
- Refresh Token 白名单: `refresh_token:user:{user_id}` → jti
- Access Token 黑名单: `token:blacklist:{jti}` → "1"
- `datetime.utcnow()` → `datetime.now(timezone.utc)` 消除 DeprecationWarning
- 新增 `/auth/refresh` 和 `/auth/logout` 接口
- 登录响应新增 `refresh_token` 字段（前端需适配）

**坑点**:
- `_build_token_pair` 中 Refresh Token 的 `sub` 使用 `user.id`(int)，Access Token 使用 `user.username`(str)，这是设计文档的要求
- Token 黑名单 TTL 设置为 Token 剩余有效期，避免 Redis 中永久存储

### A3: RBAC 权限逻辑清理

**要点**:
- 移除 `current_user.username != "admin"` 硬编码判断
- 新增 `SUPER_ADMIN_ROLE` 常量、`_is_super_admin()` 和 `_get_user_permissions()` 函数
- 权限判断逻辑简化: 超管放行 → 权限检查 → 403

**坑点**: 无

### A4: 移除生产环境自动建表

**要点**:
- `ENVIRONMENT` 配置项默认值 `"development"`，确保开发体验不受影响
- Dockerfile CMD 使用 `sh -c` 支持命令链
- docker-compose.yml 显式设置 `ENVIRONMENT=production`

**坑点**:
- 如果 `alembic upgrade head` 失败，容器不会启动 uvicorn，这是预期行为

### A5: 登录失败锁定机制

**要点**:
- 双重锁定: 用户名级 + IP 级
- 使用 Redis INCR 原子操作，并发安全
- 5 次失败后锁定 15 分钟
- 新增 `/auth/unlock/{username}` 管理员接口
- 锁定响应返回剩余时间(分钟)但不暴露精确失败次数

**坑点**:
- `_record_login_failure` 返回剩余次数，但如果达到阈值时直接抛 423 异常，不会返回次数
- 登录路由需新增 `Request` 参数获取客户端 IP

### A6: 密码重置 Token 单次使用

**要点**:
- 密码重置 Token payload 新增 `jti` 字段
- Redis `pwd_reset:used:{jti}` 标记已使用，TTL=900s(15分钟)
- Redis `pwd_reset:cooldown:{email}` 5分钟请求冷却
- `reset_password` 方法改为先解码 Token 获取 jti，再校验是否已使用

**坑点**:
- 原 `verify_password_reset_token` 函数保持兼容，但 `reset_password` 中不再使用它，而是直接用 `jwt.decode` 解码获取完整 payload

### A7: SMS 安全增强

**要点**:
- 验证码存储: 明文 → SHA-256 哈希 (`{code}{phone}{salt}`)
- 随机数: `random.randint` → `secrets.randbelow(900000) + 100000`
- 每日上限: 10条/手机号 + 20条/IP
- 验证码错误5次失效
- 日计数 TTL 计算到 UTC 午夜自动重置
- 使用 Redis pipeline 原子操作递增计数

**坑点**:
- 验证码改为哈希后，现有测试中直接构造 `SmsVerification` 记录需适配
- `_get_daily_remaining_seconds` 计算 UTC 午夜时间，非本地时间

---

## 三、回滚方案

每个任务独立提交，可单独 revert:

| 任务 | 回滚命令 | 注意事项 |
|------|---------|---------|
| A1 | `git revert <hash>` | 需恢复 allow_origins=["*"] |
| A2 | `git revert <hash>` | 前端需同步回滚 Token 刷新逻辑 |
| A3 | `git revert <hash>` | 无特殊注意 |
| A4 | `git revert <hash>` | 回滚后开发环境仍需 create_all |
| A5 | `git revert <hash>` | Redis 中已有的锁定键需手动清理 |
| A6 | `git revert <hash>` | Redis 中已有的 used 标记无需清理(自动过期) |
| A7 | `git revert <hash>` | 数据库中已有的哈希验证码需等5分钟自然过期 |

---

## 四、Redis Key 总览

| Key 模式 | 任务 | TTL | 说明 |
|----------|------|-----|------|
| `refresh_token:user:{user_id}` | A2 | 7天 | Refresh Token 白名单 |
| `token:blacklist:{jti}` | A2 | Token剩余有效期 | Access Token 黑名单 |
| `login:failed:{user/ip}:{id}` | A5 | 15分钟 | 登录失败计数 |
| `login:locked:{user/ip}:{id}` | A5 | 15分钟 | 登录锁定标记 |
| `pwd_reset:used:{jti}` | A6 | 15分钟 | 已使用的重置Token |
| `pwd_reset:cooldown:{email}` | A6 | 5分钟 | 重置请求冷却 |
| `sms:cooldown:{phone}` | A7 | 60秒 | SMS发送冷却 |
| `sms:daily:{phone}` | A7 | 至UTC午夜 | 手机号日发送计数 |
| `sms:daily:ip:{ip}` | A7 | 至UTC午夜 | IP日发送计数 |
| `sms:verify:{phone}` | A7 | 5分钟 | 验证码错误计数 |
