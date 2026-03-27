from sqlalchemy.orm import Session, selectinload
from src.models.user import User, UserProfile, SmsVerification
from src.schemas.user import UserProfileUpdate, ChangePasswordRequest, ChangePhoneRequest
from src.core.security import verify_password, get_password_hash, validate_password_strength
from src.core.exceptions import BusinessException
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
