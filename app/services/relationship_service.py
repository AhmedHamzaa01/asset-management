from uuid import UUID

from app.api.v1.schemas.relationship import RelationshipCreate
from app.core.exceptions import ConflictError, NotFoundError
from app.domain.models.relationship import Relationship
from app.repositories.asset_repository import AssetRepository
from app.repositories.relationship_repository import RelationshipRepository


class RelationshipService:
    def __init__(
        self,
        relationship_repository: RelationshipRepository,
        asset_repository: AssetRepository,
    ) -> None:
        self.relationship_repository = relationship_repository
        self.asset_repository = asset_repository

    def create_relationship(
        self,
        payload: RelationshipCreate,
        organization_id: UUID,
    ) -> Relationship:
        source = self.asset_repository.get_by_id(payload.source_asset_id, organization_id)
        target = self.asset_repository.get_by_id(payload.target_asset_id, organization_id)

        if not source or not target:
            raise NotFoundError("Source or target asset not found")

        existing = self.relationship_repository.get_existing(
            source_asset_id=payload.source_asset_id,
            target_asset_id=payload.target_asset_id,
            relationship_type=payload.relationship_type,
            organization_id=organization_id,
        )
        if existing:
            raise ConflictError("Relationship already exists")

        relationship = Relationship(
            source_asset_id=payload.source_asset_id,
            target_asset_id=payload.target_asset_id,
            relationship_type=payload.relationship_type,
            organization_id=organization_id,
        )
        return self.relationship_repository.create(relationship)

    def list_for_asset(self, asset_id: int, organization_id: UUID) -> list[Relationship]:
        return self.relationship_repository.list_by_asset(asset_id, organization_id)
