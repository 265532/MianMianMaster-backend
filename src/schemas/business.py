from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class KnowledgeGraphBase(BaseModel):
    concept_name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    tags: List[str] = []

class KnowledgeGraphCreate(KnowledgeGraphBase):
    pass

class KnowledgeGraph(KnowledgeGraphBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class InterviewConfigBase(BaseModel):
    name: str
    video_resolution: str = "1080p"
    audio_codec: str = "opus"
    enable_recording: bool = True
    max_duration_minutes: int = 60

class InterviewConfigCreate(InterviewConfigBase):
    pass

class InterviewConfig(InterviewConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AIStrategyBase(BaseModel):
    name: str
    model_name: str
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = 1024
    system_prompt: str
    is_active: bool = True

class AIStrategyCreate(AIStrategyBase):
    pass

class AIStrategy(AIStrategyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AgentStateUpdate(BaseModel):
    status: str
    current_session_id: Optional[str] = None
    metadata_info: Dict[str, Any] = {}

class AgentState(AgentStateUpdate):
    id: int
    agent_id: str
    agent_type: str
    last_heartbeat: datetime

    class Config:
        from_attributes = True

class InterviewSessionBase(BaseModel):
    candidate_id: int
    config_id: int
    strategy_id: int
    status: str = "scheduled"

class InterviewSessionCreate(InterviewSessionBase):
    pass

class InterviewSession(InterviewSessionBase):
    id: int
    score: Optional[float] = None
    feedback: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True