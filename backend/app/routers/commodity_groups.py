"""
Commodity Group API router.

This module provides API endpoints for commodity group operations.
Commodity groups are read-only reference data for classifying procurement requests.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.database import get_db
from app.models import CommodityGroup
from app.schemas.commodity_group import CommodityGroupResponse
from app.utils.rate_limit import limiter

router = APIRouter(prefix="/commodity-groups", tags=["Commodity Groups"])


@router.get(
    "",
    response_model=list[CommodityGroupResponse],
    summary="List all commodity groups",
    description="Get all commodity groups for classification dropdown.",
)
@limiter.limit("100/hour")
async def list_commodity_groups(
    request: Request,
    category: Optional[str] = Query(None, description="Filter by category code"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all commodity groups.

    - Returns all available commodity groups
    - Optionally filter by category code
    - Optionally search in name/description
    - Used for dropdown selection when creating requests
    """
    query = db.query(CommodityGroup)

    if category:
        query = query.filter(CommodityGroup.category == category.upper())

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            CommodityGroup.name.ilike(search_pattern)
            | CommodityGroup.description.ilike(search_pattern)
        )

    # Order by category and name
    query = query.order_by(CommodityGroup.category, CommodityGroup.name)

    return query.all()


@router.get(
    "/categories",
    response_model=list[str],
    summary="List unique categories",
    description="Get list of unique category codes.",
)
@limiter.limit("100/hour")
async def list_categories(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List unique category codes.

    - Returns distinct category values
    - Useful for filtering UI
    """
    categories = db.query(CommodityGroup.category).distinct().order_by(CommodityGroup.category).all()
    return [c[0] for c in categories]


@router.get(
    "/{commodity_group_id}",
    response_model=CommodityGroupResponse,
    summary="Get commodity group details",
    description="Get detailed information about a specific commodity group.",
)
@limiter.limit("100/hour")
async def get_commodity_group(
    request: Request,
    commodity_group_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific commodity group by ID.

    - Returns full commodity group details
    """
    commodity_group = db.query(CommodityGroup).filter(
        CommodityGroup.id == commodity_group_id
    ).first()

    if not commodity_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commodity group {commodity_group_id} not found",
        )

    return commodity_group
