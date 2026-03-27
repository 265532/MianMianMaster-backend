from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Any
from src.api.deps import get_db, check_permissions
from src.schemas.user import Role as RoleSchema, RoleCreate, Permission as PermissionSchema
from src.schemas.system import ResponseModel
from src.services.role_service import role_service

router = APIRouter()

@router.get("/roles", response_model=ResponseModel[List[RoleSchema]], dependencies=[Depends(check_permissions("role", "read"))])
def list_roles(db: Session = Depends(get_db)) -> Any:
    roles = role_service.list_roles(db)
    return ResponseModel(data=roles)

@router.post("/roles", response_model=ResponseModel[RoleSchema], dependencies=[Depends(check_permissions("role", "create"))])
def create_role(
    role_in: RoleCreate,
    db: Session = Depends(get_db)
) -> Any:
    new_role = role_service.create_role(db, role_in)
    return ResponseModel(data=new_role)

@router.post("/roles/{role_id}/permissions", response_model=ResponseModel[RoleSchema], dependencies=[Depends(check_permissions("role", "update"))])
def assign_permissions_to_role(
    role_id: int,
    permission_ids: List[int],
    db: Session = Depends(get_db)
) -> Any:
    role = role_service.assign_permissions_to_role(db, role_id, permission_ids)
    return ResponseModel(data=role)

@router.post("/users/{user_id}/roles", response_model=ResponseModel[str], dependencies=[Depends(check_permissions("user", "update"))])
def assign_role_to_user(
    user_id: int,
    role_ids: List[int],
    db: Session = Depends(get_db)
) -> Any:
    message = role_service.assign_role_to_user(db, user_id, role_ids)
    return ResponseModel(data=message)

@router.get("/permissions", response_model=ResponseModel[List[PermissionSchema]], dependencies=[Depends(check_permissions("role", "read"))])
def list_permissions(db: Session = Depends(get_db)) -> Any:
    permissions = role_service.list_permissions(db)
    return ResponseModel(data=permissions)
