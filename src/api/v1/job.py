from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Any, Dict
from src.api.deps import get_db, get_current_active_user
from src.schemas.business import JobPosition, JobPositionCreate
from src.schemas.system import ResponseModel
from src.services import job_service
from src.models.user import User as UserModel

router = APIRouter()

@router.post("", response_model=ResponseModel[JobPosition])
def create_job_position(
    obj_in: JobPositionCreate,
    db: Session = Depends(get_db)
) -> Any:
    job = job_service.create_job_position(db, obj_in)
    return ResponseModel(data=job)

@router.get("", response_model=ResponseModel[List[JobPosition]])
def list_job_positions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> Any:
    jobs = job_service.get_job_positions(db, skip, limit)
    return ResponseModel(data=jobs)

@router.get("/{job_id}/skill-tree", response_model=ResponseModel[Dict[str, Any]])
def get_skill_tree(
    job_id: int,
    db: Session = Depends(get_db)
) -> Any:
    tree = job_service.get_job_skill_tree(db, job_id)
    return ResponseModel(data=tree)

@router.get("/{job_id}/match", response_model=ResponseModel[float])
def get_job_match(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    match_score = job_service.calculate_job_match(db, current_user.id, job_id)
    return ResponseModel(data=match_score)
