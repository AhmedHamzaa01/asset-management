from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import UnauthorizedError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__truncate_error=False)

# bcrypt silently truncates passwords at 72 bytes; we enforce this explicitly
# to avoid passlib/bcrypt version compatibility errors
_MAX_BCRYPT_BYTES = 72

def _prepare_password(password: str) -> str:
    encoded = password.encode("utf-8")
    return encoded[:_MAX_BCRYPT_BYTES]

def hash_password(password: str) -> str:
    return pwd_context.hash(_prepare_password(password))

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(_prepare_password(plain_password), hashed_password)

def _create_token(
    *,
    subject: str,
    organization_id: str,
    expires_minutes: int,
    token_type: str,
) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "organization_id": organization_id,
        "token_type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(*, subject: str, organization_id: str) -> str:
    return _create_token(
        subject=subject,
        organization_id=organization_id,
        expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        token_type="access",
    )


def create_refresh_token(*, subject: str, organization_id: str) -> str:
    return _create_token(
        subject=subject,
        organization_id=organization_id,
        expires_minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
        token_type="refresh",
    )


def verify_token(token: str, expected_token_type: str | None = None) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as exc:
        raise UnauthorizedError("Invalid authentication token") from exc

    if expected_token_type and payload.get("token_type") != expected_token_type:
        raise UnauthorizedError("Invalid token type")

    if "sub" not in payload or "organization_id" not in payload:
        raise UnauthorizedError("Invalid authentication token payload")

    return payload