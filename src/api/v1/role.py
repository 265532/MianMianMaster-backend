from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from typing import List, Any
from src.api.deps import get_db, check_permissions
from src.models.user import Role, Permission, User
from src.schemas.user import Role as RoleSchema, RoleCreate, Permission as PermissionSchema, PermissionCreate
from src.schemas.system import ResponseModel
from src.core.exceptions import BusinessException
from src.db.redis_client import get_redis

router = APIRouter()

@router.get("/roles", response_model=ResponseModel[List[RoleSchema]], dependencies=[Depends(check_permissions("role", "read"))])
def list_roles(db: Session = Depends(get_db)) -> Any:
    roles = db.query(Role).options(selectinload(Role.permissions)).all()
    return ResponseModel(data=roles)

@router.post("/roles", response_model=ResponseModel[RoleSchema], dependencies=[Depends(check_permissions("role", "create"))])
def create_role(
    role_in: RoleCreate,
    db: Session = Depends(get_db)
) -> Any:
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
    return ResponseModel(data=new_role)

@router.post("/roles/{role_id}/permissions", response_model=ResponseModel[RoleSchema], dependencies=[Depends(check_permissions("role", "update"))])
def assign_permissions_to_role(
    role_id: int,
    permission_ids: List[int],
    db: Session = Depends(get_db)
) -> Any:
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
        
    return ResponseModel(data=role)

@router.post("/users/{user_id}/roles", response_model=ResponseModel[str], dependencies=[Depends(check_permissions("user", "update"))])
def assign_role_to_user(
    user_id: int,
    role_ids: List[int],
    db: Session = Depends(get_db)
) -> Any:
    user = db.query(User).options(selectinload(User.roles)).filter(User.id == user_id).first()
    if not user:
        raise BusinessException(code=404, detail="User not found.")
        
    roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
    user.roles = roles
    db.commit()
    
    # Invalidate cache
    redis_client = get_redis()
    redis_client.delete(f"user:perms:{user.id}")
    
    return ResponseModel(data="Roles assigned successfully.")

@router.get("/permissions", response_model=ResponseModel[List[PermissionSchema]], dependencies=[Depends(check_permissions("role", "read"))])
def list_permissions(db: Session = Depends(get_db)) -> Any:
    permissions = db.query(Permission).all()
    return ResponseModel(data=permissions)
