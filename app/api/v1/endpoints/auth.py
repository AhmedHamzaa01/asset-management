from fastapi import APIRouter

from app.api.deps import AuthServiceDep
from app.api.v1.schemas.auth import LoginRequest, RefreshRequest, TokenResponse

router = APIRouter(prefix="/auth")


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, service: AuthServiceDep) -> TokenResponse:
    return service.login(payload.email, payload.password)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, service: AuthServiceDep) -> TokenResponse:
    return service.refresh(payload.refresh_token)
