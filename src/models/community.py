from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.db.database import Base

class Post(Base):
    """帖子模型"""
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String, nullable=False) # e.g., 'interview_review', 'real_questions', 'experience'
    status = Column(String, default="published") # e.g., 'draft', 'published', 'hidden'
    ai_analysis_status = Column(String, default="pending") # e.g., 'pending', 'processing', 'completed', 'failed'
    ai_review_content = Column(Text, nullable=True) # LLM 自动点评内容
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    author = relationship("User", backref="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("PostLike", back_populates="post", cascade="all, delete-orphan")

class Comment(Base):
    """评论模型"""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    post = relationship("Post", back_populates="comments")
    author = relationship("User", backref="comments")
    parent = relationship("Comment", remote_side=[id], backref="replies")

class PostLike(Base):
    """点赞模型"""
    __tablename__ = "post_likes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    post = relationship("Post", back_populates="likes")
    user = relationship("User", backref="likes")

class UserFollow(Base):
    """用户关注模型"""
    __tablename__ = "user_follows"

    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    followed_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    follower = relationship("User", foreign_keys=[follower_id], backref="following")
    followed = relationship("User", foreign_keys=[followed_id], backref="followers")
