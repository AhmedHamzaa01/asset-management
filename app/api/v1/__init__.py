from fastapi import APIRouter

from app.api.v1.endpoints.assets import router as assets_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.relationships import router as relationships_router

api_router = APIRouter()
api_router.include_router(assets_router, tags=["assets"])
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(relationships_router, tags=["relationships"])
