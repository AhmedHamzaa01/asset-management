from app.api.v1.endpoints.assets import router as assets_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.relationships import router as relationships_router

__all__ = ["assets_router", "auth_router", "relationships_router"]
