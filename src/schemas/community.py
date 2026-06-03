from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PostBase(BaseModel):
    title: str
    content: str
    category: str
    status: Optional[str] = "published"

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None

class PostInDBBase(PostBase):
    id: int
    user_id: int
    ai_analysis_status: str
    ai_review_content: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class PostResponse(PostInDBBase):
    likes_count: int = 0
    comments_count: int = 0

class CommentBase(BaseModel):
    content: str
    parent_id: Optional[int] = None

class CommentCreate(CommentBase):
    post_id: int

class CommentResponse(CommentBase):
    id: int
    post_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
