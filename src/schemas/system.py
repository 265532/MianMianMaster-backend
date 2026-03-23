from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

class SystemConfigBase(BaseModel):
    key: str
    value: Dict[str, Any]
    description: Optional[str] = None

class SystemConfigCreate(SystemConfigBase):
    pass

class SystemConfig(SystemConfigBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True

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

    class Config:
        from_attributes = True