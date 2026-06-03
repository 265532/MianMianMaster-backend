from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.db.database import Base

class Course(Base):
    """课程模型"""
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text)
    level = Column(String) # e.g., beginner, intermediate, advanced
    cover_url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    materials = relationship("CourseMaterial", back_populates="course", cascade="all, delete-orphan")


class CourseMaterial(Base):
    """课程资料模型"""
    __tablename__ = "course_materials"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    knowledge_graph_id = Column(Integer, ForeignKey("knowledge_graphs.id", ondelete="SET NULL"), nullable=True)
    title = Column(String, nullable=False)
    material_type = Column(String, nullable=False) # video, pdf, article
    url = Column(String, nullable=False)
    duration = Column(Integer, default=0) # 预计时长（分钟）
    order_num = Column(Integer, default=0) # 排序
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    course = relationship("Course", back_populates="materials")


class UserLearningProgress(Base):
    """用户学习进度"""
    __tablename__ = "user_learning_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    material_id = Column(Integer, ForeignKey("course_materials.id", ondelete="CASCADE"), nullable=False)
    progress_percent = Column(Float, default=0.0) # 0.0 - 100.0
    is_completed = Column(Boolean, default=False)
    last_accessed_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class UserQuestionCollection(Base):
    """用户题目收藏夹"""
    __tablename__ = "user_question_collections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    notes = Column(Text) # 个人笔记
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserWrongQuestion(Base):
    """用户错题本"""
    __tablename__ = "user_wrong_questions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    wrong_answer = Column(JSON) # 用户的错误答案
    answer_count = Column(Integer, default=1) # 答错次数
    is_mastered = Column(Boolean, default=False) # 是否已掌握
    last_answered_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Badge(Base):
    """徽章模型"""
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    icon_url = Column(String)
    condition_type = Column(String, nullable=False) # 达成条件类型，例如 'course_completed', 'score_reached'
    condition_value = Column(String) # 条件值，例如课程 ID 或 分数阈值
    ai_prompt_override = Column(Text) # 为未来游戏通关式面试预留的人设覆盖
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserBadge(Base):
    """用户徽章关联"""
    __tablename__ = "user_badges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    badge_id = Column(Integer, ForeignKey("badges.id", ondelete="CASCADE"), nullable=False)
    awarded_at = Column(DateTime(timezone=True), server_default=func.now())
    tx_hash = Column(String) # 预留区块链存证扩展
