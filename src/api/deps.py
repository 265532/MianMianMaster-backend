from typing import Generator, List, Callable
import json
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session, selectinload
from src.core.config import settings
from src.core import security
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
