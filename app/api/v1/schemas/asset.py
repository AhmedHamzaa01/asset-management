from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import AssetStatus, AssetType


class AssetBase(BaseModel):
    type: AssetType
    value: str
    source: str = "import"
    tags: list[str] = Field(default_factory=list)
    extra_data: dict[str, Any] = Field(default_factory=dict)


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    status: AssetStatus | None = None
    source: str | None = None
    tags: list[str] | None = None
    extra_data: dict[str, Any] | None = None


class AssetResponse(BaseModel):
    id: int
    type: AssetType
    value: str
    status: AssetStatus
    first_seen: datetime
    last_seen: datetime
    source: str
    tags: list[str]
    extra_data: dict[str, Any]

    model_config = ConfigDict(from_attributes=True)
