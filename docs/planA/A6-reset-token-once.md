# Task A6: 密码重置 Token 单次使用

> **优先级**: 🟠 P1 | **工时**: 1 天 | **依赖**: 无  
> **影响范围**: auth_service.py, security.py

---

## 一、问题描述

**当前代码** ([auth_service.py:134-158](../../src/services/auth_service.py#L134-L158)):

```python
def generate_password_reset_token(db: Session, request: PasswordResetTokenRequest) -> str:
    user = db.query(UserModel).filter(UserModel.email == request.email).first()
    if not user:
        raise BusinessException(code=404, detail="User not found.")
    token = security.create_password_reset_token(email=user.email)
    return token

def reset_password(db: Session, request: PasswordResetRequest) -> str:
    email = security.verify_password_reset_token(request.token)
    if not email:
        raise BusinessException(code=400, detail="Invalid or expired reset token.")
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user:
        raise BusinessException(code=404, detail="User not found.")
    if not security.validate_password_strength(request.new_password):
        raise BusinessException(code=400, detail="Password must be at least 8 characters...")
    user.hashed_password = security.get_password_hash(request.new_password)
    db.commit()
    return "Password reset successfully."
```

**风险**:
1. 同一密码重置 Token 可被多次使用（重放攻击）
2. Token 被截获后，攻击者可在用户重置前/后使用
3. 无频率限制，可反复尝试不同 Token

---

## 二、设计方案

### 2.1 方案选择: Redis 存储已使用 Token

**选择 Redis 而非数据库字段的原因**:
- Token 本身是短期有效的 (15分钟)，不需要持久化
- Redis 的 TTL 自动过期机制与 Token 有效期天然匹配
- 无需修改数据库模型和生成 Alembic 迁移

### 2.2 Redis Key 设计

| Key 模式 | 用途 | TTL | Value |
|----------|------|-----|-------|
| `pwd_reset:used:{jti}` | 标记已使用的重置 Token | 15 分钟 (与 Token 有效期一致) | "1" |
| `pwd_reset:cooldown:{email}` | 重置请求冷却 | 5 分钟 | "1" |

---

## 三、详细实现

### 3.1 修改 `src/core/security.py`

**修改 `create_password_reset_token` 增加 jti**:

```python
def create_password_reset_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    jti = str(uuid4())
    to_encode = {"exp": expire, "sub": email, "type": "reset", "jti": jti}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt
```

**新增 Token 使用标记函数**:

```python
def mark_reset_token_used(jti: str) -> None:
    redis_client = get_redis()
    redis_key = f"pwd_reset:used:{jti}"
    redis_client.setex(redis_key, 900, "1")  # 15 minutes TTL


def is_reset_token_used(jti: str) -> bool:
    redis_client = get_redis()
    redis_key = f"pwd_reset:used:{jti}"
    return redis_client.exists(redis_key) > 0
```

### 3.2 修改 `src/services/auth_service.py`

**修改 `generate_password_reset_token` 增加冷却**:

```python
@staticmethod
def generate_password_reset_token(db: Session, request: PasswordResetTokenRequest) -> str:
    redis_client = get_redis()
    cooldown_key = f"pwd_reset:cooldown:{request.email}"
    if redis_client.exists(cooldown_key):
        raise BusinessException(code=429, detail="Please wait before requesting another password reset.")

    user = db.query(UserModel).filter(UserModel.email == request.email).first()
    if not user:
        raise BusinessException(code=404, detail="User not found.")

    token = security.create_password_reset_token(email=user.email)

    redis_client.setex(cooldown_key, 300, "1")  # 5 minutes cooldown

    return token
```

**修改 `reset_password` 增加单次使用校验**:

```python
@staticmethod
def reset_password(db: Session, request: PasswordResetRequest) -> str:
    try:
        payload = jwt.decode(request.token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "reset":
            raise BusinessException(code=400, detail="Invalid reset token.")
        jti = payload.get("jti", "")
        email = payload.get("sub")
    except JWTError:
        raise BusinessException(code=400, detail="Invalid or expired reset token.")

    if not email:
        raise BusinessException(code=400, detail="Invalid reset token.")

    if security.is_reset_token_used(jti):
        raise BusinessException(code=400, detail="This reset token has already been used.")

    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user:
        raise BusinessException(code=404, detail="User not found.")

    if not security.validate_password_strength(request.new_password):
        raise BusinessException(code=400, detail="Password must be at least 8 characters long and contain uppercase, lowercase, digit, and special character.")

    user.hashed_password = security.get_password_hash(request.new_password)
    db.commit()

    security.mark_reset_token_used(jti)

    return "Password reset successfully."
```

**变更说明**:
1. 先解码 Token 获取 `jti`，再校验是否已使用
2. 密码重置成功后，标记 Token 为已使用
3. 已使用的 Token 再次请求返回错误
4. 生成重置 Token 时增加 5 分钟冷却期

---

## 四、测试用例

### 4.1 新增 `tests/test_password_reset.py`

```python
from src.db.redis_client import get_redis


def _clear_reset_keys():
    redis_client = get_redis()
    for key in redis_client.scan_iter("pwd_reset:*"):
        redis_client.delete(key)


def test_reset_token_single_use(client):
    """密码重置 Token 只能使用一次"""
    _clear_reset_keys()

    token_resp = client.post("/api/v1/auth/password/reset-token", json={
        "email": "admin_test@example.com"
    })
    token = token_resp.json()["data"]

    first_reset = client.post("/api/v1/auth/password/reset", json={
        "token": token,
        "new_password": "NewPassword@123"
    })
    assert first_reset.json()["code"] == 200

    second_reset = client.post("/api/v1/auth/password/reset", json={
        "token": token,
        "new_password": "AnotherPass@456"
    })
    assert second_reset.json()["code"] == 400
    assert "already been used" in second_reset.json()["message"]


def test_reset_cooldown(client):
    """密码重置请求应有冷却期"""
    _clear_reset_keys()

    first_req = client.post("/api/v1/auth/password/reset-token", json={
        "email": "admin_test@example.com"
    })
    assert first_req.json()["code"] == 200

    second_req = client.post("/api/v1/auth/password/reset-token", json={
        "email": "admin_test@example.com"
    })
    assert second_req.json()["code"] == 429


def test_expired_reset_token_rejected(client):
    """过期的重置 Token 应被拒绝"""
    _clear_reset_keys()

    response = client.post("/api/v1/auth/password/reset", json={
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.expired",
        "new_password": "NewPassword@123"
    })
    assert response.json()["code"] == 400
```

---

## 五、验证清单

- [ ] `security.py` `create_password_reset_token` 新增 jti 字段
- [ ] `security.py` 新增 `mark_reset_token_used()` 函数
- [ ] `security.py` 新增 `is_reset_token_used()` 函数
- [ ] `auth_service.py` `reset_password` 校验 Token 是否已使用
- [ ] `auth_service.py` `reset_password` 成功后标记 Token 已使用
- [ ] `auth_service.py` `generate_password_reset_token` 增加 5 分钟冷却
- [ ] 同一 Token 第二次使用返回错误
- [ ] 冷却期内重复请求返回 429

---

## 六、提交信息

```
feat(auth): enforce single-use password reset tokens

- Add jti field to password reset JWT payload
- Add Redis-based used token tracking with auto-expiry
- Reject already-used reset tokens with clear error
- Add 5-minute cooldown between reset token requests
- Add password reset security test cases
```
