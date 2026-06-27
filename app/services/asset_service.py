
from datetime import datetime, timezone
from uuid import UUID

from pydantic import ValidationError

from app.api.v1.schemas.asset import AssetCreate, AssetUpdate
from app.api.v1.schemas.import_schema import RawAssetRecord
from app.core.exceptions import NotFoundError
from app.domain.enums import AssetStatus
from app.domain.models.asset import Asset
from app.repositories.asset_repository import AssetRepository
from app.repositories.relationship_repository import RelationshipRepository


class AssetService:

    def __init__(
        self,
        repository: AssetRepository,
        relationship_repository: RelationshipRepository,
    ) -> None:
        self.repository = repository
        self.relationship_repository = relationship_repository

    def bulk_import(self, assets: list[RawAssetRecord], organization_id: UUID) -> dict:
        inserted = 0
        updated = 0
        failed = 0
        errors: list[str] = []

        for index, raw in enumerate(assets):
            try:
                # Per-record validation — bad records are reported, not 422'd
                payload = raw.to_asset_create()
            except (ValidationError, Exception) as exc:
                failed += 1
                errors.append(f"Row {index}: validation error — {exc}")
                continue

            try:
                existing = self.repository.get_by_type_value(
                    asset_type=payload.type,
                    value=payload.value,
                    organization_id=organization_id,
                )
                self._upsert_asset(payload, organization_id, existing)
                if existing:
                    updated += 1
                else:
                    inserted += 1
            except Exception as exc:
                failed += 1
                errors.append(f"Row {index}: {exc}")

        return {
            "inserted": inserted,
            "updated": updated,
            "failed": failed,
            "errors": errors,
        }

    def create_asset(self, payload: AssetCreate, organization_id: UUID) -> Asset:
        existing = self.repository.get_by_type_value(
            asset_type=payload.type,
            value=payload.value,
            organization_id=organization_id,
        )
        return self._upsert_asset(payload, organization_id, existing)

    def _upsert_asset(
        self,
        payload: AssetCreate,
        organization_id: UUID,
        existing: Asset | None,
    ) -> Asset:
        if existing:
            existing.last_seen = datetime.now(timezone.utc)

            if payload.tags:
                existing.tags = sorted(set((existing.tags or []) + payload.tags))

            if payload.extra_data:
                existing.extra_data = {
                    **(existing.extra_data or {}),
                    **payload.extra_data,
                }

            # Re-appearing stale asset → back to active
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
        sort,
        order,
    ) -> tuple[list[Asset], int]:
        return self.repository.list_assets(
            organization_id=organization_id,
            skip=skip,
            limit=limit,
            asset_type=asset_type,
            status=status,
            tag=tag,
            search=search,
            sort=sort,
            order=order,
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


    def get_asset_graph(self, asset_id: int, organization_id: UUID) -> dict:
        asset = self.repository.get_by_id(asset_id, organization_id)
        if not asset:
            raise NotFoundError("Asset not found")

        related = self.relationship_repository.get_related_assets(
            asset_id, organization_id
        )
        return {"asset": asset, "related_assets": related}

  
    def mark_asset_stale(self, asset_id: int, organization_id: UUID) -> Asset:
        asset = self.repository.get_by_id(asset_id, organization_id)
        if not asset:
            raise NotFoundError("Asset not found")
        asset.status = AssetStatus.STALE
        return self.repository.save(asset)