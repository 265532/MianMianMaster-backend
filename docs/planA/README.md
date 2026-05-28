# 轨道 A: 安全加固计划 — 总览

> **计划周期**: Week 1-2 (2026-05-09 ~ 2026-05-22)  
> **优先级范围**: P0 (致命) + P1 (严重)  
> **总工时**: 7.5 人天  
> **前置依赖**: 无  
> **完成标志**: 所有 P0/P1 安全缺陷清零

---

## 一、任务总览与执行顺序

```
Day 1        Day 2        Day 3        Day 4        Day 5        Day 6-7
┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐
│ A1   │   │ A2   │   │ A2   │   │ A3   │   │ A5   │   │ A6   │
│ CORS │   │ JWT  │   │ JWT  │   │ RBAC │   │ 锁定 │   │ 重置 │
│ 0.5d │   │ 双Token│   │ 双Token│   │ 重构 │   │ 1.5d│   │ 1d   │
│      │   │      │   │      │   │ 1d   │   │      │   │      │
│ A4   │   │      │   │      │   │      │   │      │   │ A7   │
│ 建表 │   │      │   │      │   │      │   │      │   │ SMS  │
│ 0.5d │   │      │   │      │   │      │   │      │   │ 1d   │
└──────┘   └──────┘   └──────┘   └──────┘   └──────┘   └──────┘
  P0          P0          P0          P0         P1          P1
```

## 二、任务清单

| Task ID | 任务名称 | 优先级 | 工时 | 涉及文件 | 详细文档 |
|---------|---------|--------|------|---------|---------|
| A1 | CORS 安全配置修复 | 🔴 P0 | 0.5d | config.py, main.py | [A1-cors-fix.md](./A1-cors-fix.md) |
| A2 | JWT 双 Token 机制实现 | 🔴 P0 | 2d | security.py, config.py, auth_service.py, auth.py, deps.py, user.py(schema) | [A2-jwt-dual-token.md](./A2-jwt-dual-token.md) |
| A3 | RBAC 权限逻辑清理 | 🔴 P0 | 1d | deps.py | [A3-rbac-cleanup.md](./A3-rbac-cleanup.md) |
| A4 | 移除生产环境自动建表 | 🔴 P0 | 0.5d | main.py, config.py, Dockerfile | [A4-remove-auto-create.md](./A4-remove-auto-create.md) |
| A5 | 登录失败锁定机制 | 🟠 P1 | 1.5d | auth_service.py, auth.py, redis_client.py | [A5-login-lockout.md](./A5-login-lockout.md) |
| A6 | 密码重置 Token 单次使用 | 🟠 P1 | 1d | auth_service.py, security.py | [A6-reset-token-once.md](./A6-reset-token-once.md) |
| A7 | SMS 安全增强 | 🟠 P1 | 1d | auth_service.py, redis_client.py | [A7-sms-security.md](./A7-sms-security.md) |

## 三、文件变更影响矩阵

| 文件路径 | A1 | A2 | A3 | A4 | A5 | A6 | A7 | 变更类型 |
|---------|----|----|----|----|----|----|----|----| 
| `src/core/config.py` | ✏️ | ✏️ | | ✏️ | | | | 修改 |
| `src/main.py` | ✏️ | | | ✏️ | | | | 修改 |
| `src/core/security.py` | | ✏️ | | | | ✏️ | | 修改 |
| `src/api/deps.py` | | ✏️ | ✏️ | | | | | 修改 |
| `src/services/auth_service.py` | | ✏️ | | | ✏️ | ✏️ | ✏️ | 修改 |
| `src/api/v1/auth.py` | | ✏️ | | | ✏️ | | | 修改 |
| `src/schemas/user.py` | | ✏️ | | | ✏️ | | | 修改 |
| `src/db/redis_client.py` | | | | | | | ✏️ | 修改 |
| `Dockerfile` | | | | ✏️ | | | | 修改 |
| `.env.example` | 🆕 | 🆕 | | 🆕 | | | | 新建 |
| `tests/test_auth_security.py` | 🆕 | 🆕 | 🆕 | | 🆕 | 🆕 | 🆕 | 新建 |

**图例**: ✏️ 修改 | 🆕 新建

## 四、共享基础设施变更

以下变更被多个 Task 共享，需最先完成：

### 4.1 config.py 新增字段汇总

```python
# 所有 A 系列任务需要在 Settings 类中新增的字段
class Settings(BaseSettings):
    # ... 现有字段 ...
    
    # [A1] CORS 白名单
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8080"
    
    # [A2] JWT 双 Token
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # [A4] 环境标识
    ENVIRONMENT: str = "development"
```

### 4.2 .env.example 模板

```env
# === 应用基础 ===
PROJECT_NAME=MianMianMaster Backend
SECRET_KEY=your-secret-key-change-this-in-production
ENVIRONMENT=development

# === CORS ===
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# === JWT ===
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# === Database ===
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-db-password
POSTGRES_DB=mian_mian_db
POSTGRES_PORT=5432

# === Redis ===
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## 五、验收标准

### 5.1 P0 验收 (Day 1-4 完成后)

- [ ] 非白名单来源的跨域请求被拒绝
- [ ] Access Token 30 分钟过期，可通过 Refresh Token 续期
- [ ] 登出后 Access Token 立即失效（黑名单）
- [ ] 权限判断无 `username == "admin"` 硬编码
- [ ] 生产环境启动不执行 `create_all()`
- [ ] Dockerfile 启动命令包含 `alembic upgrade head`

### 5.2 P1 验收 (Day 5-7 完成后)

- [ ] 连续 5 次登录失败后账户锁定 15 分钟
- [ ] 密码重置 Token 只能使用一次
- [ ] SMS 验证码存储哈希值
- [ ] 每日每手机号 SMS 发送上限 10 条
- [ ] SMS 验证码错误 5 次后失效

### 5.3 测试验收

- [ ] 所有新增功能有对应测试用例
- [ ] 现有测试全部通过 (无回归)
- [ ] 安全相关测试覆盖正常/异常/边界场景

## 六、回滚方案

每个 Task 独立提交，如出现问题可单独 revert：

```
git revert <commit-hash>  # 按需回滚单个 Task
```

关键回滚点：
- A2 (JWT 双 Token) 改动最大，如需回滚需同时回滚前端 Token 刷新逻辑
- A4 (自动建表) 回滚后需确保开发环境仍可正常启动

## 七、风险提示

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| JWT 双 Token 改造需前端配合 | 前端需实现 Token 刷新逻辑 | 先实现后端，前端可渐进式对接 |
| Redis 不可用时安全功能降级 | 锁定/黑名单失效 | 增加 Redis 连接异常的降级处理 |
| CORS 白名单遗漏导致前端无法访问 | 开发环境受影响 | 开发环境默认允许 localhost |
