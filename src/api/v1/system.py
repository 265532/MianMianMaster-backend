from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Any
from src.api.deps import get_db, get_current_active_user, check_permissions
from src.models import system as models
from src.schemas import system as schemas

router = APIRouter()

@router.get("/config", response_model=schemas.ResponseModel[List[schemas.SystemConfig]], dependencies=[Depends(check_permissions("config", "read"))])
def list_system_configs(db: Session = Depends(get_db)) -> Any:
    configs = db.query(models.SystemConfig).all()
    return schemas.ResponseModel(data=configs)

@router.post("/config", response_model=schemas.ResponseModel[schemas.SystemConfig], dependencies=[Depends(check_permissions("config", "create"))])
def create_system_config(obj_in: schemas.SystemConfigCreate, db: Session = Depends(get_db)) -> Any:
    db_obj = models.SystemConfig(**obj_in.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return schemas.ResponseModel(data=db_obj)

@router.get("/audit-log", response_model=schemas.ResponseModel[List[schemas.AuditLog]], dependencies=[Depends(check_permissions("audit_log", "read"))])
def list_audit_logs(db: Session = Depends(get_db)) -> Any:
    logs = db.query(models.AuditLog).order_by(models.AuditLog.created_at.desc()).limit(100).all()
    return schemas.ResponseModel(data=logs)
