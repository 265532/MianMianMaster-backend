from sqlalchemy.orm import Session, selectinload
from typing import List
from src.models.user import Role, Permission, User
from src.schemas.user import RoleCreate
from src.core.exceptions import BusinessException
from src.db.redis_client import get_redis

class RoleService:
    @staticmethod
    def list_roles(db: Session) -> List[Role]:
        return db.query(Role).options(selectinload(Role.permissions)).all()

    @staticmethod
    def create_role(db: Session, role_in: RoleCreate) -> Role:
        role = db.query(Role).filter(Role.name == role_in.name).first()
        if role:
            raise BusinessException(code=400, detail="Role already exists.")
        
        new_role = Role(
            name=role_in.name,
            description=role_in.description,
            parent_id=role_in.parent_id
        )
        
        if role_in.permission_ids:
            permissions = db.query(Permission).filter(Permission.id.in_(role_in.permission_ids)).all()
            new_role.permissions = permissions
            
        db.add(new_role)
        db.commit()
        db.refresh(new_role)
        return new_role

    @staticmethod
    def assign_permissions_to_role(db: Session, role_id: int, permission_ids: List[int]) -> Role:
        role = db.query(Role).options(selectinload(Role.permissions)).filter(Role.id == role_id).first()
        if not role:
            raise BusinessException(code=404, detail="Role not found.")
            
        permissions = db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
        role.permissions = permissions
        db.commit()
        db.refresh(role)
        
        # Invalidate cache
        redis_client = get_redis()
        keys = redis_client.keys("user:perms:*")
        if keys:
            redis_client.delete(*keys)
            
        return role

    @staticmethod
    def assign_role_to_user(db: Session, user_id: int, role_ids: List[int]) -> str:
        user = db.query(User).options(selectinload(User.roles)).filter(User.id == user_id).first()
        if not user:
            raise BusinessException(code=404, detail="User not found.")
            
        roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
        user.roles = roles
        db.commit()
        
        # Invalidate cache
        redis_client = get_redis()
        redis_client.delete(f"user:perms:{user.id}")
        
        return "Roles assigned successfully."

    @staticmethod
    def list_permissions(db: Session) -> List[Permission]:
        return db.query(Permission).all()

role_service = RoleService()
