"""
Request service layer.

This module provides business logic for procurement request operations
including CRUD, status transitions, and permission checks.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import desc, or_
from sqlalchemy.orm import Session, joinedload

from app.auth.models import User, UserRole
from app.models import Request, RequestStatus, OrderLine, StatusHistory, CommodityGroup
from app.schemas.request import RequestCreate, RequestUpdate, RequestStatusUpdate
from app.services.validation_service import ValidationService


class RequestServiceError(Exception):
    """Base exception for request service errors."""
    pass


class PermissionDeniedError(RequestServiceError):
    """Raised when user doesn't have permission for an operation."""
    pass


class RequestNotFoundError(RequestServiceError):
    """Raised when request is not found."""
    pass


class InvalidStatusTransitionError(RequestServiceError):
    """Raised when status transition is not allowed."""
    pass


class ValidationError(RequestServiceError):
    """Raised when validation fails."""
    pass


class RequestService:
    """Service for managing procurement requests."""

    def __init__(self, db: Session):
        self.db = db

    def create_request(
        self,
        user_id: UUID,
        data: RequestCreate,
    ) -> Request:
        """
        Create a new procurement request.

        Args:
            user_id: ID of the user creating the request
            data: Request creation data

        Returns:
            Created Request object

        Raises:
            ValidationError: If validation fails
        """
        # Validate request data
        is_valid, errors = ValidationService.validate_request_data(
            vat_id=data.vat_id,
            order_lines=data.order_lines,
        )
        if not is_valid:
            raise ValidationError("; ".join(errors))

        # Verify commodity group exists if provided
        if data.commodity_group_id:
            commodity_group = self.db.query(CommodityGroup).filter(
                CommodityGroup.id == data.commodity_group_id
            ).first()
            if not commodity_group:
                raise ValidationError(f"Commodity group {data.commodity_group_id} not found")

        # Calculate total cost from order lines
        total_cost = ValidationService.calculate_request_total(data.order_lines)

        # Create the request
        request = Request(
            user_id=user_id,
            title=data.title,
            vendor_name=data.vendor_name,
            vat_id=data.vat_id.upper(),
            commodity_group_id=data.commodity_group_id,
            department=data.department,
            total_cost=total_cost,
            status=RequestStatus.OPEN,
            notes=data.notes,
        )
        self.db.add(request)
        self.db.flush()  # Get the request ID

        # Create order lines
        for line_data in data.order_lines:
            line_total = ValidationService.calculate_order_line_total(
                line_data.unit_price,
                line_data.amount,
            )
            order_line = OrderLine(
                request_id=request.id,
                description=line_data.description,
                unit_price=line_data.unit_price,
                amount=line_data.amount,
                unit=line_data.unit,
                total_price=line_total,
            )
            self.db.add(order_line)

        # Create initial status history entry
        status_history = StatusHistory(
            request_id=request.id,
            status=RequestStatus.OPEN,
            changed_by_user_id=user_id,
            notes="Request created",
        )
        self.db.add(status_history)

        self.db.commit()
        self.db.refresh(request)

        return request

    def get_request(
        self,
        request_id: UUID,
        user_id: UUID,
        user_role: UserRole,
    ) -> Request:
        """
        Get a request by ID with permission check.

        Args:
            request_id: ID of the request
            user_id: ID of the requesting user
            user_role: Role of the requesting user

        Returns:
            Request object

        Raises:
            RequestNotFoundError: If request doesn't exist
            PermissionDeniedError: If user doesn't have access
        """
        request = self.db.query(Request).options(
            joinedload(Request.order_lines),
            joinedload(Request.commodity_group),
            joinedload(Request.user),
        ).filter(Request.id == request_id).first()

        if not request:
            raise RequestNotFoundError(f"Request {request_id} not found")

        # Permission check: requestors can only see their own requests
        if user_role == UserRole.REQUESTOR and request.user_id != user_id:
            raise PermissionDeniedError("You don't have permission to view this request")

        return request

    def list_requests(
        self,
        user_id: UUID,
        user_role: UserRole,
        status_filter: Optional[RequestStatus] = None,
        department_filter: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Request], int]:
        """
        List requests with filtering and pagination.

        Args:
            user_id: ID of the requesting user
            user_role: Role of the requesting user
            status_filter: Filter by status
            department_filter: Filter by department
            search: Search in title and vendor name
            page: Page number (1-based)
            page_size: Number of items per page

        Returns:
            Tuple of (list of requests, total count)
        """
        query = self.db.query(Request).options(
            joinedload(Request.commodity_group),
        )

        # Permission filter: requestors only see their own requests
        if user_role == UserRole.REQUESTOR:
            query = query.filter(Request.user_id == user_id)

        # Apply filters
        if status_filter:
            query = query.filter(Request.status == status_filter)

        if department_filter:
            query = query.filter(Request.department == department_filter)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Request.title.ilike(search_pattern),
                    Request.vendor_name.ilike(search_pattern),
                )
            )

        # Get total count before pagination
        total = query.count()

        # Apply ordering and pagination
        query = query.order_by(desc(Request.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        requests = query.all()

        return requests, total

    def update_request(
        self,
        request_id: UUID,
        user_id: UUID,
        user_role: UserRole,
        data: RequestUpdate,
    ) -> Request:
        """
        Update a request's basic information.

        Args:
            request_id: ID of the request
            user_id: ID of the requesting user
            user_role: Role of the requesting user
            data: Update data

        Returns:
            Updated Request object

        Raises:
            RequestNotFoundError: If request doesn't exist
            PermissionDeniedError: If user doesn't have permission
            ValidationError: If validation fails
        """
        request = self.get_request(request_id, user_id, user_role)

        # Only the owner can update their request details
        if request.user_id != user_id:
            raise PermissionDeniedError("You can only update your own requests")

        # Can't update closed requests
        if request.status == RequestStatus.CLOSED:
            raise PermissionDeniedError("Cannot update a closed request")

        # Validate VAT ID if provided
        if data.vat_id:
            is_valid, error = ValidationService.validate_vat_id(data.vat_id)
            if not is_valid:
                raise ValidationError(error)

        # Verify commodity group exists if provided
        if data.commodity_group_id:
            commodity_group = self.db.query(CommodityGroup).filter(
                CommodityGroup.id == data.commodity_group_id
            ).first()
            if not commodity_group:
                raise ValidationError(f"Commodity group {data.commodity_group_id} not found")

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                if field == "vat_id":
                    value = value.upper()
                setattr(request, field, value)

        request.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(request)

        return request

    def update_request_status(
        self,
        request_id: UUID,
        user_id: UUID,
        user_role: UserRole,
        data: RequestStatusUpdate,
    ) -> Request:
        """
        Update a request's status.

        Args:
            request_id: ID of the request
            user_id: ID of the requesting user
            user_role: Role of the requesting user
            data: Status update data

        Returns:
            Updated Request object

        Raises:
            RequestNotFoundError: If request doesn't exist
            PermissionDeniedError: If user doesn't have permission
            InvalidStatusTransitionError: If transition is not allowed
        """
        request = self.db.query(Request).filter(Request.id == request_id).first()

        if not request:
            raise RequestNotFoundError(f"Request {request_id} not found")

        # Only procurement team can change status
        if user_role != UserRole.PROCUREMENT_TEAM:
            raise PermissionDeniedError("Only procurement team members can change request status")

        # Validate status transition
        is_valid, error = ValidationService.validate_status_transition(
            request.status,
            data.status,
        )
        if not is_valid:
            raise InvalidStatusTransitionError(error)

        # Update status
        old_status = request.status
        request.status = data.status
        request.updated_at = datetime.utcnow()

        # Create status history entry
        status_history = StatusHistory(
            request_id=request.id,
            status=data.status,
            changed_by_user_id=user_id,
            notes=data.notes or f"Status changed from {old_status.value} to {data.status.value}",
        )
        self.db.add(status_history)

        self.db.commit()
        self.db.refresh(request)

        return request

    def get_status_history(
        self,
        request_id: UUID,
        user_id: UUID,
        user_role: UserRole,
    ) -> List[StatusHistory]:
        """
        Get status history for a request.

        Args:
            request_id: ID of the request
            user_id: ID of the requesting user
            user_role: Role of the requesting user

        Returns:
            List of StatusHistory entries

        Raises:
            RequestNotFoundError: If request doesn't exist
            PermissionDeniedError: If user doesn't have access
        """
        # First verify the user has access to this request
        self.get_request(request_id, user_id, user_role)

        history = self.db.query(StatusHistory).options(
            joinedload(StatusHistory.changed_by),
        ).filter(
            StatusHistory.request_id == request_id
        ).order_by(desc(StatusHistory.changed_at)).all()

        return history

    def delete_request(
        self,
        request_id: UUID,
        user_id: UUID,
        user_role: UserRole,
    ) -> bool:
        """
        Delete a request (soft delete by closing, or hard delete if open).

        Args:
            request_id: ID of the request
            user_id: ID of the requesting user
            user_role: Role of the requesting user

        Returns:
            True if deleted successfully

        Raises:
            RequestNotFoundError: If request doesn't exist
            PermissionDeniedError: If user doesn't have permission
        """
        request = self.get_request(request_id, user_id, user_role)

        # Only the owner or procurement team can delete
        if request.user_id != user_id and user_role != UserRole.PROCUREMENT_TEAM:
            raise PermissionDeniedError("You don't have permission to delete this request")

        # Only allow deletion of open requests
        if request.status != RequestStatus.OPEN:
            raise PermissionDeniedError("Can only delete requests with 'open' status")

        # Hard delete for open requests
        self.db.delete(request)
        self.db.commit()

        return True
