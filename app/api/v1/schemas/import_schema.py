from typing import Any, List
from pydantic import BaseModel, model_validator

from app.api.v1.schemas.asset import AssetCreate
from app.domain.enums import AssetType, AssetStatus


class RawAssetRecord(BaseModel):
    """
    Lenient wrapper used by bulk import.
    Accepts any dict; per-record validation happens inside the service
    so that one bad record never rejects the whole batch.
    """
    type: Any = None
    value: Any = None
    source: str = "import"
    tags: list[str] = []
    extra_data: dict[str, Any] = {}

    def to_asset_create(self) -> AssetCreate:
        """Validate and coerce into a strict AssetCreate, raising on bad data."""
        return AssetCreate(
            type=self.type,
            value=self.value,
            source=self.source,
            tags=self.tags,
            extra_data=self.extra_data,
        )


class BulkImportRequest(BaseModel):
    assets: List[RawAssetRecord]


class ImportResult(BaseModel):
    inserted: int
    updated: int
    failed: int
    errors: list[str] = []