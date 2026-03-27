from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Any
from src.api.deps import get_db, get_current_active_user
from src.schemas.assessment import Assessment, AssessmentCreate, AssessmentSubmitRequest, UserAssessmentRecord
from src.schemas.system import ResponseModel
from src.services import assessment_service
from src.models.user import User as UserModel

router = APIRouter()

@router.post("", response_model=ResponseModel[Assessment])
def create_assessment(
    obj_in: AssessmentCreate,
    db: Session = Depends(get_db)
) -> Any:
    assessment = assessment_service.create_assessment(db, obj_in)
    return ResponseModel(data=assessment)

@router.post("/submit", response_model=ResponseModel[UserAssessmentRecord])
def submit_assessment(
    request: AssessmentSubmitRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    record = assessment_service.submit_assessment(db, current_user.id, request)
    return ResponseModel(data=record)
