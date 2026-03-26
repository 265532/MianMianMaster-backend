from datetime import datetime, timedelta
from typing import Any
import random
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.core import security
from src.core.config import settings
from src.core.exceptions import BusinessException
from src.schemas.user import (
    Token, UserCreate, User, SmsSendRequest, SmsLoginRequest, 
    PasswordResetRequest, PasswordResetTokenRequest, LoginRequest
)
from src.schemas.system import ResponseModel
from src.api.deps import get_db, get_current_user
from src.models.user import User as UserModel, SmsVerification
from src.db.redis_client import get_redis

router = APIRouter()

@router.post("/swagger-login", include_in_schema=False)
def swagger_login(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    user = db.query(UserModel).filter(UserModel.username == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.username, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/login", response_model=ResponseModel[Token])
def login_access_token(
    request: LoginRequest, db: Session = Depends(get_db)
) -> Any:
    user = db.query(UserModel).filter(UserModel.username == request.username).first()
    if not user or not security.verify_password(request.password, user.hashed_password):
        raise BusinessException(code=400, detail="Incorrect username or password")
    elif not user.is_active:
        raise BusinessException(code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return ResponseModel(data={
        "access_token": security.create_access_token(
            user.username, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    })

@router.post("/register", response_model=ResponseModel[User])
def register_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
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
    
    from src.models.user import Role
    if user_in.role_ids:
        roles = db.query(Role).filter(Role.id.in_(user_in.role_ids)).all()
        user_obj.roles = roles

    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    return ResponseModel(data=user_obj)

@router.get("/me", response_model=ResponseModel[User])
def read_users_me(
    current_user: UserModel = Depends(get_current_user)
) -> Any:
    return ResponseModel(data=current_user)

@router.post("/sms/send", response_model=ResponseModel[str])
def send_sms_code(
    request: SmsSendRequest,
    db: Session = Depends(get_db)
) -> Any:
    redis_client = get_redis()
    cooldown_key = f"sms:cooldown:{request.phone}"
    if redis_client.get(cooldown_key):
        raise BusinessException(code=400, detail="Please wait 60 seconds before sending another SMS.")
    
    code = f"{random.randint(100000, 999999)}"
    
    # In a real app, send the SMS here via a 3rd party service
    
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    sms_record = SmsVerification(
        phone=request.phone,
        code=code,
        expires_at=expires_at
    )
    db.add(sms_record)
    db.commit()
    
    redis_client.setex(cooldown_key, 60, "1")
    return ResponseModel(data="SMS sent successfully (simulated)")

@router.post("/sms/login", response_model=ResponseModel[Token])
def sms_login(
    request: SmsLoginRequest,
    db: Session = Depends(get_db)
) -> Any:
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
        # Auto register or throw error? Let's say we throw error for now
        raise BusinessException(code=404, detail="User with this phone number not found.")
    
    if not user.is_active:
        raise BusinessException(code=400, detail="Inactive user")
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = {
        "access_token": security.create_access_token(
            user.username, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }
    return ResponseModel(data=token)

@router.post("/password/reset-token", response_model=ResponseModel[str])
def generate_password_reset_token(
    request: PasswordResetTokenRequest,
    db: Session = Depends(get_db)
) -> Any:
    user = db.query(UserModel).filter(UserModel.email == request.email).first()
    if not user:
        raise BusinessException(code=404, detail="User not found.")
    
    token = security.create_password_reset_token(email=user.email)
    # In a real app, send an email with the token
    return ResponseModel(data=token) # Returning token for testing purposes

@router.post("/password/reset", response_model=ResponseModel[str])
def reset_password(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
) -> Any:
    email = security.verify_password_reset_token(request.token)
    if not email:
        raise BusinessException(code=400, detail="Invalid or expired reset token.")
    
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user:
        raise BusinessException(code=404, detail="User not found.")
        
    if not security.validate_password_strength(request.new_password):
        raise BusinessException(code=400, detail="Password must be at least 8 characters long and contain uppercase, lowercase, digit, and special character.")
        
    user.hashed_password = security.get_password_hash(request.new_password)
    db.commit()
    return ResponseModel(data="Password reset successfully.")