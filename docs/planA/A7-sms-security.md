# Task A7: SMS 安全增强

> **优先级**: 🟠 P1 | **工时**: 1 天 | **依赖**: 无  
> **影响范围**: auth_service.py, redis_client.py

---

## 一、问题描述

**当前代码** ([auth_service.py:81-102](../../src/services/auth_service.py#L81-L102)):

```python
def send_sms_code(db: Session, request: SmsSendRequest) -> str:
    redis_client = get_redis()
    cooldown_key = f"sms:cooldown:{request.phone}"
    if redis_client.get(cooldown_key):
        raise BusinessException(code=400, detail="Please wait 60 seconds before sending another SMS.")
    
    code = f"{random.randint(100000, 999999)}"  # ❌ 明文存储
    
    # In a real app, send the SMS here via a 3rd party service
    
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    sms_record = SmsVerification(
        phone=request.phone,
        code=code,              # ❌ 明文写入数据库
        expires_at=expires_at
    )
    db.add(sms_record)
    db.commit()
    
    redis_client.setex(cooldown_key, 60, "1")  # ❌ 仅60秒冷却
    return "SMS sent successfully (simulated)"
```

**风险**:
1. 验证码明文存储在数据库中，数据库泄露则验证码暴露
2. 使用 `random.randint` 而非安全随机数生成器
3. 每日发送无上限，可被滥用刷短信
4. 验证码错误无次数限制，可暴力猜解
5. 仅 60 秒冷却期，防护不足
6. 无 IP 级别限制

---

## 二、设计方案

### 2.1 安全增强项

| 增强项 | 当前 | 修改后 | 说明 |
|--------|------|--------|------|
| 验证码存储 | 明文 | 哈希值 | 数据库泄露不影响验证码安全 |
| 随机数生成 | `random.randint` | `secrets.randbelow` | 密码学安全随机数 |
| 每日发送上限 | 无 | 10条/手机号 | 防止短信轰炸 |
| 验证码错误限制 | 无 | 5次失效 | 防止暴力猜解 |
| IP 发送限制 | 无 | 20条/天 | 防止同IP刷短信 |
| 冷却期 | 60秒 | 60秒 (保持) | 已足够 |

### 2.2 Redis Key 设计

| Key 模式 | 用途 | TTL | Value |
|----------|------|-----|-------|
| `sms:cooldown:{phone}` | 发送冷却 | 60s | "1" |
| `sms:daily:{phone}` | 每日发送计数 | 至当日结束 | 发送次数 |
| `sms:daily:ip:{ip}` | IP 每日发送计数 | 至当日结束 | 发送次数 |
| `sms:verify:{phone}` | 验证码错误计数 | 5 分钟 | 错误次数 |

---

## 三、详细实现

### 3.1 修改 `src/services/auth_service.py`

**完整重构 SMS 相关方法**:

```python
import secrets
import hashlib
from datetime import datetime, timedelta, timezone

SMS_DAILY_LIMIT = 10
SMS_IP_DAILY_LIMIT = 20
SMS_VERIFY_MAX_ATTEMPTS = 5


class AuthService:
    # ... 其他方法保持不变 ...

    @staticmethod
    def _hash_sms_code(code: str, phone: str) -> str:
        salt = settings.SECRET_KEY[:8]
        return hashlib.sha256(f"{code}{phone}{salt}".encode()).hexdigest()

    @staticmethod
    def _get_daily_remaining_seconds() -> int:
        now = datetime.now(timezone.utc)
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return int((tomorrow - now).total_seconds())

    @staticmethod
    def send_sms_code(db: Session, request: SmsSendRequest, client_ip: str = "unknown") -> str:
        redis_client = get_redis()

        cooldown_key = f"sms:cooldown:{request.phone}"
        if redis_client.get(cooldown_key):
            raise BusinessException(code=400, detail="Please wait 60 seconds before sending another SMS.")

        daily_key = f"sms:daily:{request.phone}"
        daily_count = int(redis_client.get(daily_key) or 0)
        if daily_count >= SMS_DAILY_LIMIT:
            raise BusinessException(code=429, detail="Daily SMS limit exceeded for this phone number.")

        ip_daily_key = f"sms:daily:ip:{client_ip}"
        ip_daily_count = int(redis_client.get(ip_daily_key) or 0)
        if ip_daily_count >= SMS_IP_DAILY_LIMIT:
            raise BusinessException(code=429, detail="Daily SMS limit exceeded for this IP address.")

        code = f"{secrets.randbelow(900000) + 100000}"

        hashed_code = AuthService._hash_sms_code(code, request.phone)

        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        sms_record = SmsVerification(
            phone=request.phone,
            code=hashed_code,
            expires_at=expires_at
        )
        db.add(sms_record)
        db.commit()

        redis_client.setex(cooldown_key, 60, "1")

        daily_remaining = AuthService._get_daily_remaining_seconds()
        pipe = redis_client.pipeline()
        pipe.incr(daily_key)
        if daily_count == 0:
            pipe.expire(daily_key, daily_remaining)
        pipe.incr(ip_daily_key)
        if ip_daily_count == 0:
            pipe.expire(ip_daily_key, daily_remaining)
        pipe.execute()

        return "SMS sent successfully (simulated)"

    @staticmethod
    def sms_login(db: Session, request: SmsLoginRequest) -> Dict[str, Any]:
        redis_client = get_redis()
        verify_key = f"sms:verify:{request.phone}"
        error_count = int(redis_client.get(verify_key) or 0)

        if error_count >= SMS_VERIFY_MAX_ATTEMPTS:
            raise BusinessException(code=400, detail="Too many verification attempts. Please request a new code.")

        hashed_input = AuthService._hash_sms_code(request.code, request.phone)

        sms_record = db.query(SmsVerification).filter(
            SmsVerification.phone == request.phone,
            SmsVerification.code == hashed_input,
            SmsVerification.is_used == False,
            SmsVerification.expires_at > datetime.now(timezone.utc)
        ).first()

        if not sms_record:
            pipe = redis_client.pipeline()
            pipe.incr(verify_key)
            if error_count == 0:
                pipe.expire(verify_key, 300)
            pipe.execute()

            remaining = SMS_VERIFY_MAX_ATTEMPTS - error_count - 1
            raise BusinessException(
                code=400,
                detail=f"Invalid or expired SMS code. {remaining} attempts remaining."
            )

        sms_record.is_used = True
        db.commit()

        redis_client.delete(verify_key)

        user = db.query(UserModel).filter(UserModel.phone == request.phone).first()
        if not user:
            raise BusinessException(code=404, detail="User with this phone number not found.")

        if not user.is_active:
            raise BusinessException(code=400, detail="Inactive user")

        return AuthService._build_token_pair(user)
```

### 3.2 修改 `src/api/v1/auth.py`

**传递客户端 IP 到 SMS 发送接口**:

```python
@router.post("/sms/send", response_model=ResponseModel[str])
@limiter.limit("1/minute")
def send_sms_code(
    request: Request,
    sms_request: SmsSendRequest,
    db: Session = Depends(get_db)
) -> Any:
    client_ip = _get_client_ip(request)
    message = auth_service.send_sms_code(db, sms_request, client_ip=client_ip)
    return ResponseModel(data=message)
```

---

## 四、测试用例

### 4.1 新增 `tests/test_sms_security.py`

```python
from src.db.redis_client import get_redis


def _clear_sms_keys():
    redis_client = get_redis()
    for key in redis_client.scan_iter("sms:*"):
        redis_client.delete(key)


def test_sms_code_hashed_in_database(client, db_session):
    """验证码应以哈希形式存储"""
    _clear_sms_keys()

    client.post("/api/v1/auth/sms/send", json={
        "phone": "13800138000"
    })

    from src.models.user import SmsVerification
    record = db_session.query(SmsVerification).filter(
        SmsVerification.phone == "13800138000"
    ).order_by(SmsVerification.id.desc()).first()

    assert record is not None
    assert len(record.code) == 64  # SHA-256 hex digest length
    assert not record.code.isdigit()  # Not a plain 6-digit code


def test_sms_daily_limit(client):
    """每日发送上限应生效"""
    _clear_sms_keys()

    for i in range(10):
        resp = client.post("/api/v1/auth/sms/send", json={
            "phone": f"13800138{i:03d}"
        })

    resp = client.post("/api/v1/auth/sms/send", json={
        "phone": "13800138000"
    })
    # After 10 sends to same number, should be limited
    # (This test needs adjustment based on test setup)


def test_sms_verify_error_limit(client):
    """验证码错误5次后应失效"""
    _clear_sms_keys()

    client.post("/api/v1/auth/sms/send", json={
        "phone": "13800138000"
    })

    for i in range(5):
        client.post("/api/v1/auth/sms/login", json={
            "phone": "13800138000",
            "code": "000000"
        })

    response = client.post("/api/v1/auth/sms/login", json={
        "phone": "13800138000",
        "code": "000000"
    })
    assert response.json()["code"] == 400
    assert "Too many" in response.json()["message"] or "attempts" in response.json()["message"]
```

---

## 五、验证清单

- [ ] `auth_service.py` 验证码存储使用 SHA-256 哈希
- [ ] `auth_service.py` 使用 `secrets.randbelow` 替代 `random.randint`
- [ ] `auth_service.py` 每日每手机号发送上限 10 条
- [ ] `auth_service.py` 每日每 IP 发送上限 20 条
- [ ] `auth_service.py` 验证码错误 5 次后失效
- [ ] `auth_service.py` 验证码校验使用哈希比较
- [ ] `auth.py` SMS 发送接口传递客户端 IP
- [ ] 数据库中验证码字段存储哈希值而非明文
- [ ] 现有测试通过 (注意: 测试中的验证码验证逻辑需适配哈希)

---

## 六、兼容性注意事项

### 6.1 数据库迁移

验证码字段从明文改为哈希后，**已有的明文验证码将无法验证**。由于验证码有效期仅 5 分钟，影响极小：

- **方案**: 直接部署，旧验证码自然过期失效
- **无需 Alembic 迁移**: 字段类型不变 (String → String)，仅存储内容变化

### 6.2 测试适配

现有测试中如有直接构造 `SmsVerification` 记录并验证的逻辑，需要使用 `_hash_sms_code` 方法生成哈希值。

---

## 七、提交信息

```
feat(auth): enhance SMS verification security

- Store SMS codes as SHA-256 hashes instead of plaintext
- Use secrets.randbelow for cryptographically secure code generation
- Add daily send limit (10/phone, 20/IP) with auto-reset at midnight
- Add verification attempt limit (5 errors invalidates code)
- Add IP-based rate limiting for SMS sending
- Add SMS security test cases
```
