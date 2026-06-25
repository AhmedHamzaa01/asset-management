from datetime import datetime, timezone
from uuid import UUID

from app.api.v1.schemas.asset import AssetCreate, AssetUpdate
from app.core.exceptions import NotFoundError
from app.domain.enums import AssetStatus
from app.domain.models.asset import Asset
from app.repositories.asset_repository import AssetRepository


class AssetService:
    def __init__(self, repository: AssetRepository) -> None:
        self.repository = repository

    def create_asset(self, payload: AssetCreate, organization_id: UUID) -> Asset:
        existing = self.repository.get_by_type_value(
            asset_type=payload.type,
            value=payload.value,
            organization_id=organization_id,
        )
        if existing:
            existing.last_seen = datetime.now(timezone.utc)
            if payload.tags:
                existing.tags = sorted(set((existing.tags or []) + payload.tags))
            if payload.extra_data:
                existing.extra_data = {**(existing.extra_data or {}), **payload.extra_data}
            if existing.status == AssetStatus.STALE:
                existing.status = AssetStatus.ACTIVE
            return self.repository.save(existing)

        asset = Asset(
            type=payload.type,
            value=payload.value,
            source=payload.source,
            tags=payload.tags,
            extra_data=payload.extra_data,
            organization_id=organization_id,
        )
        return self.repository.create(asset)

    def list_assets(
        self,
        organization_id: UUID,
        skip: int,
        limit: int,
        asset_type,
        status,
        tag,
        search,
    ) -> list[Asset]:
        return self.repository.list_assets(
            organization_id=organization_id,
            skip=skip,
            limit=limit,
            asset_type=asset_type,
            status=status,
            tag=tag,
            search=search,
        )

    def get_asset(self, asset_id: int, organization_id: UUID) -> Asset:
        asset = self.repository.get_by_id(asset_id, organization_id)
        if not asset or asset.status == AssetStatus.ARCHIVED:
            raise NotFoundError("Asset not found")
        return asset

    def update_asset(
        self,
        asset_id: int,
        payload: AssetUpdate,
        organization_id: UUID,
    ) -> Asset:
        asset = self.repository.get_by_id(asset_id, organization_id)
        if not asset:
            raise NotFoundError("Asset not found")

        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(asset, key, value)

        return self.repository.save(asset)

    def delete_asset(self, asset_id: int, organization_id: UUID) -> None:
        asset = self.repository.get_by_id(asset_id, organization_id)
        if not asset:
            raise NotFoundError("Asset not found")

        asset.status = AssetStatus.ARCHIVED
        self.repository.save(asset)
