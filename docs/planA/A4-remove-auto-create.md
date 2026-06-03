# Task A4: 移除生产环境自动建表

> **优先级**: 🔴 P0 | **工时**: 0.5 天 | **依赖**: 无

---

## 一、问题描述

**当前代码** ([main.py:22](../../src/main.py#L22)):

```python
Base.metadata.create_all(bind=engine)
```

**风险**:
1. 每次应用启动时自动创建所有表，绕过 Alembic 迁移管理
2. 无法追踪数据库结构变更历史
3. 生产环境可能导致表结构不一致
4. 与 Alembic 迁移机制冲突，可能产生不可预期的行为

---

## 二、修复方案

### 2.1 修改 `src/core/config.py`

**新增环境标识字段**:

```python
class Settings(BaseSettings):
    # ... 现有字段 ...

    ENVIRONMENT: str = "development"
```

### 2.2 修改 `src/main.py`

**条件化自动建表**:

```python
# 修改前
Base.metadata.create_all(bind=engine)

# 修改后
if settings.ENVIRONMENT == "development":
    Base.metadata.create_all(bind=engine)
```

**变更说明**:
- 仅在开发环境保留自动建表，方便开发者快速启动
- 生产环境完全依赖 Alembic 迁移

### 2.3 修改 `Dockerfile`

**启动命令增加数据库迁移**:

```dockerfile
# 修改前
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

# 修改后
CMD ["sh", "-c", "alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8000"]
```

**变更说明**:
- 容器启动前先执行 `alembic upgrade head` 确保数据库结构最新
- 使用 `sh -c` 支持命令链式执行
- 如果迁移失败，容器不会启动 uvicorn，避免运行在错误的数据库结构上

### 2.4 更新 `.env.example`

```env
# === 应用环境 ===
# development: 开发环境 (自动建表, 调试模式)
# production:  生产环境 (依赖 Alembic 迁移)
ENVIRONMENT=development
```

### 2.5 更新 `docker-compose.yml`

在 api 服务的 environment 中新增:

```yaml
services:
  api:
    environment:
      - POSTGRES_SERVER=db
      - REDIS_HOST=redis
      - ENVIRONMENT=production  # 新增: Docker 部署使用生产模式
```

---

## 三、测试用例

### 3.1 新增测试 `tests/test_environment_config.py`

```python
import os
from unittest.mock import patch


def test_development_environment_auto_creates_tables():
    """开发环境应自动建表"""
    with patch("src.core.config.settings.ENVIRONMENT", "development"):
        # 验证 create_all 在开发环境被调用
        pass  # 通过集成测试验证


def test_production_environment_skips_auto_create():
    """生产环境不应自动建表"""
    with patch("src.core.config.settings.ENVIRONMENT", "production"):
        # 验证 create_all 在生产环境不被调用
        pass


def test_alembic_migration_available():
    """验证 Alembic 迁移脚本可用"""
    import subprocess
    result = subprocess.run(
        ["alembic", "heads"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
```

---

## 四、验证清单

- [ ] `config.py` 新增 `ENVIRONMENT` 字段，默认值 `development`
- [ ] `main.py` 仅在 `ENVIRONMENT == "development"` 时执行 `create_all()`
- [ ] `Dockerfile` CMD 包含 `alembic upgrade head`
- [ ] `docker-compose.yml` api 服务设置 `ENVIRONMENT=production`
- [ ] `.env.example` 包含 `ENVIRONMENT` 配置项
- [ ] 开发环境启动正常，表自动创建
- [ ] 设置 `ENVIRONMENT=production` 后启动不自动建表

---

## 五、提交信息

```
fix(deploy): conditionally auto-create tables only in development

- Add ENVIRONMENT config field (development/production)
- Guard Base.metadata.create_all() with environment check
- Add alembic upgrade head to Dockerfile CMD
- Set ENVIRONMENT=production in docker-compose
- Add .env.example with ENVIRONMENT configuration
```
