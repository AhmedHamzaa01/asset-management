from typing import Optional
from fastapi import APIRouter, Query, status, Depends
from sqlalchemy.orm import Session
from app.infrastructure.database import get_db
from app.services.asset_service import AssetService
from app.repositories.asset_repository import AssetRepository
from app.api.v1.schemas.asset import AssetCreate, AssetResponse, AssetUpdate
from app.domain.enums import AssetStatus, AssetType

router = APIRouter(prefix="/assets")

# Helper to get AssetService
def get_asset_service(db: Session = Depends(get_db)) -> AssetService:
    repository = AssetRepository(db)
    return AssetService(repository)

@router.post("/", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
def create_asset(
    payload: AssetCreate,
    service: AssetService = Depends(get_asset_service),
) -> AssetResponse:
    # Use organization_id = 1 for testing
    asset = service.create_asset(payload, organization_id=1)
    return AssetResponse.model_validate(asset)


@router.get("/", response_model=list[AssetResponse])
def get_assets(
    service: AssetService = Depends(get_asset_service),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    type: Optional[AssetType] = None,
    status: Optional[AssetStatus] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
) -> list[AssetResponse]:
    assets = service.list_assets(
        organization_id=1,
        skip=skip,
        limit=limit,
        asset_type=type,
        status=status,
        tag=tag,
        search=search
    )
    return [AssetResponse.model_validate(asset) for asset in assets]


@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(
    asset_id: int,
    service: AssetService = Depends(get_asset_service),
) -> AssetResponse:
    asset = service.get_asset(asset_id, organization_id=1)
    return AssetResponse.model_validate(asset)


@router.put("/{asset_id}", response_model=AssetResponse)
def update_asset(
    asset_id: int,
    payload: AssetUpdate,
    service: AssetService = Depends(get_asset_service),
) -> AssetResponse:
    asset = service.update_asset(asset_id, payload, organization_id=1)
    return AssetResponse.model_validate(asset)


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(
    asset_id: int,
    service: AssetService = Depends(get_asset_service),
) -> None:
    service.delete_asset(asset_id, organization_id=1)