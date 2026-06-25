from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query, status, Depends
from sqlalchemy.orm import Session

from app.api.deps import CurrentUserDep, AssetServiceDep
from app.infrastructure.database import get_db
from app.services.asset_service import AssetService
from app.repositories.asset_repository import AssetRepository
from app.api.v1.schemas.asset import AssetCreate, AssetResponse, AssetUpdate
from app.domain.enums import AssetStatus, AssetType
from app.domain.models.user import User

router = APIRouter(prefix="/assets")


@router.post("/", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
def create_asset(
    payload: AssetCreate,
    current_user: CurrentUserDep,
    service: AssetServiceDep,
) -> AssetResponse:
    asset = service.create_asset(payload, organization_id=current_user.organization_id)
    return AssetResponse.model_validate(asset)


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
) -> list[AssetResponse]:
    assets = service.list_assets(
        organization_id=current_user.organization_id,
        skip=skip,
        limit=limit,
        asset_type=type,
        status=status,
        tag=tag,
        search=search,
    )
    return [AssetResponse.model_validate(asset) for asset in assets]


@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(
    asset_id: int,
    current_user: CurrentUserDep,
    service: AssetServiceDep,
) -> AssetResponse:
    asset = service.get_asset(asset_id, organization_id=current_user.organization_id)
    return AssetResponse.model_validate(asset)


@router.put("/{asset_id}", response_model=AssetResponse)
def update_asset(
    asset_id: int,
    payload: AssetUpdate,
    current_user: CurrentUserDep,
    service: AssetServiceDep,
) -> AssetResponse:
    asset = service.update_asset(asset_id, payload, organization_id=current_user.organization_id)
    return AssetResponse.model_validate(asset)


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(
    asset_id: int,
    current_user: CurrentUserDep,
    service: AssetServiceDep,
) -> None:
    service.delete_asset(asset_id, organization_id=current_user.organization_id)