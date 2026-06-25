from uuid import UUID

from app.api.v1.schemas.auth import TokenResponse
from app.core.exceptions import UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    verify_token,
)
from app.domain.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    def login(self, email: str, password: str) -> TokenResponse:
        user = self.user_repository.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid credentials")
        return self._issue_tokens(user)

    def refresh(self, refresh_token: str) -> TokenResponse:
        payload = verify_token(refresh_token, expected_token_type="refresh")
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedError("Invalid refresh token")

        user = self.user_repository.get_by_id(UUID(user_id))
        if not user:
            raise UnauthorizedError("User not found")
        return self._issue_tokens(user)

    def _issue_tokens(self, user: User) -> TokenResponse:
        access_token = create_access_token(
            subject=str(user.id),
            organization_id=str(user.organization_id),
        )
        refresh_token = create_refresh_token(
            subject=str(user.id),
            organization_id=str(user.organization_id),
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    def register(self, email: str, password: str) -> User:
        from uuid import uuid4
        from app.core.exceptions import ConflictError
        from app.core.security import hash_password

        if self.user_repository.exists_by_email(email):
            raise ConflictError("Email already registered")

        user = User(
            id=uuid4(),
            email=email,
            hashed_password=hash_password(password),
            organization_id=uuid4(),
        )
        return self.user_repository.create(user)