from fastapi import APIRouter, status

from app.api.deps import AuthServiceDep
from app.api.v1.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, service: AuthServiceDep) -> RegisterResponse:
    user = service.register(payload.email, payload.password)
    return RegisterResponse(
        id=str(user.id),
        email=user.email,
        organization_id=str(user.organization_id),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, service: AuthServiceDep) -> TokenResponse:
    return service.login(payload.email, payload.password)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, service: AuthServiceDep) -> TokenResponse:
    return service.refresh(payload.refresh_token)