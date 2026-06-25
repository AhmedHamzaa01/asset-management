from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.models.relationship import Relationship


class RelationshipRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_related_assets(
        self,
        asset_id,
    ):
        relationships = (
        self.db.query(Relationship)
        .filter(
            (
                Relationship.parent_asset_id
                == asset_id
            )
            |
            (
                Relationship.child_asset_id
                == asset_id
            )
        )
        .all()
         )

        ids = set()

        for relation in relationships:

            ids.add(
                relation.parent_asset_id
            )

            ids.add(
                relation.child_asset_id
            )

        ids.discard(asset_id)

        return (
            self.db.query(Asset)
            .filter(
                Asset.id.in_(ids)
            )
            .all()
        )    

    def create(self, relationship: Relationship) -> Relationship:
        self.db.add(relationship)
        self.db.commit()
        self.db.refresh(relationship)
        return relationship

    def list_by_asset(self, asset_id: int, organization_id: UUID) -> list[Relationship]:
        return (
            self.db.query(Relationship)
            .filter(
                Relationship.organization_id == organization_id,
                (Relationship.source_asset_id == asset_id)
                | (Relationship.target_asset_id == asset_id),
            )
            .all()
        )

    def get_existing(
        self,
        source_asset_id: int,
        target_asset_id: int,
        relationship_type: str,
        organization_id: UUID,
    ) -> Relationship | None:
        return (
            self.db.query(Relationship)
            .filter(
                Relationship.source_asset_id == source_asset_id,
                Relationship.target_asset_id == target_asset_id,
                Relationship.relationship_type == relationship_type,
                Relationship.organization_id == organization_id,
            )
            .first()
        )
