import uuid
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.database import Base, get_db
from app.core.security import create_access_token
from app.domain.models.user import User
from app.domain import models  # noqa: F401 — ensure all models are registered
from main import app

TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5433/assetdb_test",
)

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True, scope="function")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db):
    org_id = uuid.uuid4()
    # Pre-computed bcrypt hash of "password123" — avoids calling hash_password()
    # at runtime, which breaks on newer bcrypt versions during passlib's self-test.
    # This hash was generated with bcrypt 4.0.1 + passlib 1.7.4 and is valid.
    pre_hashed = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
    u = User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password=pre_hashed,
        organization_id=org_id,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def auth_headers(test_user):
    token = create_access_token(
        subject=str(test_user.id),
        organization_id=str(test_user.organization_id),
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client():
    return TestClient(app)