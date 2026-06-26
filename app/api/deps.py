from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.core.security import verify_token
from app.domain.models.user import User
from app.infrastructure.database import get_db
from app.repositories.asset_repository import AssetRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.repositories.user_repository import UserRepository
from app.services.asset_service import AssetService
from app.services.auth_service import AuthService
from app.services.relationship_service import RelationshipService

bearer_scheme = HTTPBearer(auto_error=False)


def get_asset_service(
    db: Session = Depends(get_db),
) -> AssetService:

    return AssetService(
        repository=AssetRepository(db),
        relationship_repository=RelationshipRepository(db),
    )

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db))


def get_relationship_service(db: Session = Depends(get_db)) -> RelationshipService:
    return RelationshipService(
        relationship_repository=RelationshipRepository(db),
        asset_repository=AssetRepository(db),
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise UnauthorizedError("Authentication required")

    payload = verify_token(credentials.credentials, expected_token_type="access")
    user_id = payload.get("sub")

    user = UserRepository(db).get_by_id(UUID(user_id)) if user_id else None
    if not user:
        raise UnauthorizedError("Invalid user")

    if str(user.organization_id) != str(payload.get("organization_id")):
        raise UnauthorizedError("Invalid token scope")

    return user


DBSessionDep = Annotated[Session, Depends(get_db)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
AssetServiceDep = Annotated[AssetService, Depends(get_asset_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
RelationshipServiceDep = Annotated[RelationshipService, Depends(get_relationship_service)]
