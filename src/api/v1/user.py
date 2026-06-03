from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Any, List
from src.api.deps import get_db, get_current_active_user
from src.schemas.user import User, UserProfile, UserProfileUpdate, ChangePasswordRequest, ChangePhoneRequest, InterviewHistoryItem, AbilityDataItem, GameInterviewData
from src.schemas.system import ResponseModel
from src.services import user_service
from src.models.user import User as UserModel
from src.models.business import InterviewSession

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

@router.get("/interview-history", response_model=ResponseModel[List[InterviewHistoryItem]])
def get_interview_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    """获取用户面试历史"""
    interviews = user_service.get_interview_history(db, current_user.id, skip, limit)
    return ResponseModel(data=interviews)

@router.get("/ability-data", response_model=ResponseModel[List[AbilityDataItem]])
def get_ability_data(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    """获取用户能力数据"""
    ability_data = user_service.get_ability_data(db, current_user.id)
    return ResponseModel(data=ability_data)

@router.get("/game-interview-data", response_model=ResponseModel[GameInterviewData])
def get_game_interview_data(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    """获取用户游戏化面试数据"""
    game_data = user_service.get_game_interview_data(db, current_user.id)
    return ResponseModel(data=game_data)
