from fastapi import APIRouter, status

from app.api.deps import CurrentUserDep, RelationshipServiceDep
from app.api.v1.schemas.relationship import RelationshipCreate, RelationshipResponse

router = APIRouter()


@router.post(
    "/relationships",
    response_model=RelationshipResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_relationship(
    payload: RelationshipCreate,
    current_user: CurrentUserDep,
    service: RelationshipServiceDep,
) -> RelationshipResponse:
    return service.create_relationship(payload, current_user.organization_id)


@router.get("/assets/{asset_id}/relationships", response_model=list[RelationshipResponse])
def get_asset_relationships(
    asset_id: int,
    current_user: CurrentUserDep,
    service: RelationshipServiceDep,
) -> list[RelationshipResponse]:
    return service.list_for_asset(asset_id, current_user.organization_id)
