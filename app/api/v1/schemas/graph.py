from pydantic import BaseModel
from typing import List

from app.api.v1.schemas import AssetResponse


class AssetGraphResponse(BaseModel):
    asset: AssetResponse
    related_assets: List[AssetResponse]