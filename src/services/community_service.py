from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from src.models.community import Post, Comment, PostLike, UserFollow
from src.schemas.community import PostCreate, PostUpdate, CommentCreate
from src.core.exceptions import BusinessException

class CommunityService:
    def create_post(self, db: Session, user_id: int, post_in: PostCreate) -> Post:
        db_post = Post(**post_in.model_dump(), user_id=user_id)
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
        return db_post

    def get_post(self, db: Session, post_id: int) -> Post:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise BusinessException(code=404, detail="Post not found")
        return post

    def get_feed(self, db: Session, skip: int = 0, limit: int = 10, keyword: Optional[str] = None):
        query = db.query(Post).filter(Post.status == "published")
        if keyword:
            query = query.filter(or_(
                Post.title.ilike(f"%{keyword}%"),
                Post.content.ilike(f"%{keyword}%")
            ))
        return query.order_by(Post.created_at.desc()).offset(skip).limit(limit).all()

    def update_post(self, db: Session, user_id: int, post_id: int, post_in: PostUpdate) -> Post:
        post = self.get_post(db, post_id)
        if post.user_id != user_id:
            raise BusinessException(code=403, detail="Not authorized to update this post")
        
        update_data = post_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(post, field, value)
            
        db.commit()
        db.refresh(post)
        return post

    def delete_post(self, db: Session, user_id: int, post_id: int):
        post = self.get_post(db, post_id)
        if post.user_id != user_id:
            raise BusinessException(code=403, detail="Not authorized to delete this post")
        
        db.delete(post)
        db.commit()
        return True

    def create_comment(self, db: Session, user_id: int, comment_in: CommentCreate) -> Comment:
        # verify post exists
        self.get_post(db, comment_in.post_id)
        
        if comment_in.parent_id:
            parent = db.query(Comment).filter(Comment.id == comment_in.parent_id).first()
            if not parent:
                raise BusinessException(code=404, detail="Parent comment not found")
                
        db_comment = Comment(**comment_in.model_dump(), user_id=user_id)
        db.add(db_comment)
        db.commit()
        db.refresh(db_comment)
        return db_comment

    def toggle_like(self, db: Session, user_id: int, post_id: int) -> bool:
        self.get_post(db, post_id)
        
        existing_like = db.query(PostLike).filter(
            PostLike.post_id == post_id,
            PostLike.user_id == user_id
        ).first()
        
        if existing_like:
            db.delete(existing_like)
            db.commit()
            return False # unliked
        else:
            new_like = PostLike(post_id=post_id, user_id=user_id)
            db.add(new_like)
            db.commit()
            return True # liked

    def toggle_follow(self, db: Session, follower_id: int, followed_id: int) -> bool:
        if follower_id == followed_id:
            raise BusinessException(code=400, detail="Cannot follow yourself")
            
        existing_follow = db.query(UserFollow).filter(
            UserFollow.follower_id == follower_id,
            UserFollow.followed_id == followed_id
        ).first()
        
        if existing_follow:
            db.delete(existing_follow)
            db.commit()
            return False # unfollowed
        else:
            new_follow = UserFollow(follower_id=follower_id, followed_id=followed_id)
            db.add(new_follow)
            db.commit()
            return True # followed

    def trigger_ai_review(self, db: Session, post_id: int) -> str:
        post = self.get_post(db, post_id)
        post.ai_analysis_status = "processing"
        db.commit()
        # In actual implementation, send message to queue
        return "AI review triggered"

community_service = CommunityService()
