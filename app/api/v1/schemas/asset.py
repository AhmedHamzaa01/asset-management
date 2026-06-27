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
# fields allowed via PUT /assets/{id}.
#     `status` is intentionally excluded — use PATCH /assets/{id}/stale
#     or DELETE /assets/{id} for lifecycle transitions.    
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
    certificate_status: str | None = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        data = super().model_validate(obj, *args, **kwargs)

        if hasattr(obj, "extra_data"):
            data.certificate_status = (
                obj.extra_data or {}
            ).get("certificate_status")

        return data

class PaginatedAssetResponse(BaseModel):
    """Paginated wrapper returned by GET /assets/."""
    items: list[AssetResponse]
    total: int
    skip: int
    limit: int