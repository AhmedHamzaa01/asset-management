from sqlalchemy import Column, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    __table_args__ = (UniqueConstraint("email", name="uq_user_email"),)
