from fastapi import APIRouter
from src.api.v1 import auth, business, system, role, user, notification, job, assessment, learning, community

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(user.router, prefix="/user", tags=["user"])
api_router.include_router(notification.router, prefix="/notifications", tags=["notification"])
api_router.include_router(business.router, prefix="/business", tags=["business"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(role.router, prefix="/rbac", tags=["rbac"])
api_router.include_router(job.router, prefix="/jobs", tags=["job"])
api_router.include_router(assessment.router, prefix="/assessments", tags=["assessment"])
api_router.include_router(learning.router, prefix="/learning", tags=["learning"])
api_router.include_router(community.router, prefix="/community", tags=["community"])