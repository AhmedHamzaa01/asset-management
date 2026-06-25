from sqlalchemy import JSON, DateTime, Enum, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.sql import func
from sqlalchemy import Column

from app.domain.enums import AssetStatus, AssetType
from app.infrastructure.database import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    type = Column(Enum(AssetType), nullable=False)
    value = Column(String(500), nullable=False)
    status = Column(Enum(AssetStatus), default=AssetStatus.ACTIVE, nullable=False)
    first_seen = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    source = Column(String(100), default="import")
    tags = Column(ARRAY(String), default=[])
    extra_data = Column(JSON, default={})
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("type", "value", "organization_id", name="uq_asset_type_value_org"),
    )
