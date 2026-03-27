from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from src.api.deps import get_db, get_current_active_user, check_permissions
from src.schemas import business as schemas
from src.schemas.system import ResponseModel
from src.services.business_service import business_service

router = APIRouter()

# Knowledge Graph
@router.get("/knowledge-graph", response_model=ResponseModel[List[schemas.KnowledgeGraph]], dependencies=[Depends(check_permissions("knowledge_graph", "read"))])
def list_knowledge_graph(db: Session = Depends(get_db)):
    data = business_service.list_knowledge_graph(db)
    return ResponseModel(data=data)

@router.post("/knowledge-graph", response_model=ResponseModel[schemas.KnowledgeGraph], dependencies=[Depends(check_permissions("knowledge_graph", "create"))])
def create_knowledge_graph(obj_in: schemas.KnowledgeGraphCreate, db: Session = Depends(get_db)):
    data = business_service.create_knowledge_graph(db, obj_in)
    return ResponseModel(data=data)

# AI Strategy
@router.get("/ai-strategy", response_model=ResponseModel[List[schemas.AIStrategy]], dependencies=[Depends(check_permissions("ai_strategy", "read"))])
def list_ai_strategy(db: Session = Depends(get_db)):
    data = business_service.list_ai_strategy(db)
    return ResponseModel(data=data)

@router.post("/ai-strategy", response_model=ResponseModel[schemas.AIStrategy], dependencies=[Depends(check_permissions("ai_strategy", "create"))])
def create_ai_strategy(obj_in: schemas.AIStrategyCreate, db: Session = Depends(get_db)):
    data = business_service.create_ai_strategy(db, obj_in)
    return ResponseModel(data=data)

# Interview Config
@router.get("/interview-config", response_model=ResponseModel[List[schemas.InterviewConfig]], dependencies=[Depends(check_permissions("interview_config", "read"))])
def list_interview_config(db: Session = Depends(get_db)):
    data = business_service.list_interview_config(db)
    return ResponseModel(data=data)

@router.post("/interview-config", response_model=ResponseModel[schemas.InterviewConfig], dependencies=[Depends(check_permissions("interview_config", "create"))])
def create_interview_config(obj_in: schemas.InterviewConfigCreate, db: Session = Depends(get_db)):
    data = business_service.create_interview_config(db, obj_in)
    return ResponseModel(data=data)

# Interview Session
@router.post("/interview-session", response_model=ResponseModel[schemas.InterviewSession], dependencies=[Depends(check_permissions("interview_session", "create"))])
def create_interview_session(obj_in: schemas.InterviewSessionCreate, db: Session = Depends(get_db)):
    data = business_service.create_interview_session(db, obj_in)
    return ResponseModel(data=data)

@router.get("/interview-session", response_model=ResponseModel[List[schemas.InterviewSession]], dependencies=[Depends(check_permissions("interview_session", "read"))])
def list_interview_session(db: Session = Depends(get_db)):
    data = business_service.list_interview_session(db)
    return ResponseModel(data=data)

# Agent State
@router.get("/agent-state", response_model=ResponseModel[List[schemas.AgentState]], dependencies=[Depends(check_permissions("agent_state", "read"))])
def list_agent_state(db: Session = Depends(get_db)):
    data = business_service.list_agent_state(db)
    return ResponseModel(data=data)
