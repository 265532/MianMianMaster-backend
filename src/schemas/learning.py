from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime

# ================= Course =================
class CourseMaterialBase(BaseModel):
    title: str
    material_type: str = Field(..., description="video, pdf, article")
    url: str
    duration: Optional[int] = 0
    order_num: Optional[int] = 0
    knowledge_graph_id: Optional[int] = None

class CourseMaterialCreate(CourseMaterialBase):
    course_id: int

class CourseMaterialResponse(CourseMaterialBase):
    id: int
    course_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None
    level: Optional[str] = None
    cover_url: Optional[str] = None

class CourseCreate(CourseBase):
    pass

class CourseResponse(CourseBase):
    id: int
    created_at: datetime
    updated_at: datetime
    materials: List[CourseMaterialResponse] = []

    class Config:
        from_attributes = True

# ================= Progress =================
class UserLearningProgressBase(BaseModel):
    progress_percent: float = Field(ge=0.0, le=100.0)
    is_completed: bool = False

class UserLearningProgressUpdate(UserLearningProgressBase):
    pass

class UserLearningProgressResponse(UserLearningProgressBase):
    id: int
    user_id: int
    course_id: int
    material_id: int
    last_accessed_at: datetime

    class Config:
        from_attributes = True

# ================= Question Bank =================
class QuestionCollectionCreate(BaseModel):
    question_id: int
    notes: Optional[str] = None

class QuestionCollectionResponse(BaseModel):
    id: int
    user_id: int
    question_id: int
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class WrongQuestionCreate(BaseModel):
    question_id: int
    wrong_answer: Any

class WrongQuestionResponse(BaseModel):
    id: int
    user_id: int
    question_id: int
    wrong_answer: Any
    answer_count: int
    is_mastered: bool
    last_answered_at: datetime

    class Config:
        from_attributes = True

# ================= Badge =================
class BadgeBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    condition_type: str
    condition_value: Optional[str] = None

class BadgeCreate(BadgeBase):
    pass

class BadgeResponse(BadgeBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class UserBadgeResponse(BaseModel):
    id: int
    user_id: int
    badge_id: int
    awarded_at: datetime
    tx_hash: Optional[str] = None

    class Config:
        from_attributes = True
