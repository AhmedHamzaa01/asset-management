from typing import List
from pydantic import BaseModel

from app.api.v1.schemas.asset import AssetCreate


class BulkImportRequest(BaseModel):
    assets: List[AssetCreate]

class ImportResult(BaseModel):
    inserted: int
    updated: int
    failed: int
    errors: list[str] = []