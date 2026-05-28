# Task A2: JWT 双 Token 机制实现

> **优先级**: 🔴 P0 | **工时**: 2 天 | **依赖**: 无  
> **影响范围**: security.py, config.py, auth_service.py, auth.py, deps.py, user.py(schema)

---

## 一、问题描述

**当前代码** ([config.py:12](../../src/core/config.py#L12)):

```python
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8天 = 11520分钟
```

**风险**:
1. Access Token 有效期长达 8 天，一旦泄露攻击者可长期使用
2. 无 Refresh Token 机制，无法实现"短期 Token + 长期会话"
3. 无 Token 黑名单，用户登出后 Token 仍有效
4. JWT 的 `sub` 字段使用 `username`，无法高效定位用户

---

## 二、设计方案

### 2.1 双 Token 架构

```
┌──────────────┐     登录      ┌──────────────────────────────┐
│    Client     │ ──────────→ │ POST /auth/login             │
│              │              │ 返回 access_token + refresh_token │
│              │ ←────────── │                              │
└──────┬───────┘              └──────────────────────────────┘
       │
       │ 携带 access_token 请求 API
       ↓
┌──────────────────────────────┐
│ API 请求                      │
│ Authorization: Bearer <AT>   │
│                              │
│ AT 有效 → 正常响应            │
│ AT 过期 → 返回 401           │
└──────────────────────────────┘
       │
       │ AT 过期，使用 RT 刷新
       ↓
┌──────────────────────────────┐
│ POST /auth/refresh           │
│ Body: { "refresh_token": RT }│
│                              │
│ RT 有效 → 返回新 AT + 新 RT  │
│ RT 无效 → 返回 401，需重新登录│
└──────────────────────────────┘
```

### 2.2 Token 规格对比

| 属性 | Access Token | Refresh Token |
|------|-------------|---------------|
| 有效期 | 30 分钟 | 7 天 |
| 存储位置 | 前端内存/localStorage | 前端 localStorage (httpOnly Cookie 更佳) |
| 用途 | API 请求鉴权 | 刷新 Access Token |
| 撤销方式 | Redis 黑名单 | Redis 白名单 (仅存有效的 RT) |
| JWT sub | `user_id` | `user_id` |
| JWT type | `access` | `refresh` |

### 2.3 Token 黑名单/白名单策略

**Access Token 黑名单** (登出时使用):
```
Redis Key: token:blacklist:{jti}
TTL: Token 剩余有效期
Value: "1"
```

**Refresh Token 白名单** (仅存储有效的 RT):
```
Redis Key: refresh_token:user:{user_id}
TTL: 7 天
Value: refresh_token_jti (UUID)
```

---

## 三、详细实现

### 3.1 修改 `src/core/config.py`

```python
class Settings(BaseSettings):
    # ... 现有字段 ...

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
```

### 3.2 修改 `src/core/security.py`

**完整重构后的代码**:

```python
from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional
from uuid import uuid4
from jose import jwt, JWTError
from src.core.config import settings
from src.db.redis_client import get_redis
import re
import bcrypt


def validate_password_strength(password: str) -> bool:
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    jti = str(uuid4())
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
        "jti": jti,
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def create_refresh_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    jti = str(uuid4())
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "jti": jti,
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

    redis_client = get_redis()
    redis_key = f"refresh_token:user:{subject}"
    ttl_seconds = int((expire - datetime.now(timezone.utc)).total_seconds())
    if ttl_seconds > 0:
        redis_client.setex(redis_key, ttl_seconds, jti)

    return encoded_jwt


def revoke_refresh_token(user_id: int) -> None:
    redis_client = get_redis()
    redis_key = f"refresh_token:user:{user_id}"
    redis_client.delete(redis_key)


def is_refresh_token_valid(user_id: int, jti: str) -> bool:
    redis_client = get_redis()
    redis_key = f"refresh_token:user:{user_id}"
    stored_jti = redis_client.get(redis_key)
    return stored_jti == jti


def add_token_to_blacklist(jti: str, expires_in_seconds: int) -> None:
    redis_client = get_redis()
    redis_key = f"token:blacklist:{jti}"
    if expires_in_seconds > 0:
        redis_client.setex(redis_key, expires_in_seconds, "1")


def is_token_blacklisted(jti: str) -> bool:
    redis_client = get_redis()
    redis_key = f"token:blacklist:{jti}"
    return redis_client.exists(redis_key) > 0


def create_password_reset_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode = {"exp": expire, "sub": email, "type": "reset"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if decoded_token.get("type") != "reset":
            return None
        return decoded_token.get("sub")
    except JWTError:
        return None
```

**关键变更点**:
1. `datetime.utcnow()` → `datetime.now(timezone.utc)` (消除 DeprecationWarning)
2. JWT payload 新增 `type` 字段区分 access/refresh/reset
3. JWT payload 新增 `jti` (JWT ID) 用于黑名单
4. 新增 `create_refresh_token()` — 创建 RT 并存入 Redis 白名单
5. 新增 `revoke_refresh_token()` — 删除 Redis 中的 RT (登出)
6. 新增 `is_refresh_token_valid()` — 校验 RT 是否在白名单
7. 新增 `add_token_to_blacklist()` / `is_token_blacklisted()` — AT 黑名单

### 3.3 修改 `src/schemas/user.py`

**新增/修改 Schema**:

```python
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
```

**变更说明**:
- `Token` 新增 `refresh_token` 字段
- 新增 `RefreshTokenRequest` 用于刷新接口
- `TokenData` 新增 `user_id` 字段

### 3.4 修改 `src/api/deps.py`

**修改 `get_current_user` 函数**:

```python
def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"]
        )
        username: str = payload.get("sub")
        token_type: str = payload.get("type", "")
        jti: str = payload.get("jti", "")

        if username is None or token_type != "access":
            raise credentials_exception

        if security.is_token_blacklisted(jti):
            raise credentials_exception

        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = db.query(User).options(selectinload(User.roles)).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user
```

**变更说明**:
- 校验 `token_type == "access"`，拒绝 refresh token 用于 API 访问
- 校验 `is_token_blacklisted(jti)`，拒绝已登出的 Token

### 3.5 修改 `src/services/auth_service.py`

**修改登录方法返回双 Token**:

```python
class AuthService:
    @staticmethod
    def _build_token_pair(user: UserModel) -> Dict[str, Any]:
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            user.username, expires_delta=access_token_expires
        )
        refresh_token = security.create_refresh_token(user.id)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    @staticmethod
    def swagger_login(db: Session, form_data: OAuth2PasswordRequestForm) -> Dict[str, Any]:
        user = db.query(UserModel).filter(UserModel.username == form_data.username).first()
        if not user or not security.verify_password(form_data.password, user.hashed_password):
            raise BusinessException(code=400, detail="Incorrect username or password")
        elif not user.is_active:
            raise BusinessException(code=400, detail="Inactive user")
        return AuthService._build_token_pair(user)

    @staticmethod
    def login_access_token(db: Session, request: LoginRequest) -> Dict[str, Any]:
        user = db.query(UserModel).filter(UserModel.username == request.username).first()
        if not user or not security.verify_password(request.password, user.hashed_password):
            raise BusinessException(code=400, detail="Incorrect username or password")
        elif not user.is_active:
            raise BusinessException(code=400, detail="Inactive user")
        return AuthService._build_token_pair(user)

    @staticmethod
    def refresh_access_token(db: Session, request: RefreshTokenRequest) -> Dict[str, Any]:
        try:
            payload = jwt.decode(request.refresh_token, settings.SECRET_KEY, algorithms=["HS256"])
        except JWTError:
            raise BusinessException(code=401, detail="Invalid refresh token")

        if payload.get("type") != "refresh":
            raise BusinessException(code=401, detail="Invalid token type")

        user_id = payload.get("sub")
        jti = payload.get("jti", "")

        if not user_id or not security.is_refresh_token_valid(int(user_id), jti):
            raise BusinessException(code=401, detail="Refresh token has been revoked")

        user = db.query(UserModel).filter(UserModel.id == int(user_id)).first()
        if not user or not user.is_active:
            raise BusinessException(code=401, detail="User not found or inactive")

        return AuthService._build_token_pair(user)

    @staticmethod
    def logout(db: Session, current_user: UserModel, token: str) -> str:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            jti = payload.get("jti", "")
            exp = payload.get("exp", 0)
            now = datetime.now(timezone.utc).timestamp()
            remaining = int(exp - now)
            if remaining > 0:
                security.add_token_to_blacklist(jti, remaining)
        except JWTError:
            pass

        security.revoke_refresh_token(current_user.id)
        return "Successfully logged out."

    @staticmethod
    def sms_login(db: Session, request: SmsLoginRequest) -> Dict[str, Any]:
        sms_record = db.query(SmsVerification).filter(
            SmsVerification.phone == request.phone,
            SmsVerification.code == request.code,
            SmsVerification.is_used == False,
            SmsVerification.expires_at > datetime.utcnow()
        ).first()

        if not sms_record:
            raise BusinessException(code=400, detail="Invalid or expired SMS code.")

        sms_record.is_used = True
        db.commit()

        user = db.query(UserModel).filter(UserModel.phone == request.phone).first()
        if not user:
            raise BusinessException(code=404, detail="User with this phone number not found.")

        if not user.is_active:
            raise BusinessException(code=400, detail="Inactive user")

        return AuthService._build_token_pair(user)

    # register_user, generate_password_reset_token, reset_password 保持不变
```

**关键变更点**:
1. 新增 `_build_token_pair()` 私有方法，统一生成双 Token
2. 所有登录方法 (swagger_login, login_access_token, sms_login) 返回双 Token
3. 新增 `refresh_access_token()` — 刷新 AT
4. 新增 `logout()` — 登出 (AT 加入黑名单 + RT 从白名单删除)
5. `from jose import jwt` 需要在 auth_service.py 中新增导入

### 3.6 修改 `src/api/v1/auth.py`

**新增刷新和登出接口**:

```python
from src.schemas.user import (
    Token, UserCreate, User, SmsSendRequest, SmsLoginRequest,
    PasswordResetRequest, PasswordResetTokenRequest, LoginRequest,
    RefreshTokenRequest
)

# ... 现有接口保持不变 ...

@router.post("/refresh", response_model=ResponseModel[Token])
def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> Any:
    token_data = auth_service.refresh_access_token(db, request)
    return ResponseModel(data=token_data)


@router.post("/logout", response_model=ResponseModel[str])
def logout(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Any:
    message = auth_service.logout(db, current_user, token)
    return ResponseModel(data=message)
```

**新增导入**:

```python
from src.api.deps import get_db, get_current_user, oauth2_scheme
```

---

## 四、测试用例

### 4.1 新增 `tests/test_jwt_dual_token.py`

```python
from fastapi.testclient import TestClient


def test_login_returns_both_tokens(client: TestClient):
    """登录应返回 access_token 和 refresh_token"""
    response = client.post("/api/v1/auth/login", json={
        "username": "admin_test",
        "password": "Admin@123"
    })
    data = response.json()["data"]
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_access_token_works_for_api(client: TestClient):
    """Access Token 应能正常访问 API"""
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "admin_test",
        "password": "Admin@123"
    })
    access_token = login_resp.json()["data"]["access_token"]

    response = client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {access_token}"
    })
    assert response.status_code == 200


def test_refresh_token_cannot_access_api(client: TestClient):
    """Refresh Token 不应用于 API 访问"""
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "admin_test",
        "password": "Admin@123"
    })
    refresh_token = login_resp.json()["data"]["refresh_token"]

    response = client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {refresh_token}"
    })
    assert response.status_code == 401


def test_refresh_token_generates_new_pair(client: TestClient):
    """使用 Refresh Token 应获得新的 Token 对"""
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "admin_test",
        "password": "Admin@123"
    })
    refresh_token = login_resp.json()["data"]["refresh_token"]

    response = client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert response.status_code == 200
    data = response.json()["data"]
    assert "access_token" in data
    assert "refresh_token" in data


def test_logout_invalidates_access_token(client: TestClient):
    """登出后 Access Token 应失效"""
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "admin_test",
        "password": "Admin@123"
    })
    tokens = login_resp.json()["data"]
    access_token = tokens["access_token"]

    logout_resp = client.post("/api/v1/auth/logout", headers={
        "Authorization": f"Bearer {access_token}"
    })
    assert logout_resp.status_code == 200

    me_resp = client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {access_token}"
    })
    assert me_resp.status_code == 401


def test_logout_invalidates_refresh_token(client: TestClient):
    """登出后 Refresh Token 应失效"""
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "admin_test",
        "password": "Admin@123"
    })
    tokens = login_resp.json()["data"]
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    client.post("/api/v1/auth/logout", headers={
        "Authorization": f"Bearer {access_token}"
    })

    refresh_resp = client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert refresh_resp.status_code == 200
    assert refresh_resp.json()["code"] == 401


def test_invalid_refresh_token_rejected(client: TestClient):
    """无效的 Refresh Token 应被拒绝"""
    response = client.post("/api/v1/auth/refresh", json={
        "refresh_token": "invalid.token.here"
    })
    assert response.status_code == 200
    assert response.json()["code"] == 401
```

---

## 五、前端对接指南

### 5.1 登录响应变更

```json
// 修改前
{
  "code": 200,
  "data": {
    "access_token": "eyJ...",
    "token_type": "bearer"
  }
}

// 修改后
{
  "code": 200,
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer"
  }
}
```

### 5.2 Token 刷新流程 (前端实现建议)

```javascript
let accessToken = localStorage.getItem('access_token');
let refreshToken = localStorage.getItem('refresh_token');

async function apiRequest(url, options = {}) {
  options.headers = {
    ...options.headers,
    'Authorization': `Bearer ${accessToken}`,
  };

  let response = await fetch(url, options);

  if (response.status === 401) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      options.headers['Authorization'] = `Bearer ${accessToken}`;
      response = await fetch(url, options);
    } else {
      redirectToLogin();
    }
  }

  return response;
}

async function tryRefreshToken() {
  try {
    const response = await fetch('/api/v1/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    const data = await response.json();
    if (data.code === 200) {
      accessToken = data.data.access_token;
      refreshToken = data.data.refresh_token;
      localStorage.setItem('access_token', accessToken);
      localStorage.setItem('refresh_token', refreshToken);
      return true;
    }
  } catch {}
  return false;
}
```

---

## 六、验证清单

- [ ] `config.py` ACCESS_TOKEN_EXPIRE_MINUTES 改为 30
- [ ] `config.py` 新增 REFRESH_TOKEN_EXPIRE_DAYS = 7
- [ ] `security.py` 新增 create_refresh_token / revoke_refresh_token / is_refresh_token_valid
- [ ] `security.py` 新增 add_token_to_blacklist / is_token_blacklisted
- [ ] `security.py` datetime.utcnow() → datetime.now(timezone.utc)
- [ ] `security.py` JWT payload 新增 type 和 jti 字段
- [ ] `schemas/user.py` Token 新增 refresh_token 字段
- [ ] `schemas/user.py` 新增 RefreshTokenRequest
- [ ] `deps.py` get_current_user 校验 token_type 和黑名单
- [ ] `auth_service.py` 所有登录方法返回双 Token
- [ ] `auth_service.py` 新增 refresh_access_token 方法
- [ ] `auth_service.py` 新增 logout 方法
- [ ] `auth.py` 新增 /auth/refresh 接口
- [ ] `auth.py` 新增 /auth/logout 接口
- [ ] 所有测试通过

---

## 七、提交信息

```
feat(auth): implement JWT dual-token mechanism with refresh and blacklist

- Reduce access token expiry to 30 minutes
- Add refresh token with 7-day expiry stored in Redis whitelist
- Add token blacklist for logout (Redis-based)
- Add /auth/refresh endpoint for token renewal
- Add /auth/logout endpoint for session invalidation
- Add jti (JWT ID) and type fields to JWT payload
- Replace datetime.utcnow() with datetime.now(timezone.utc)
- Update Token schema to include refresh_token
- Add comprehensive JWT security test cases
```
