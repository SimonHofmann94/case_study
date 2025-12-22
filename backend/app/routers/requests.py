"""
Request API router.

This module provides API endpoints for procurement request operations.
"""

import math
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, get_procurement_user
from app.auth.models import User
from app.database import get_db
from app.models import RequestStatus
from app.schemas.request import (
    RequestCreate,
    RequestUpdate,
    RequestStatusUpdate,
    ProcurementNoteCreate,
    RequestResponse,
    RequestDetailResponse,
    RequestListResponse,
)
from app.schemas.analytics import RequestAnalytics, FilterOptions
from app.schemas.status_history import StatusHistoryResponse
from app.services.request_service import (
    RequestService,
    PermissionDeniedError,
    RequestNotFoundError,
    InvalidStatusTransitionError,
    ValidationError,
)
from app.utils.rate_limit import limiter

router = APIRouter(prefix="/requests", tags=["Requests"])


@router.post(
    "",
    response_model=RequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new procurement request",
    description="Create a new procurement request with order lines. Only authenticated users can create requests.",
)
@limiter.limit("100/hour")
async def create_request(
    request: Request,
    request_data: RequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new procurement request.

    - **title**: Brief description of the request
    - **vendor_name**: Name of the vendor
    - **vat_id**: VAT identification number (format: DE + 9 digits)
    - **department**: Department making the request
    - **commodity_group_id**: Optional commodity group classification
    - **order_lines**: List of items/services (at least one required)
    - **notes**: Optional additional notes
    """
    service = RequestService(db)
    try:
        request = service.create_request(
            user_id=current_user.id,
            data=request_data,
        )
        return request
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/analytics",
    response_model=RequestAnalytics,
    summary="Get request analytics",
    description="Get analytics summary with counts and total values by status. Procurement team only.",
)
@limiter.limit("100/hour")
async def get_analytics(
    request: Request,
    current_user: User = Depends(get_procurement_user),
    db: Session = Depends(get_db),
):
    """
    Get analytics summary for procurement dashboard.

    - Returns counts for open, in_progress, and closed requests
    - Returns total value for each status
    - Only accessible by procurement team
    """
    service = RequestService(db)
    return service.get_analytics()


@router.get(
    "/filter-options",
    response_model=FilterOptions,
    summary="Get filter options",
    description="Get available filter options for the procurement dashboard. Procurement team only.",
)
@limiter.limit("100/hour")
async def get_filter_options(
    request: Request,
    current_user: User = Depends(get_procurement_user),
    db: Session = Depends(get_db),
):
    """
    Get available filter options for the procurement dashboard.

    - Returns unique departments
    - Returns unique vendor names
    - Returns list of requestors who have created requests
    - Only accessible by procurement team
    """
    service = RequestService(db)
    return service.get_filter_options()


@router.get(
    "",
    response_model=RequestListResponse,
    summary="List procurement requests",
    description="List requests with optional filtering. Requestors see only their own requests, procurement team sees all.",
)
@limiter.limit("100/hour")
async def list_requests(
    request: Request,
    status_filter: Optional[RequestStatus] = Query(None, alias="status", description="Filter by status"),
    department: Optional[str] = Query(None, description="Filter by department"),
    search: Optional[str] = Query(None, description="Search in title and vendor name"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    # Enhanced filters for procurement dashboard
    date_from: Optional[datetime] = Query(None, description="Filter from date (ISO format)"),
    date_to: Optional[datetime] = Query(None, description="Filter to date (ISO format)"),
    vendor: Optional[str] = Query(None, description="Filter by vendor name"),
    commodity_group_id: Optional[UUID] = Query(None, description="Filter by commodity group"),
    min_cost: Optional[Decimal] = Query(None, description="Minimum total cost"),
    max_cost: Optional[Decimal] = Query(None, description="Maximum total cost"),
    requestor_id: Optional[UUID] = Query(None, description="Filter by requestor (procurement only)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List procurement requests with filtering and pagination.

    - Requestors can only see their own requests
    - Procurement team can see all requests
    - Supports filtering by status, department, date range, vendor, commodity group, cost range
    - Supports search in title and vendor name
    - Requestor filter only works for procurement team
    """
    service = RequestService(db)
    requests, total = service.list_requests(
        user_id=current_user.id,
        user_role=current_user.role,
        status_filter=status_filter,
        department_filter=department,
        search=search,
        page=page,
        page_size=page_size,
        date_from=date_from,
        date_to=date_to,
        vendor_filter=vendor,
        commodity_group_id=commodity_group_id,
        min_cost=min_cost,
        max_cost=max_cost,
        requestor_id=requestor_id,
    )

    return RequestListResponse(
        items=requests,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get(
    "/{request_id}",
    response_model=RequestDetailResponse,
    summary="Get request details",
    description="Get detailed information about a specific request including order lines.",
)
@limiter.limit("100/hour")
async def get_request(
    request: Request,
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific request.

    - Requestors can only view their own requests
    - Procurement team can view all requests
    - Includes order lines and commodity group details
    """
    service = RequestService(db)
    try:
        request = service.get_request(
            request_id=request_id,
            user_id=current_user.id,
            user_role=current_user.role,
        )
        return request
    except RequestNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except PermissionDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.patch(
    "/{request_id}",
    response_model=RequestResponse,
    summary="Update request details",
    description="Update basic information of a request. Only the owner can update their requests.",
)
@limiter.limit("100/hour")
async def update_request(
    request: Request,
    request_id: UUID,
    request_data: RequestUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update basic information of a request.

    - Only the request owner can update their request
    - Cannot update closed requests
    - Does not update order lines (use separate endpoint)
    """
    service = RequestService(db)
    try:
        request = service.update_request(
            request_id=request_id,
            user_id=current_user.id,
            user_role=current_user.role,
            data=request_data,
        )
        return request
    except RequestNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except PermissionDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put(
    "/{request_id}/status",
    response_model=RequestResponse,
    summary="Update request status",
    description="Update the status of a request. Only procurement team members can change status.",
)
@limiter.limit("100/hour")
async def update_request_status(
    request: Request,
    request_id: UUID,
    status_data: RequestStatusUpdate,
    current_user: User = Depends(get_procurement_user),
    db: Session = Depends(get_db),
):
    """
    Update the status of a request.

    - Only procurement team members can change status
    - Valid transitions:
      - open -> in_progress, closed
      - in_progress -> closed, open
      - closed -> (none, cannot reopen)
    """
    service = RequestService(db)
    try:
        request = service.update_request_status(
            request_id=request_id,
            user_id=current_user.id,
            user_role=current_user.role,
            data=status_data,
        )
        return request
    except RequestNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except PermissionDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except InvalidStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{request_id}/notes",
    response_model=StatusHistoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add procurement note",
    description="Add a note to a request without changing status. Procurement team only.",
)
@limiter.limit("100/hour")
async def add_procurement_note(
    request: Request,
    request_id: UUID,
    note_data: ProcurementNoteCreate,
    current_user: User = Depends(get_procurement_user),
    db: Session = Depends(get_db),
):
    """
    Add a procurement note to a request.

    - Only procurement team members can add notes
    - Does not change the request status
    - Note is visible in status history to requestors
    """
    service = RequestService(db)
    try:
        history_entry = service.add_procurement_note(
            request_id=request_id,
            user_id=current_user.id,
            notes=note_data.notes,
        )
        return StatusHistoryResponse(
            id=history_entry.id,
            request_id=history_entry.request_id,
            status=history_entry.status,
            changed_by_user_id=history_entry.changed_by_user_id,
            changed_at=history_entry.changed_at,
            notes=history_entry.notes,
            changed_by_name=current_user.full_name,
        )
    except RequestNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/{request_id}/history",
    response_model=list[StatusHistoryResponse],
    summary="Get request status history",
    description="Get the status change history for a request.",
)
@limiter.limit("100/hour")
async def get_request_history(
    request: Request,
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get the status change history for a request.

    - Returns all status changes with timestamps and who made the change
    - Requestors can only view history for their own requests
    - Procurement team can view history for all requests
    """
    service = RequestService(db)
    try:
        history = service.get_status_history(
            request_id=request_id,
            user_id=current_user.id,
            user_role=current_user.role,
        )
        # Map to response with changed_by name
        result = []
        for entry in history:
            response = StatusHistoryResponse(
                id=entry.id,
                request_id=entry.request_id,
                status=entry.status,
                changed_by_user_id=entry.changed_by_user_id,
                changed_at=entry.changed_at,
                notes=entry.notes,
                changed_by_name=entry.changed_by.full_name if entry.changed_by else None,
            )
            result.append(response)
        return result
    except RequestNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except PermissionDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.delete(
    "/{request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a request",
    description="Delete a request. Only open requests can be deleted by their owner or procurement team.",
)
@limiter.limit("100/hour")
async def delete_request(
    request: Request,
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a procurement request.

    - Only open requests can be deleted
    - Request owner or procurement team can delete
    """
    service = RequestService(db)
    try:
        service.delete_request(
            request_id=request_id,
            user_id=current_user.id,
            user_role=current_user.role,
        )
        return None
    except RequestNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except PermissionDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
