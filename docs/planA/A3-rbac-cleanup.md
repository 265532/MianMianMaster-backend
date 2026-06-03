# Task A3: RBAC 权限逻辑清理

> **优先级**: 🔴 P0 | **工时**: 1 天 | **依赖**: 无  
> **影响范围**: deps.py

---

## 一、问题描述

**当前代码** ([deps.py:86-92](../../src/api/deps.py#L86-L92)):

```python
required_perm = f"{resource}:{action}"
if required_perm not in perms and "all:all" not in perms and current_user.username != "admin":
    # Auto-grant all permissions to 'admin' role regardless of username if needed,
    # or just rely on 'admin' username bypass.
    has_admin_role = any(r.name == 'admin' for r in current_user.roles)
    if not has_admin_role:
        raise HTTPException(status_code=403, detail="Not enough permissions")
```

**问题**:
1. `current_user.username != "admin"` — 基于用户名硬编码判断，绕过了 RBAC 体系
2. 注释暴露了逻辑混乱："靠 username bypass 还是靠 role 判断？"
3. 如果管理员用户名被修改，权限判断立即失效
4. `has_admin_role` 的检查在 `username != "admin"` 条件之后，逻辑冗余
5. `any(r.name == 'admin' for r in current_user.roles)` 每次请求都遍历角色列表

---

## 二、修复方案

### 2.1 设计原则

1. **权限判断仅基于角色**，不基于用户名
2. **超级管理员角色** 通过 `all:all` 权限或角色名称常量判断
3. **逻辑清晰**: 先检查权限 → 再检查超级管理员角色 → 否则拒绝

### 2.2 修改 `src/api/deps.py`

**完整重构 `check_permissions` 函数**:

```python
from typing import Generator, List, Callable
import json
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session, selectinload
from src.core.config import settings
from src.core.exceptions import BusinessException
from src.db.database import get_db
from src.db.redis_client import get_redis
from src.models.user import User, Role, Permission
from src.schemas.user import TokenData

SUPER_ADMIN_ROLE = "admin"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/swagger-login")

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
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = db.query(User).options(selectinload(User.roles)).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_role_permissions(db: Session, role: Role) -> List[Permission]:
    permissions = list(role.permissions)
    if role.parent_id:
        parent = db.query(Role).options(selectinload(Role.permissions)).filter(Role.id == role.parent_id).first()
        if parent:
            permissions.extend(get_role_permissions(db, parent))
    return permissions

def _is_super_admin(user: User) -> bool:
    return any(r.name == SUPER_ADMIN_ROLE for r in user.roles)

def _get_user_permissions(db: Session, user: User) -> List[str]:
    redis_client = get_redis()
    cache_key = f"user:perms:{user.id}"

    perms = None
    try:
        cached_perms = redis_client.get(cache_key)
        if cached_perms:
            perms = json.loads(cached_perms)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Redis cache error: {e}")

    if perms is None:
        perms = []
        for role in user.roles:
            full_role = db.query(Role).options(selectinload(Role.permissions)).filter(Role.id == role.id).first()
            role_perms = get_role_permissions(db, full_role)
            for p in role_perms:
                perms.append(f"{p.resource}:{p.action}")

        perms = list(set(perms))
        try:
            redis_client.setex(cache_key, 3600, json.dumps(perms))
        except Exception:
            pass

    return perms

def check_permissions(resource: str, action: str) -> Callable:
    def permission_checker(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        if _is_super_admin(current_user):
            return current_user

        perms = _get_user_permissions(db, current_user)

        required_perm = f"{resource}:{action}"
        if required_perm in perms or "all:all" in perms:
            return current_user

        raise HTTPException(status_code=403, detail="Not enough permissions")

    return permission_checker
```

**关键变更点**:

1. **新增 `SUPER_ADMIN_ROLE = "admin"` 常量** — 替代硬编码字符串
2. **新增 `_is_super_admin()` 函数** — 超级管理员判断逻辑独立
3. **新增 `_get_user_permissions()` 函数** — 权限获取逻辑独立
4. **`check_permissions` 逻辑简化**:
   - 超级管理员 → 直接放行
   - 普通用户 → 检查权限列表
   - 无权限 → 403
5. **移除 `current_user.username != "admin"` 硬编码**

### 2.3 逻辑对比

```
修改前:
  required_perm not in perms 
  AND "all:all" not in perms 
  AND username != "admin"    ← 硬编码
  → 检查 has_admin_role     ← 冗余
  → 403

修改后:
  is_super_admin?           ← 基于角色
  → 放行
  → required_perm in perms OR "all:all" in perms?
  → 放行
  → 403
```

---

## 三、测试用例

### 3.1 新增 `tests/test_rbac_permissions.py`

```python
from src.api.deps import _is_super_admin, SUPER_ADMIN_ROLE
from src.models.user import User, Role


def test_super_admin_detected_by_role():
    """拥有 admin 角色的用户应被识别为超级管理员"""
    admin_role = Role(name="admin", description="Admin")
    user = User(
        username="any_admin_name",
        email="admin@example.com",
        hashed_password="xxx",
        is_active=True,
    )
    user.roles.append(admin_role)
    assert _is_super_admin(user) is True


def test_non_admin_not_super_admin():
    """没有 admin 角色的用户不是超级管理员"""
    student_role = Role(name="student", description="Student")
    user = User(
        username="student1",
        email="student@example.com",
        hashed_password="xxx",
        is_active=True,
    )
    user.roles.append(student_role)
    assert _is_super_admin(user) is False


def test_admin_username_without_role_not_super():
    """用户名为 admin 但没有 admin 角色的用户不是超级管理员"""
    student_role = Role(name="student", description="Student")
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password="xxx",
        is_active=True,
    )
    user.roles.append(student_role)
    assert _is_super_admin(user) is False


def test_super_admin_role_constant():
    """超级管理员角色常量应为 'admin'"""
    assert SUPER_ADMIN_ROLE == "admin"


def test_check_permissions_allows_super_admin(client):
    """超级管理员应能访问所有接口"""
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "admin_test",
        "password": "Admin@123"
    })
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/rbac/roles", headers=headers)
    assert response.status_code == 200
```

---

## 四、验证清单

- [ ] `deps.py` 新增 `SUPER_ADMIN_ROLE` 常量
- [ ] `deps.py` 新增 `_is_super_admin()` 函数
- [ ] `deps.py` 新增 `_get_user_permissions()` 函数
- [ ] `deps.py` `check_permissions` 移除 `username == "admin"` 判断
- [ ] `deps.py` `check_permissions` 逻辑: 超管放行 → 权限检查 → 403
- [ ] 用户名为 admin 但无 admin 角色的用户不能绕过权限
- [ ] 拥有 admin 角色的用户（无论用户名）可访问所有接口
- [ ] 现有测试全部通过

---

## 五、提交信息

```
fix(auth): remove hardcoded admin username bypass from RBAC

- Add SUPER_ADMIN_ROLE constant replacing hardcoded "admin" string
- Extract _is_super_admin() for role-based super admin detection
- Extract _get_user_permissions() for cleaner permission retrieval
- Simplify check_permissions: super admin → perm check → deny
- Remove username-based permission bypass entirely
- Add RBAC permission unit tests
```
