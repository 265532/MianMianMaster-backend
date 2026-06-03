from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func
from src.models.user import User, UserProfile, SmsVerification
from src.models.business import InterviewSession
from src.models.assessment import UserSkillMastery
from src.models.gamification import UserDailyTask
from src.models.business import KnowledgeGraph
from src.schemas.user import UserProfileUpdate, ChangePasswordRequest, ChangePhoneRequest, InterviewHistoryItem, AbilityDataItem, GameInterviewData
from src.core.security import verify_password, get_password_hash, validate_password_strength
from src.core.exceptions import BusinessException
from typing import List, Optional
from datetime import datetime

def get_user_profile(db: Session, user_id: int) -> User:
    user = db.query(User).options(selectinload(User.profile), selectinload(User.roles)).filter(User.id == user_id).first()
    if not user:
        raise BusinessException(code=404, detail="User not found.")
    
    # Initialize profile if it doesn't exist
    if not user.profile:
        new_profile = UserProfile(user_id=user_id)
        db.add(new_profile)
        db.commit()
        db.refresh(user)
        
    return user

def update_user_profile(db: Session, user_id: int, profile_in: UserProfileUpdate) -> UserProfile:
    user = get_user_profile(db, user_id)
    profile = user.profile
    
    update_data = profile_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
        
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

def change_password(db: Session, user_id: int, request: ChangePasswordRequest) -> str:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise BusinessException(code=404, detail="User not found.")
        
    if not verify_password(request.old_password, user.hashed_password):
        raise BusinessException(code=400, detail="Incorrect old password.")
        
    if not validate_password_strength(request.new_password):
        raise BusinessException(code=400, detail="Password must be at least 8 characters long and contain uppercase, lowercase, digit, and special character.")
        
    user.hashed_password = get_password_hash(request.new_password)
    db.commit()
    return "Password updated successfully."

def change_phone(db: Session, user_id: int, request: ChangePhoneRequest) -> str:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise BusinessException(code=404, detail="User not found.")
        
    # Verify SMS Code
    sms_record = db.query(SmsVerification).filter(
        SmsVerification.phone == request.new_phone,
        SmsVerification.code == request.code,
        SmsVerification.is_used == False,
        SmsVerification.expires_at > datetime.utcnow()
    ).first()
    
    if not sms_record:
        raise BusinessException(code=400, detail="Invalid or expired SMS code.")
        
    # Check if phone already in use by someone else
    existing_user = db.query(User).filter(User.phone == request.new_phone).first()
    if existing_user and existing_user.id != user_id:
        raise BusinessException(code=400, detail="Phone number already registered.")
        
    sms_record.is_used = True
    user.phone = request.new_phone
    db.commit()
    return "Phone number updated successfully."

def get_interview_history(db: Session, user_id: int, skip: int = 0, limit: int = 10) -> List[InterviewSession]:
    """获取用户面试历史"""
    return db.query(InterviewSession).filter(
        InterviewSession.candidate_id == user_id
    ).order_by(InterviewSession.created_at.desc()).offset(skip).limit(limit).all()

def get_ability_data(db: Session, user_id: int) -> List[dict]:
    """获取用户能力数据（技能掌握度）"""
    results = db.query(
        UserSkillMastery,
        KnowledgeGraph.concept_name
    ).join(
        KnowledgeGraph, UserSkillMastery.knowledge_graph_id == KnowledgeGraph.id
    ).filter(
        UserSkillMastery.user_id == user_id
    ).all()

    return [
        {
            "knowledge_graph_id": mastery.knowledge_graph_id,
            "concept_name": concept_name,
            "mastery_level": mastery.mastery_level,
            "last_assessed_at": mastery.last_assessed_at
        }
        for mastery, concept_name in results
    ]

def get_game_interview_data(db: Session, user_id: int) -> GameInterviewData:
    """获取用户游戏化面试数据"""
    # 面试统计
    interview_stats = db.query(
        func.count(InterviewSession.id).label('total'),
        func.count(InterviewSession.id).filter(InterviewSession.status == 'completed').label('completed'),
        func.avg(InterviewSession.score).filter(InterviewSession.status == 'completed').label('avg_score')
    ).filter(InterviewSession.candidate_id == user_id).first()

    # 每日任务统计
    task_stats = db.query(
        func.count(UserDailyTask.id).filter(UserDailyTask.is_completed == True).label('completed_tasks'),
        func.coalesce(func.sum(UserDailyTask.reward_points), 0).label('total_points')
    ).filter(UserDailyTask.user_id == user_id).first()

    # 用户等级
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    level = profile.level if profile else 1

    return GameInterviewData(
        total_interviews=interview_stats.total or 0,
        completed_interviews=interview_stats.completed or 0,
        average_score=round(float(interview_stats.avg_score), 1) if interview_stats.avg_score else None,
        total_tasks_completed=task_stats.completed_tasks or 0,
        total_points=task_stats.total_points or 0,
        level=level
    )
