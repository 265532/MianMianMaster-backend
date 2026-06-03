from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Any
from src.api.deps import get_db, get_current_active_user
from src.schemas import learning as schemas
from src.schemas.system import ResponseModel
from src.services.learning_service import learning_service
from src.models.user import User as UserModel

router = APIRouter()

# ================= Course & Materials =================

@router.post("/courses", response_model=ResponseModel[schemas.CourseResponse])
def create_course(
    course_in: schemas.CourseCreate,
    db: Session = Depends(get_db)
) -> Any:
    course = learning_service.create_course(db, course_in)
    return ResponseModel(data=course)

@router.get("/courses", response_model=ResponseModel[List[schemas.CourseResponse]])
def get_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Any:
    courses = learning_service.get_courses(db, skip=skip, limit=limit)
    return ResponseModel(data=courses)

@router.post("/materials", response_model=ResponseModel[schemas.CourseMaterialResponse])
def add_material(
    material_in: schemas.CourseMaterialCreate,
    db: Session = Depends(get_db)
) -> Any:
    material = learning_service.add_material_to_course(db, material_in)
    return ResponseModel(data=material)

# ================= Progress =================

@router.post("/progress/update", response_model=ResponseModel[schemas.UserLearningProgressResponse])
def update_progress(
    course_id: int,
    material_id: int,
    progress_in: schemas.UserLearningProgressUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    progress = learning_service.update_learning_progress(
        db, user_id=current_user.id, course_id=course_id, material_id=material_id, progress_in=progress_in
    )
    return ResponseModel(data=progress)

@router.get("/progress/{course_id}", response_model=ResponseModel[List[schemas.UserLearningProgressResponse]])
def get_progress(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    progress = learning_service.get_user_progress(db, user_id=current_user.id, course_id=course_id)
    return ResponseModel(data=progress)

# ================= Question Bank =================

@router.post("/collections", response_model=ResponseModel[schemas.QuestionCollectionResponse])
def add_to_collection(
    collection_in: schemas.QuestionCollectionCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    collection = learning_service.add_to_collection(db, user_id=current_user.id, collection_in=collection_in)
    return ResponseModel(data=collection)

@router.get("/collections", response_model=ResponseModel[List[schemas.QuestionCollectionResponse]])
def get_collections(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    collections = learning_service.get_collections(db, user_id=current_user.id, skip=skip, limit=limit)
    return ResponseModel(data=collections)

@router.post("/wrong-questions", response_model=ResponseModel[schemas.WrongQuestionResponse])
def record_wrong_question(
    wrong_in: schemas.WrongQuestionCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    record = learning_service.record_wrong_question(db, user_id=current_user.id, wrong_in=wrong_in)
    return ResponseModel(data=record)

@router.get("/wrong-questions", response_model=ResponseModel[List[schemas.WrongQuestionResponse]])
def get_wrong_questions(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    records = learning_service.get_wrong_questions(db, user_id=current_user.id, skip=skip, limit=limit)
    return ResponseModel(data=records)

@router.post("/wrong-questions/{question_id}/master", response_model=ResponseModel[schemas.WrongQuestionResponse])
def mark_wrong_question_mastered(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    record = learning_service.mark_wrong_question_mastered(db, user_id=current_user.id, question_id=question_id)
    return ResponseModel(data=record)

# ================= Badges =================

@router.post("/badges", response_model=ResponseModel[schemas.BadgeResponse])
def create_badge(
    badge_in: schemas.BadgeCreate,
    db: Session = Depends(get_db)
) -> Any:
    badge = learning_service.create_badge(db, badge_in)
    return ResponseModel(data=badge)

@router.get("/badges", response_model=ResponseModel[List[schemas.BadgeResponse]])
def get_badges(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Any:
    badges = learning_service.get_badges(db, skip=skip, limit=limit)
    return ResponseModel(data=badges)

@router.post("/badges/award/{badge_id}", response_model=ResponseModel[schemas.UserBadgeResponse])
def award_badge(
    badge_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    user_badge = learning_service.award_badge(db, user_id=current_user.id, badge_id=badge_id)
    return ResponseModel(data=user_badge)

@router.get("/my-badges", response_model=ResponseModel[List[schemas.UserBadgeResponse]])
def get_my_badges(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    badges = learning_service.get_user_badges(db, user_id=current_user.id)
    return ResponseModel(data=badges)
