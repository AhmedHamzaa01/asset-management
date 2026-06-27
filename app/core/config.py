import os
import sys
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Asset Management API")
    API_V1_PREFIX: str = os.getenv("API_V1_PREFIX", "/api/v1")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/assetdb",
    )
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
    REFRESH_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", "10080")
    )


settings = Settings()

if settings.JWT_SECRET_KEY == "change-me":
    print(
        "ERROR: JWT_SECRET_KEY is not set. "
        "Set it in your .env file or environment before starting.",
        file=sys.stderr,
    )
    sys.exit(1)