from sqlalchemy.orm import Session
from typing import List
from src.models import business as models
from src.schemas import business as schemas

class BusinessService:
    # Knowledge Graph
    @staticmethod
    def list_knowledge_graph(db: Session) -> List[models.KnowledgeGraph]:
        return db.query(models.KnowledgeGraph).all()

    @staticmethod
    def create_knowledge_graph(db: Session, obj_in: schemas.KnowledgeGraphCreate) -> models.KnowledgeGraph:
        db_obj = models.KnowledgeGraph(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    # AI Strategy
    @staticmethod
    def list_ai_strategy(db: Session) -> List[models.AIStrategy]:
        return db.query(models.AIStrategy).all()

    @staticmethod
    def create_ai_strategy(db: Session, obj_in: schemas.AIStrategyCreate) -> models.AIStrategy:
        db_obj = models.AIStrategy(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    # Interview Config
    @staticmethod
    def list_interview_config(db: Session) -> List[models.InterviewConfig]:
        return db.query(models.InterviewConfig).all()

    @staticmethod
    def create_interview_config(db: Session, obj_in: schemas.InterviewConfigCreate) -> models.InterviewConfig:
        db_obj = models.InterviewConfig(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    # Interview Session
    @staticmethod
    def create_interview_session(db: Session, obj_in: schemas.InterviewSessionCreate) -> models.InterviewSession:
        db_obj = models.InterviewSession(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def list_interview_session(db: Session) -> List[models.InterviewSession]:
        return db.query(models.InterviewSession).all()

    # Agent State
    @staticmethod
    def list_agent_state(db: Session) -> List[models.AgentState]:
        return db.query(models.AgentState).all()

business_service = BusinessService()
