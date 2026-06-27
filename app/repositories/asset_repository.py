# app/repositories/asset_repository.py

from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session

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

    def get_by_id(self, asset_id: int, organization_id: UUID) -> Optional[Asset]:
        return (
            self.db.query(Asset)
            .filter(
                Asset.id == asset_id,
                Asset.organization_id == organization_id,
            )
            .first()
        )

    def get_by_type_value(
        self, asset_type: AssetType, value: str, organization_id: UUID
    ) -> Optional[Asset]:
        return (
            self.db.query(Asset)
            .filter(
                Asset.type == asset_type,
                Asset.value == value,
                Asset.organization_id == organization_id,
            )
            .first()
        )

    def list_assets(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 50,
        asset_type: Optional[AssetType] = None,
        status: Optional[AssetStatus] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None,
        sort=None,
        order: str = "desc",
    ) -> tuple[List[Asset], int]:
        query = self.db.query(Asset).filter(Asset.organization_id == organization_id)

        if status is None:
            query = query.filter(Asset.status != AssetStatus.ARCHIVED)
        else:
            query = query.filter(Asset.status == status)

        if asset_type:
            query = query.filter(Asset.type == asset_type)
        if tag:
            query = query.filter(Asset.tags.contains([tag]))
        if search:
            query = query.filter(Asset.value.contains(search))

        total = query.count()

        sortable = {
            "value": Asset.value,
            "status": Asset.status,
            "first_seen": Asset.first_seen,
            "last_seen": Asset.last_seen,
        }

        if sort in sortable:
            column = sortable[sort]
            query = query.order_by(column.asc() if order == "asc" else column.desc())

        items = query.offset(skip).limit(limit).all()
        return items, total