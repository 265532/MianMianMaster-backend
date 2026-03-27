from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class QuestionBase(BaseModel):
    knowledge_graph_id: Optional[int] = None
    question_type: str
    content: str
    options: List[Dict[str, str]] = []
    correct_answer: Any
    score_weight: float = 1.0

class QuestionCreate(QuestionBase):
    pass

class Question(QuestionBase):
    id: int
    assessment_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AssessmentBase(BaseModel):
    title: str
    description: Optional[str] = None
    job_position_id: Optional[int] = None

class AssessmentCreate(AssessmentBase):
    questions: List[QuestionCreate] = []

class Assessment(AssessmentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    questions: List[Question] = []

    model_config = ConfigDict(from_attributes=True)

class AssessmentSubmitItem(BaseModel):
    question_id: int
    answer: Any

class AssessmentSubmitRequest(BaseModel):
    assessment_id: int
    answers: List[AssessmentSubmitItem]

class UserAssessmentRecord(BaseModel):
    id: int
    user_id: int
    assessment_id: int
    total_score: float
    details: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserSkillMastery(BaseModel):
    id: int
    user_id: int
    knowledge_graph_id: int
    mastery_level: float
    last_assessed_at: datetime

    model_config = ConfigDict(from_attributes=True)
