from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime
import re

class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None
    resource: str
    action: str

class PermissionCreate(PermissionBase):
    pass

class Permission(PermissionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None

class RoleCreate(RoleBase):
    permission_ids: List[int] = []

class Role(RoleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    permissions: List[Permission] = []

    model_config = {"from_attributes": True}

class UserProfileBase(BaseModel):
    avatar_url: Optional[str] = None
    education: Optional[str] = None
    target_position: Optional[str] = None
    work_years: Optional[int] = None

class UserProfileUpdate(UserProfileBase):
    pass

class UserProfile(UserProfileBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class UserBase(BaseModel):
    username: str
    email: EmailStr
    phone: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str
    role_ids: List[int] = []

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    roles: List[Role] = []
    profile: Optional[UserProfile] = None

    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class SmsSendRequest(BaseModel):
    phone: str
    
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if not re.match(r"^1[3-9]\d{9}$", v):
            raise ValueError("Invalid phone number format")
        return v

class SmsLoginRequest(BaseModel):
    phone: str
    code: str

class PasswordResetRequest(BaseModel):
    token: str
    new_password: str

class PasswordResetTokenRequest(BaseModel):
    email: EmailStr

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class ChangePhoneRequest(BaseModel):
    new_phone: str
    code: str
