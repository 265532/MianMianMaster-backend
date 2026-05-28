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
    jti = str(uuid4())
    to_encode = {"exp": expire, "sub": email, "type": "reset", "jti": jti}
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

def mark_reset_token_used(jti: str) -> None:
    redis_client = get_redis()
    redis_key = f"pwd_reset:used:{jti}"
    redis_client.setex(redis_key, 900, "1")

def is_reset_token_used(jti: str) -> bool:
    redis_client = get_redis()
    redis_key = f"pwd_reset:used:{jti}"
    return redis_client.exists(redis_key) > 0
