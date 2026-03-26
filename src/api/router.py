from fastapi import APIRouter
from src.api.v1 import auth, business, system, role

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(business.router, prefix="/business", tags=["business"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(role.router, prefix="/rbac", tags=["rbac"])