from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.db.database import Base

class KnowledgeGraph(Base):
    """知识图谱节点"""
    __tablename__ = "knowledge_graphs"

    id = Column(Integer, primary_key=True, index=True)
    concept_name = Column(String, index=True, nullable=False)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey("knowledge_graphs.id"), nullable=True)
    tags = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    children = relationship("KnowledgeGraph", backref="parent", remote_side=[id])

class InterviewConfig(Base):
    """音视频面试配置"""
    __tablename__ = "interview_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    video_resolution = Column(String, default="1080p")
    audio_codec = Column(String, default="opus")
    enable_recording = Column(Boolean, default=True)
    max_duration_minutes = Column(Integer, default=60)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class AIStrategy(Base):
    """AI策略优化参数"""
    __tablename__ = "ai_strategies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    model_name = Column(String, nullable=False)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=1024)
    system_prompt = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class AgentState(Base):
    """AI Agent状态管理"""
    __tablename__ = "agent_states"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String, unique=True, index=True, nullable=False)
    agent_type = Column(String, nullable=False) # e.g., 'interviewer', 'evaluator'
    status = Column(String, default="idle") # idle, running, error, offline
    current_session_id = Column(String, nullable=True)
    last_heartbeat = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    metadata_info = Column(JSON, default={})

class InterviewSession(Base):
    """面试流程监控"""
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("users.id"))
    config_id = Column(Integer, ForeignKey("interview_configs.id"))
    strategy_id = Column(Integer, ForeignKey("ai_strategies.id"))
    status = Column(String, default="scheduled") # scheduled, in_progress, completed, failed
    score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    candidate = relationship("User", foreign_keys=[candidate_id])
    config = relationship("InterviewConfig")
    strategy = relationship("AIStrategy")