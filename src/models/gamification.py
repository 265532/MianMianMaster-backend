from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Date, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.db.database import Base

class UserDailyTask(Base):
    __tablename__ = "user_daily_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    task_type = Column(String, nullable=False) # e.g., 'login', 'study', 'assessment'
    task_date = Column(Date, nullable=False)
    is_completed = Column(Boolean, default=False)
    reward_points = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'task_type', 'task_date', name='uq_user_task_date'),
    )
    
    user = relationship("User", backref="daily_tasks")
