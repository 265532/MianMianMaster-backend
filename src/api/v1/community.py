from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from src.api.deps import get_db, get_current_user
from src.models.user import User as UserModel
from src.schemas.community import PostCreate, PostUpdate, PostResponse, CommentCreate, CommentResponse
from src.schemas.system import ResponseModel
from src.services.community_service import community_service

router = APIRouter()

@router.post("/posts", response_model=ResponseModel[PostResponse])
def create_post(
    *,
    db: Session = Depends(get_db),
    post_in: PostCreate,
    current_user: UserModel = Depends(get_current_user)
) -> Any:
    post = community_service.create_post(db, current_user.id, post_in)
    return ResponseModel(data=post)

@router.get("/posts/feed", response_model=ResponseModel[List[PostResponse]])
def get_feed(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None
) -> Any:
    posts = community_service.get_feed(db, skip=skip, limit=limit, keyword=keyword)
    return ResponseModel(data=posts)

@router.get("/posts/{post_id}", response_model=ResponseModel[PostResponse])
def get_post(
    post_id: int,
    db: Session = Depends(get_db)
) -> Any:
    post = community_service.get_post(db, post_id)
    return ResponseModel(data=post)

@router.post("/posts/{post_id}/comments", response_model=ResponseModel[CommentResponse])
def create_comment(
    *,
    db: Session = Depends(get_db),
    post_id: int,
    comment_in: CommentCreate,
    current_user: UserModel = Depends(get_current_user)
) -> Any:
    comment_in.post_id = post_id
    comment = community_service.create_comment(db, current_user.id, comment_in)
    return ResponseModel(data=comment)

@router.post("/posts/{post_id}/like", response_model=ResponseModel[bool])
def toggle_like(
    *,
    db: Session = Depends(get_db),
    post_id: int,
    current_user: UserModel = Depends(get_current_user)
) -> Any:
    status = community_service.toggle_like(db, current_user.id, post_id)
    return ResponseModel(data=status, message="Liked" if status else "Unliked")

@router.post("/users/{user_id}/follow", response_model=ResponseModel[bool])
def toggle_follow(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    current_user: UserModel = Depends(get_current_user)
) -> Any:
    status = community_service.toggle_follow(db, current_user.id, user_id)
    return ResponseModel(data=status, message="Followed" if status else "Unfollowed")

@router.post("/posts/{post_id}/ai-review", response_model=ResponseModel[str])
def trigger_ai_review(
    *,
    db: Session = Depends(get_db),
    post_id: int,
    current_user: UserModel = Depends(get_current_user)
) -> Any:
    # Future extension for LLM
    message = community_service.trigger_ai_review(db, post_id)
    return ResponseModel(data=message)
