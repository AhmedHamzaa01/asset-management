from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.domain.models.asset import Asset
from app.domain.enums import AssetStatus, AssetType

class AssetRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, asset: Asset) -> Asset:
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def save(self, asset: Asset) -> Asset:
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def get_by_id(self, asset_id: int, organization_id: int) -> Optional[Asset]:
        return self.db.query(Asset).filter(
            Asset.id == asset_id,
            Asset.organization_id == organization_id
        ).first()

    def get_by_type_value(self, asset_type: AssetType, value: str, organization_id: int) -> Optional[Asset]:
        return self.db.query(Asset).filter(
            Asset.type == asset_type,
            Asset.value == value,
            Asset.organization_id == organization_id
        ).first()

    def list_assets(self, organization_id: int, skip: int = 0, limit: int = 100,
                    asset_type: Optional[AssetType] = None,
                    status: Optional[AssetStatus] = None,
                    tag: Optional[str] = None,
                    search: Optional[str] = None) -> List[Asset]:
        query = self.db.query(Asset).filter(Asset.organization_id == organization_id)
        
        # Default: exclude archived
        if status is None:
            query = query.filter(Asset.status != AssetStatus.ARCHIVED)
        
        if asset_type:
            query = query.filter(Asset.type == asset_type)
        if status:
            query = query.filter(Asset.status == status)
        if tag:
            query = query.filter(Asset.tags.contains([tag]))
        if search:
            query = query.filter(Asset.value.contains(search))
        
        return query.offset(skip).limit(limit).all()