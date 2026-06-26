from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from uuid import UUID
from app.api.deps import CurrentUserDep, AssetServiceDep, get_asset_service
from app.api.v1.schemas.asset import (
    AssetCreate,
    AssetResponse,
    AssetUpdate,
)
from app.api.v1.schemas.graph import AssetGraphResponse
from app.api.v1.schemas.import_schema import BulkImportRequest
from app.domain.enums import AssetStatus, AssetType
from app.services.asset_service import AssetService


router = APIRouter(prefix="/assets")


@router.post("/import")
def import_assets(
    payload: BulkImportRequest,
    current_user: CurrentUserDep,
    service: AssetServiceDep,
):
    return service.bulk_import(
        assets=payload.assets,
        organization_id=current_user.organization_id,
    )


@router.post(
    "/",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_asset(
    payload: AssetCreate,
    current_user: CurrentUserDep,
    service: AssetServiceDep,
) -> AssetResponse:

    asset = service.create_asset(
        payload,
        organization_id=current_user.organization_id,
    )

    return AssetResponse.model_validate(asset)


@router.patch("/{asset_id}/stale")
def mark_stale(
    asset_id: int,
    current_user: CurrentUserDep,
    service: AssetServiceDep,
):
    return service.mark_asset_stale(
        asset_id=asset_id,
        organization_id=current_user.organization_id,
    )

@router.get(
    "/{asset_id}/graph",
    response_model=AssetGraphResponse,
)
def get_graph(
    asset_id : int,
    current_user: CurrentUserDep,
    service: AssetService = Depends(
        get_asset_service
    ),
):
    return (
        service
        .get_asset_graph(
            asset_id,
            organization_id=current_user.organization_id
        )
    )


# @router.get(
#     "/{asset_id}/graph",
#     response_model=AssetGraphResponse,
# )
# def get_graph(
#     asset_id: UUID,
#     service: AssetService = Depends(
#         get_asset_service
#     ),
# ):
#     return (
#         service.get_asset_graph(
#             asset_id
#         )
#     )

@router.get("/", response_model=list[AssetResponse])
def get_assets(
    current_user: CurrentUserDep,
    service: AssetServiceDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    type: Optional[AssetType] = None,
    status: Optional[AssetStatus] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    sort: str | None = Query(None),
    order: str = Query("desc"),
) -> list[AssetResponse]:

    assets = service.list_assets(
        organization_id=current_user.organization_id,
        skip=skip,
        limit=limit,
        asset_type=type,
        status=status,
        tag=tag,
        search=search,
        sort=sort,
        order=order,
    )

    return [
        AssetResponse.model_validate(asset)
        for asset in assets
    ]


@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(
    asset_id: int,
    current_user: CurrentUserDep,
    service: AssetServiceDep,
) -> AssetResponse:

    asset = service.get_asset(
        asset_id,
        organization_id=current_user.organization_id,
    )

    return AssetResponse.model_validate(asset)


@router.put("/{asset_id}", response_model=AssetResponse)
def update_asset(
    asset_id: int,
    payload: AssetUpdate,
    current_user: CurrentUserDep,
    service: AssetServiceDep,
) -> AssetResponse:

    asset = service.update_asset(
        asset_id,
        payload,
        organization_id=current_user.organization_id,
    )

    return AssetResponse.model_validate(asset)


@router.delete(
    "/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_asset(
    asset_id: int,
    current_user: CurrentUserDep,
    service: AssetServiceDep,
) -> None:

    service.delete_asset(
        asset_id,
        organization_id=current_user.organization_id,
    )