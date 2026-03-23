from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from src.api.deps import get_db, get_current_active_user
from src.models import system as models
from src.schemas import system as schemas

router = APIRouter()

@router.get("/config", response_model=List[schemas.SystemConfig])
def list_system_configs(db: Session = Depends(get_db)):
    return db.query(models.SystemConfig).all()

@router.post("/config", response_model=schemas.SystemConfig)
def create_system_config(obj_in: schemas.SystemConfigCreate, db: Session = Depends(get_db)):
    db_obj = models.SystemConfig(**obj_in.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/audit-log", response_model=List[schemas.AuditLog])
def list_audit_logs(db: Session = Depends(get_db)):
    return db.query(models.AuditLog).order_by(models.AuditLog.created_at.desc()).limit(100).all()