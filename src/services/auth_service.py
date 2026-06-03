from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
import secrets
import hashlib
import random
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from src.core import security
from src.core.config import settings
from src.core.exceptions import BusinessException
from src.models.user import User as UserModel, SmsVerification, Role
from src.schemas.user import (
    UserCreate, SmsSendRequest, SmsLoginRequest, PasswordResetRequest,
    PasswordResetTokenRequest, LoginRequest, RefreshTokenRequest
)
from src.db.redis_client import get_redis

LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 900
LOGIN_FAILED_COUNT_TTL = 900

SMS_DAILY_LIMIT = 10
SMS_IP_DAILY_LIMIT = 20
SMS_VERIFY_MAX_ATTEMPTS = 5

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
    def _check_login_lockout(identifier: str, id_type: str = "user") -> None:
        redis_client = get_redis()
        lock_key = f"login:locked:{id_type}:{identifier}"
        if redis_client.exists(lock_key):
            ttl = redis_client.ttl(lock_key)
            remaining_minutes = max(1, ttl // 60)
            raise BusinessException(
                code=423,
                detail=f"Account locked due to too many failed attempts. Try again in {remaining_minutes} minutes."
            )

    @staticmethod
    def _record_login_failure(identifier: str, id_type: str = "user") -> int:
        redis_client = get_redis()
        count_key = f"login:failed:{id_type}:{identifier}"
        lock_key = f"login:locked:{id_type}:{identifier}"

        count = redis_client.incr(count_key)
        if count == 1:
            redis_client.expire(count_key, LOGIN_FAILED_COUNT_TTL)

        if count >= LOGIN_MAX_ATTEMPTS:
            redis_client.setex(lock_key, LOGIN_LOCKOUT_SECONDS, "1")
            redis_client.delete(count_key)
            raise BusinessException(
                code=423,
                detail=f"Account locked due to too many failed attempts. Try again in {LOGIN_LOCKOUT_SECONDS // 60} minutes."
            )

        remaining = LOGIN_MAX_ATTEMPTS - count
        return remaining

    @staticmethod
    def _clear_login_failures(identifier: str, id_type: str = "user") -> None:
        redis_client = get_redis()
        count_key = f"login:failed:{id_type}:{identifier}"
        redis_client.delete(count_key)

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
    def swagger_login(db: Session, form_data: OAuth2PasswordRequestForm, client_ip: Optional[str] = None) -> Dict[str, Any]:
        AuthService._check_login_lockout(form_data.username, "user")
        if client_ip:
            AuthService._check_login_lockout(client_ip, "ip")

        user = db.query(UserModel).filter(UserModel.username == form_data.username).first()
        if not user or not security.verify_password(form_data.password, user.hashed_password):
            remaining = AuthService._record_login_failure(form_data.username, "user")
            if client_ip:
                AuthService._record_login_failure(client_ip, "ip")
            raise BusinessException(
                code=401,
                detail=f"Incorrect username or password. {remaining} attempts remaining."
            )
        elif not user.is_active:
            raise BusinessException(code=400, detail="Inactive user")

        AuthService._clear_login_failures(form_data.username, "user")
        if client_ip:
            AuthService._clear_login_failures(client_ip, "ip")

        return AuthService._build_token_pair(user)

    @staticmethod
    def login_access_token(db: Session, request: LoginRequest, client_ip: Optional[str] = None) -> Dict[str, Any]:
        AuthService._check_login_lockout(request.username, "user")
        if client_ip:
            AuthService._check_login_lockout(client_ip, "ip")

        user = db.query(UserModel).filter(UserModel.username == request.username).first()
        if not user or not security.verify_password(request.password, user.hashed_password):
            remaining = AuthService._record_login_failure(request.username, "user")
            if client_ip:
                AuthService._record_login_failure(client_ip, "ip")
            raise BusinessException(
                code=401,
                detail=f"Incorrect username or password. {remaining} attempts remaining."
            )
        elif not user.is_active:
            raise BusinessException(code=400, detail="Inactive user")

        AuthService._clear_login_failures(request.username, "user")
        if client_ip:
            AuthService._clear_login_failures(client_ip, "ip")

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
    def unlock_user(username: str) -> str:
        redis_client = get_redis()
        redis_client.delete(f"login:locked:user:{username}")
        redis_client.delete(f"login:failed:user:{username}")
        return f"User '{username}' unlocked successfully."

    @staticmethod
    def register_user(db: Session, user_in: UserCreate) -> UserModel:
        user = db.query(UserModel).filter(UserModel.username == user_in.username).first()
        if user:
            raise BusinessException(code=400, detail="The user with this username already exists.")

        user_email = db.query(UserModel).filter(UserModel.email == user_in.email).first()
        if user_email:
            raise BusinessException(code=400, detail="The user with this email already exists.")

        if user_in.phone:
            user_phone = db.query(UserModel).filter(UserModel.phone == user_in.phone).first()
            if user_phone:
                raise BusinessException(code=400, detail="The user with this phone number already exists.")

        if not security.validate_password_strength(user_in.password):
            raise BusinessException(code=400, detail="Password must be at least 8 characters long and contain uppercase, lowercase, digit, and special character.")

        user_obj = UserModel(
            email=user_in.email,
            username=user_in.username,
            hashed_password=security.get_password_hash(user_in.password),
            phone=user_in.phone,
            is_active=user_in.is_active,
        )

        if user_in.role_ids:
            roles = db.query(Role).filter(Role.id.in_(user_in.role_ids)).all()
            user_obj.roles = roles

        db.add(user_obj)
        db.commit()
        db.refresh(user_obj)
        return user_obj

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

        redis_client.setex(cooldown_key, 300, "1")

        return token

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

auth_service = AuthService()
