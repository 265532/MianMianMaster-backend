from sqlalchemy.orm import Session
from typing import List
from src.models import system as models
from src.schemas import system as schemas

class SystemService:
    @staticmethod
    def list_system_configs(db: Session) -> List[models.SystemConfig]:
        return db.query(models.SystemConfig).all()

    @staticmethod
    def create_system_config(db: Session, obj_in: schemas.SystemConfigCreate) -> models.SystemConfig:
        db_obj = models.SystemConfig(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def list_audit_logs(db: Session) -> List[models.AuditLog]:
        return db.query(models.AuditLog).order_by(models.AuditLog.created_at.desc()).limit(100).all()

system_service = SystemService()
