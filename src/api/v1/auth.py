from typing import Any
from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.schemas.user import (
    Token, UserCreate, User, SmsSendRequest, SmsLoginRequest, 
    PasswordResetRequest, PasswordResetTokenRequest, LoginRequest
)
from src.schemas.system import ResponseModel
from src.api.deps import get_db, get_current_user
from src.models.user import User as UserModel
from src.services.auth_service import auth_service
from src.core.limiter import limiter

router = APIRouter()

@router.post("/swagger-login", include_in_schema=False)
@limiter.limit("10/minute")
def swagger_login(
    request: Request, db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    return auth_service.swagger_login(db, form_data)

@router.post("/login", response_model=ResponseModel[Token])
@limiter.limit("5/minute")
def login_access_token(
    request: Request, login_request: LoginRequest, db: Session = Depends(get_db)
) -> Any:
    token_data = auth_service.login_access_token(db, login_request)
    return ResponseModel(data=token_data)

@router.post("/register", response_model=ResponseModel[User])
@limiter.limit("3/minute")
def register_user(
    request: Request,
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    user_obj = auth_service.register_user(db, user_in)
    return ResponseModel(data=user_obj)

@router.get("/me", response_model=ResponseModel[User])
def read_users_me(
    current_user: UserModel = Depends(get_current_user)
) -> Any:
    return ResponseModel(data=current_user)

@router.post("/sms/send", response_model=ResponseModel[str])
@limiter.limit("1/minute")
def send_sms_code(
    request: Request,
    sms_request: SmsSendRequest,
    db: Session = Depends(get_db)
) -> Any:
    message = auth_service.send_sms_code(db, sms_request)
    return ResponseModel(data=message)

@router.post("/sms/login", response_model=ResponseModel[Token])
def sms_login(
    request: SmsLoginRequest,
    db: Session = Depends(get_db)
) -> Any:
    token_data = auth_service.sms_login(db, request)
    return ResponseModel(data=token_data)

@router.post("/password/reset-token", response_model=ResponseModel[str])
def generate_password_reset_token(
    request: PasswordResetTokenRequest,
    db: Session = Depends(get_db)
) -> Any:
    token = auth_service.generate_password_reset_token(db, request)
    return ResponseModel(data=token)

@router.post("/password/reset", response_model=ResponseModel[str])
def reset_password(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
) -> Any:
    message = auth_service.reset_password(db, request)
    return ResponseModel(data=message)
