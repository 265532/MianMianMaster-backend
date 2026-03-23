from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from src.api.deps import get_db, get_current_active_user
from src.models import business as models
from src.schemas import business as schemas
from src.db.redis_client import get_redis

router = APIRouter()

# Knowledge Graph
@router.get("/knowledge-graph", response_model=List[schemas.KnowledgeGraph])
def list_knowledge_graph(db: Session = Depends(get_db)):
    return db.query(models.KnowledgeGraph).all()

@router.post("/knowledge-graph", response_model=schemas.KnowledgeGraph)
def create_knowledge_graph(obj_in: schemas.KnowledgeGraphCreate, db: Session = Depends(get_db)):
    db_obj = models.KnowledgeGraph(**obj_in.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

# AI Strategy
@router.get("/ai-strategy", response_model=List[schemas.AIStrategy])
def list_ai_strategy(db: Session = Depends(get_db)):
    return db.query(models.AIStrategy).all()

@router.post("/ai-strategy", response_model=schemas.AIStrategy)
def create_ai_strategy(obj_in: schemas.AIStrategyCreate, db: Session = Depends(get_db)):
    db_obj = models.AIStrategy(**obj_in.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

# Interview Config
@router.get("/interview-config", response_model=List[schemas.InterviewConfig])
def list_interview_config(db: Session = Depends(get_db)):
    return db.query(models.InterviewConfig).all()

@router.post("/interview-config", response_model=schemas.InterviewConfig)
def create_interview_config(obj_in: schemas.InterviewConfigCreate, db: Session = Depends(get_db)):
    db_obj = models.InterviewConfig(**obj_in.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

# Interview Session
@router.post("/interview-session", response_model=schemas.InterviewSession)
def create_interview_session(obj_in: schemas.InterviewSessionCreate, db: Session = Depends(get_db)):
    db_obj = models.InterviewSession(**obj_in.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/interview-session", response_model=List[schemas.InterviewSession])
def list_interview_session(db: Session = Depends(get_db)):
    return db.query(models.InterviewSession).all()

# Agent State
@router.get("/agent-state", response_model=List[schemas.AgentState])
def list_agent_state(db: Session = Depends(get_db)):
    return db.query(models.AgentState).all()