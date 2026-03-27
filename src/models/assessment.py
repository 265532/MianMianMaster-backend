from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.db.database import Base

class Assessment(Base):
    """测评试卷"""
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text)
    job_position_id = Column(Integer, ForeignKey("job_positions.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    questions = relationship("Question", back_populates="assessment", cascade="all, delete-orphan")

class Question(Base):
    """测评题目"""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=True)
    knowledge_graph_id = Column(Integer, ForeignKey("knowledge_graphs.id", ondelete="SET NULL"), nullable=True)
    question_type = Column(String, nullable=False) # single_choice, multi_choice, text
    content = Column(Text, nullable=False)
    options = Column(JSON, default=[]) # e.g., [{"id": "A", "text": "..."}, ...]
    correct_answer = Column(JSON, nullable=False) # e.g., ["A"] or ["A", "B"] or text
    score_weight = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    assessment = relationship("Assessment", back_populates="questions")

class UserAssessmentRecord(Base):
    """用户测评记录"""
    __tablename__ = "user_assessment_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    total_score = Column(Float, default=0.0)
    details = Column(JSON, default={}) # 用户的每道题回答详情
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class UserSkillMastery(Base):
    """用户技能掌握度"""
    __tablename__ = "user_skill_mastery"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    knowledge_graph_id = Column(Integer, ForeignKey("knowledge_graphs.id", ondelete="CASCADE"), nullable=False)
    mastery_level = Column(Float, default=0.0) # 0.0 - 100.0
    last_assessed_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
