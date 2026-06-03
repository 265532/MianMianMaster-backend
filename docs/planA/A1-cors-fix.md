# Task A1: CORS 安全配置修复

> **优先级**: 🔴 P0 | **工时**: 0.5 天 | **依赖**: 无

---

## 一、问题描述

**当前代码** ([main.py:34-40](../../src/main.py#L34-L40)):

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # ❌ 允许所有来源
    allow_credentials=True,     # ❌ 与 allow_origins=["*"] 组合不安全
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**风险**:
1. 任何域名都可以向本 API 发起跨域请求，存在 CSRF 攻击面
2. `allow_credentials=True` 与 `allow_origins=["*"]` 组合在浏览器中实际被阻止，但服务端未做限制
3. 恶意网站可以诱导已登录用户发起请求窃取数据

---

## 二、修复方案

### 2.1 修改 `src/core/config.py`

**新增配置项**:

```python
class Settings(BaseSettings):
    # ... 现有字段 ...

    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8080"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
```

**变更说明**:
- `ALLOWED_ORIGINS` 使用逗号分隔的字符串，便于通过环境变量配置
- `cors_origins_list` 属性自动解析为列表
- 默认值包含前端开发常用端口

### 2.2 修改 `src/main.py`

**替换 CORS 中间件配置**:

```python
# 修改前
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 修改后
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
```

**变更说明**:
- `allow_origins` 从环境变量读取白名单
- `allow_methods` 收紧为实际使用的方法
- `allow_headers` 收紧为实际需要的请求头

### 2.3 新建 `.env.example`

在 `.env.example` 中新增:

```env
# === CORS ===
# 逗号分隔的允许来源列表，生产环境必须修改
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

---

## 三、测试用例

### 3.1 新增测试文件 `tests/test_cors_security.py`

```python
from fastapi.testclient import TestClient


def test_cors_allows_allowed_origin(client: TestClient):
    """白名单内的 Origin 应被允许"""
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_blocks_disallowed_origin(client: TestClient):
    """白名单外的 Origin 应被拒绝"""
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://evil-site.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" not in response.headers


def test_cors_allowed_methods_restricted(client: TestClient):
    """仅允许指定的 HTTP 方法"""
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "TRACE",
        },
    )
    allow_methods = response.headers.get("access-control-allow-methods", "")
    assert "TRACE" not in allow_methods
```

### 3.2 现有测试回归

确保 `test_health_check` 和 `test_openapi_schema` 仍通过。

---

## 四、验证清单

- [ ] `config.py` 新增 `ALLOWED_ORIGINS` 字段和 `cors_origins_list` 属性
- [ ] `main.py` CORS 中间件使用 `settings.cors_origins_list`
- [ ] `main.py` CORS `allow_methods` 和 `allow_headers` 收紧
- [ ] `.env.example` 包含 `ALLOWED_ORIGINS` 配置项
- [ ] 白名单内 Origin 可以正常跨域访问
- [ ] 白名单外 Origin 被拒绝
- [ ] 现有测试全部通过

---

## 五、提交信息

```
fix(security): restrict CORS to configured origin whitelist

- Add ALLOWED_ORIGINS config field with comma-separated parsing
- Replace allow_origins=["*"] with settings-driven whitelist
- Restrict allow_methods and allow_headers to required set
- Add .env.example with CORS configuration template
- Add CORS security test cases
```
