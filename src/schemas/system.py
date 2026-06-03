from pydantic import BaseModel
from typing import Dict, Any, Optional, TypeVar, Generic
from datetime import datetime

T = TypeVar("T")

class ResponseModel(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: Optional[T] = None

class SystemConfigBase(BaseModel):
    key: str
    value: Dict[str, Any]
    description: Optional[str] = None

class SystemConfigCreate(SystemConfigBase):
    pass

class SystemConfig(SystemConfigBase):
    id: int
    updated_at: datetime

    model_config = {"from_attributes": True}

class AuditLogBase(BaseModel):
    user_id: Optional[int] = None
    action: str
    resource: str
    ip_address: Optional[str] = None
    details: Dict[str, Any] = {}

class AuditLogCreate(AuditLogBase):
    pass

class AuditLog(AuditLogBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}