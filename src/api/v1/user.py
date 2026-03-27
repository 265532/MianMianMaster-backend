from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Any
from src.api.deps import get_db, get_current_active_user
from src.schemas.user import User, UserProfile, UserProfileUpdate, ChangePasswordRequest, ChangePhoneRequest
from src.schemas.system import ResponseModel
from src.services import user_service
from src.models.user import User as UserModel

router = APIRouter()

@router.get("/profile", response_model=ResponseModel[User])
def get_profile(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    user = user_service.get_user_profile(db, current_user.id)
    return ResponseModel(data=user)

@router.put("/profile", response_model=ResponseModel[UserProfile])
def update_profile(
    profile_in: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    profile = user_service.update_user_profile(db, current_user.id, profile_in)
    return ResponseModel(data=profile)

@router.post("/security/change-password", response_model=ResponseModel[str])
def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    message = user_service.change_password(db, current_user.id, request)
    return ResponseModel(data=message)

@router.post("/security/change-phone", response_model=ResponseModel[str])
def change_phone(
    request: ChangePhoneRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    message = user_service.change_phone(db, current_user.id, request)
    return ResponseModel(data=message)
