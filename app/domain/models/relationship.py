from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.database import Base


class Relationship(Base):
    __tablename__ = "asset_relationships"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    source_asset_id = Column(Integer, nullable=False, index=True)
    target_asset_id = Column(Integer, nullable=False, index=True)
    relationship_type = Column(String(100), nullable=False)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint(
            "source_asset_id",
            "target_asset_id",
            "relationship_type",
            "organization_id",
            name="uq_asset_relationship",
        ),
    )
