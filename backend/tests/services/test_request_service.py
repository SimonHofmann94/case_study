"""
Unit tests for RequestService.

Tests CRUD operations, status transitions, and permission checks.
"""

import pytest
from decimal import Decimal
from uuid import uuid4

from app.auth.models import User, UserRole
from app.models import CommodityGroup, Request, RequestStatus
from app.schemas.request import (
    RequestCreate,
    RequestUpdate,
    RequestStatusUpdate,
    OrderLineCreate,
)
from app.services.request_service import (
    RequestService,
    PermissionDeniedError,
    RequestNotFoundError,
    InvalidStatusTransitionError,
    ValidationError,
)


@pytest.fixture
def commodity_group(db_session):
    """Create a test commodity group."""
    group = CommodityGroup(
        category="A",
        name="Test Commodity",
        description="Test description",
    )
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)
    return group


@pytest.fixture
def requestor_user(create_test_user):
    """Create a requestor user."""
    return create_test_user(
        email="requestor@example.com",
        role=UserRole.REQUESTOR,
        department="Engineering",
    )


@pytest.fixture
def procurement_user(create_test_user):
    """Create a procurement team user."""
    return create_test_user(
        email="procurement@example.com",
        role=UserRole.PROCUREMENT_TEAM,
        department="Procurement",
    )


@pytest.fixture
def another_requestor(create_test_user):
    """Create another requestor user."""
    return create_test_user(
        email="another@example.com",
        role=UserRole.REQUESTOR,
        department="Marketing",
    )


@pytest.fixture
def valid_request_data(commodity_group):
    """Valid request creation data."""
    return RequestCreate(
        title="Test Request",
        vendor_name="Test Vendor GmbH",
        vat_id="DE123456789",
        department="Engineering",
        commodity_group_id=commodity_group.id,
        notes="Test notes",
        order_lines=[
            OrderLineCreate(
                description="Item 1",
                unit_price=Decimal("100.00"),
                amount=2,
                unit="pieces",
            ),
            OrderLineCreate(
                description="Item 2",
                unit_price=Decimal("50.00"),
                amount=3,
                unit="hours",
            ),
        ],
    )


class TestRequestServiceCreate:
    """Tests for request creation."""

    def test_create_request_success(
        self, db_session, requestor_user, valid_request_data
    ):
        """Test successful request creation."""
        service = RequestService(db_session)
        request = service.create_request(
            user_id=requestor_user.id,
            data=valid_request_data,
        )

        assert request.id is not None
        assert request.title == "Test Request"
        assert request.vendor_name == "Test Vendor GmbH"
        assert request.vat_id == "DE123456789"
        assert request.status == RequestStatus.OPEN
        assert request.user_id == requestor_user.id
        assert len(request.order_lines) == 2
        # Total: 100*2 + 50*3 = 350
        assert request.total_cost == Decimal("350.00")

    def test_create_request_invalid_vat_id(
        self, db_session, requestor_user, commodity_group
    ):
        """Test request creation with invalid VAT ID format - caught by Pydantic."""
        from pydantic import ValidationError as PydanticValidationError

        # Pydantic validates VAT ID pattern (DE + 9 digits) before the service
        with pytest.raises(PydanticValidationError) as exc_info:
            RequestCreate(
                title="Test Request",
                vendor_name="Test Vendor",
                vat_id="XX123456789",  # Valid length but wrong format
                department="Engineering",
                order_lines=[
                    OrderLineCreate(
                        description="Item 1",
                        unit_price=Decimal("100.00"),
                        amount=1,
                        unit="pieces",
                    ),
                ],
            )

        assert "pattern" in str(exc_info.value).lower()

    def test_create_request_empty_order_lines(
        self, db_session, requestor_user
    ):
        """Test request creation with empty order lines - caught by Pydantic."""
        from pydantic import ValidationError as PydanticValidationError

        # Pydantic validates min_length on order_lines before the service
        with pytest.raises(PydanticValidationError) as exc_info:
            RequestCreate(
                title="Test Request",
                vendor_name="Test Vendor",
                vat_id="DE123456789",
                department="Engineering",
                order_lines=[],
            )

        assert "too_short" in str(exc_info.value)

    def test_create_request_invalid_commodity_group(
        self, db_session, requestor_user
    ):
        """Test request creation with non-existent commodity group."""
        service = RequestService(db_session)
        invalid_data = RequestCreate(
            title="Test Request",
            vendor_name="Test Vendor",
            vat_id="DE123456789",
            department="Engineering",
            commodity_group_id=uuid4(),  # Non-existent
            order_lines=[
                OrderLineCreate(
                    description="Item 1",
                    unit_price=Decimal("100.00"),
                    amount=1,
                    unit="pieces",
                ),
            ],
        )

        with pytest.raises(ValidationError) as exc_info:
            service.create_request(user_id=requestor_user.id, data=invalid_data)

        assert "Commodity group" in str(exc_info.value)


class TestRequestServiceGet:
    """Tests for getting requests."""

    def test_get_request_owner_success(
        self, db_session, requestor_user, valid_request_data
    ):
        """Test owner can get their own request."""
        service = RequestService(db_session)
        created = service.create_request(
            user_id=requestor_user.id,
            data=valid_request_data,
        )

        request = service.get_request(
            request_id=created.id,
            user_id=requestor_user.id,
            user_role=requestor_user.role,
        )

        assert request.id == created.id
        assert request.title == "Test Request"

    def test_get_request_procurement_success(
        self, db_session, requestor_user, procurement_user, valid_request_data
    ):
        """Test procurement team can get any request."""
        service = RequestService(db_session)
        created = service.create_request(
            user_id=requestor_user.id,
            data=valid_request_data,
        )

        request = service.get_request(
            request_id=created.id,
            user_id=procurement_user.id,
            user_role=procurement_user.role,
        )

        assert request.id == created.id

    def test_get_request_other_user_denied(
        self, db_session, requestor_user, another_requestor, valid_request_data
    ):
        """Test requestor cannot get another user's request."""
        service = RequestService(db_session)
        created = service.create_request(
            user_id=requestor_user.id,
            data=valid_request_data,
        )

        with pytest.raises(PermissionDeniedError):
            service.get_request(
                request_id=created.id,
                user_id=another_requestor.id,
                user_role=another_requestor.role,
            )

    def test_get_request_not_found(self, db_session, requestor_user):
        """Test getting non-existent request."""
        service = RequestService(db_session)

        with pytest.raises(RequestNotFoundError):
            service.get_request(
                request_id=uuid4(),
                user_id=requestor_user.id,
                user_role=requestor_user.role,
            )


class TestRequestServiceList:
    """Tests for listing requests."""

    def test_list_requests_requestor_only_own(
        self, db_session, requestor_user, another_requestor, valid_request_data
    ):
        """Test requestor only sees their own requests."""
        service = RequestService(db_session)

        # Create request for first user
        service.create_request(
            user_id=requestor_user.id,
            data=valid_request_data,
        )

        # Create request for second user
        another_data = RequestCreate(
            title="Another Request",
            vendor_name="Another Vendor",
            vat_id="DE987654321",
            department="Marketing",
            order_lines=[
                OrderLineCreate(
                    description="Item",
                    unit_price=Decimal("100.00"),
                    amount=1,
                    unit="pieces",
                ),
            ],
        )
        service.create_request(
            user_id=another_requestor.id,
            data=another_data,
        )

        # First user should only see their request
        requests, total = service.list_requests(
            user_id=requestor_user.id,
            user_role=requestor_user.role,
        )

        assert total == 1
        assert len(requests) == 1
        assert requests[0].user_id == requestor_user.id

    def test_list_requests_procurement_sees_all(
        self, db_session, requestor_user, another_requestor, procurement_user, valid_request_data
    ):
        """Test procurement team sees all requests."""
        service = RequestService(db_session)

        # Create requests for different users
        service.create_request(
            user_id=requestor_user.id,
            data=valid_request_data,
        )

        another_data = RequestCreate(
            title="Another Request",
            vendor_name="Another Vendor",
            vat_id="DE987654321",
            department="Marketing",
            order_lines=[
                OrderLineCreate(
                    description="Item",
                    unit_price=Decimal("100.00"),
                    amount=1,
                    unit="pieces",
                ),
            ],
        )
        service.create_request(
            user_id=another_requestor.id,
            data=another_data,
        )

        # Procurement should see all
        requests, total = service.list_requests(
            user_id=procurement_user.id,
            user_role=procurement_user.role,
        )

        assert total == 2
        assert len(requests) == 2

    def test_list_requests_filter_by_status(
        self, db_session, procurement_user, requestor_user, valid_request_data
    ):
        """Test filtering by status."""
        service = RequestService(db_session)

        # Create and change status of one request
        request1 = service.create_request(
            user_id=requestor_user.id,
            data=valid_request_data,
        )
        service.update_request_status(
            request_id=request1.id,
            user_id=procurement_user.id,
            user_role=procurement_user.role,
            data=RequestStatusUpdate(status=RequestStatus.IN_PROGRESS),
        )

        # Create another open request
        another_data = RequestCreate(
            title="Another Request",
            vendor_name="Another Vendor",
            vat_id="DE987654321",
            department="Marketing",
            order_lines=[
                OrderLineCreate(
                    description="Item",
                    unit_price=Decimal("100.00"),
                    amount=1,
                    unit="pieces",
                ),
            ],
        )
        service.create_request(
            user_id=requestor_user.id,
            data=another_data,
        )

        # Filter by open status
        requests, total = service.list_requests(
            user_id=procurement_user.id,
            user_role=procurement_user.role,
            status_filter=RequestStatus.OPEN,
        )

        assert total == 1
        assert requests[0].status == RequestStatus.OPEN


class TestRequestServiceStatusTransition:
    """Tests for status transitions."""

    def test_open_to_in_progress(
        self, db_session, requestor_user, procurement_user, valid_request_data
    ):
        """Test valid transition from open to in_progress."""
        service = RequestService(db_session)
        request = service.create_request(
            user_id=requestor_user.id,
            data=valid_request_data,
        )

        updated = service.update_request_status(
            request_id=request.id,
            user_id=procurement_user.id,
            user_role=procurement_user.role,
            data=RequestStatusUpdate(status=RequestStatus.IN_PROGRESS),
        )

        assert updated.status == RequestStatus.IN_PROGRESS

    def test_open_to_closed(
        self, db_session, requestor_user, procurement_user, valid_request_data
    ):
        """Test valid transition from open to closed."""
        service = RequestService(db_session)
        request = service.create_request(
            user_id=requestor_user.id,
            data=valid_request_data,
        )

        updated = service.update_request_status(
            request_id=request.id,
            user_id=procurement_user.id,
            user_role=procurement_user.role,
            data=RequestStatusUpdate(status=RequestStatus.CLOSED),
        )

        assert updated.status == RequestStatus.CLOSED

    def test_in_progress_to_closed(
        self, db_session, requestor_user, procurement_user, valid_request_data
    ):
        """Test valid transition from in_progress to closed."""
        service = RequestService(db_session)
        request = service.create_request(
            user_id=requestor_user.id,
            data=valid_request_data,
        )

        # First transition to in_progress
        service.update_request_status(
            request_id=request.id,
            user_id=procurement_user.id,
            user_role=procurement_user.role,
            data=RequestStatusUpdate(status=RequestStatus.IN_PROGRESS),
        )

        # Then to closed
        updated = service.update_request_status(
            request_id=request.id,
            user_id=procurement_user.id,
            user_role=procurement_user.role,
            data=RequestStatusUpdate(status=RequestStatus.CLOSED),
        )

        assert updated.status == RequestStatus.CLOSED

    def test_closed_cannot_transition(
        self, db_session, requestor_user, procurement_user, valid_request_data
    ):
        """Test that closed requests cannot transition."""
        service = RequestService(db_session)
        request = service.create_request(
            user_id=requestor_user.id,
            data=valid_request_data,
        )

        # Close the request
        service.update_request_status(
            request_id=request.id,
            user_id=procurement_user.id,
            user_role=procurement_user.role,
            data=RequestStatusUpdate(status=RequestStatus.CLOSED),
        )

        # Try to reopen
        with pytest.raises(InvalidStatusTransitionError):
            service.update_request_status(
                request_id=request.id,
                user_id=procurement_user.id,
                user_role=procurement_user.role,
                data=RequestStatusUpdate(status=RequestStatus.OPEN),
            )

    def test_requestor_cannot_change_status(
        self, db_session, requestor_user, valid_request_data
    ):
        """Test that requestors cannot change status."""
        service = RequestService(db_session)
        request = service.create_request(
            user_id=requestor_user.id,
            data=valid_request_data,
        )

        with pytest.raises(PermissionDeniedError):
            service.update_request_status(
                request_id=request.id,
                user_id=requestor_user.id,
                user_role=requestor_user.role,
                data=RequestStatusUpdate(status=RequestStatus.IN_PROGRESS),
            )

    def test_status_history_created(
        self, db_session, requestor_user, procurement_user, valid_request_data
    ):
        """Test that status history is tracked."""
        service = RequestService(db_session)
        request = service.create_request(
            user_id=requestor_user.id,
            data=valid_request_data,
        )

        # Change status
        service.update_request_status(
            request_id=request.id,
            user_id=procurement_user.id,
            user_role=procurement_user.role,
            data=RequestStatusUpdate(
                status=RequestStatus.IN_PROGRESS,
                notes="Starting work",
            ),
        )

        # Get history
        history = service.get_status_history(
            request_id=request.id,
            user_id=procurement_user.id,
            user_role=procurement_user.role,
        )

        assert len(history) == 2  # Initial creation + status change
        assert history[0].status == RequestStatus.IN_PROGRESS
        assert history[0].notes == "Starting work"
        assert history[1].status == RequestStatus.OPEN


class TestRequestServiceUpdate:
    """Tests for request updates."""

    def test_owner_can_update(
        self, db_session, requestor_user, valid_request_data
    ):
        """Test owner can update their request."""
        service = RequestService(db_session)
        request = service.create_request(
            user_id=requestor_user.id,
            data=valid_request_data,
        )

        updated = service.update_request(
            request_id=request.id,
            user_id=requestor_user.id,
            user_role=requestor_user.role,
            data=RequestUpdate(title="Updated Title"),
        )

        assert updated.title == "Updated Title"

    def test_other_user_cannot_update(
        self, db_session, requestor_user, another_requestor, valid_request_data
    ):
        """Test other requestor cannot update."""
        service = RequestService(db_session)
        request = service.create_request(
            user_id=requestor_user.id,
            data=valid_request_data,
        )

        with pytest.raises(PermissionDeniedError):
            service.update_request(
                request_id=request.id,
                user_id=another_requestor.id,
                user_role=another_requestor.role,
                data=RequestUpdate(title="Hacked"),
            )

    def test_cannot_update_closed_request(
        self, db_session, requestor_user, procurement_user, valid_request_data
    ):
        """Test cannot update closed request."""
        service = RequestService(db_session)
        request = service.create_request(
            user_id=requestor_user.id,
            data=valid_request_data,
        )

        # Close the request
        service.update_request_status(
            request_id=request.id,
            user_id=procurement_user.id,
            user_role=procurement_user.role,
            data=RequestStatusUpdate(status=RequestStatus.CLOSED),
        )

        with pytest.raises(PermissionDeniedError) as exc_info:
            service.update_request(
                request_id=request.id,
                user_id=requestor_user.id,
                user_role=requestor_user.role,
                data=RequestUpdate(title="Updated"),
            )

        assert "closed" in str(exc_info.value).lower()


class TestRequestServiceDelete:
    """Tests for request deletion."""

    def test_owner_can_delete_open(
        self, db_session, requestor_user, valid_request_data
    ):
        """Test owner can delete their open request."""
        service = RequestService(db_session)
        request = service.create_request(
            user_id=requestor_user.id,
            data=valid_request_data,
        )

        result = service.delete_request(
            request_id=request.id,
            user_id=requestor_user.id,
            user_role=requestor_user.role,
        )

        assert result is True

        # Verify deletion
        with pytest.raises(RequestNotFoundError):
            service.get_request(
                request_id=request.id,
                user_id=requestor_user.id,
                user_role=requestor_user.role,
            )

    def test_procurement_can_delete_open(
        self, db_session, requestor_user, procurement_user, valid_request_data
    ):
        """Test procurement team can delete open requests."""
        service = RequestService(db_session)
        request = service.create_request(
            user_id=requestor_user.id,
            data=valid_request_data,
        )

        result = service.delete_request(
            request_id=request.id,
            user_id=procurement_user.id,
            user_role=procurement_user.role,
        )

        assert result is True

    def test_cannot_delete_in_progress(
        self, db_session, requestor_user, procurement_user, valid_request_data
    ):
        """Test cannot delete in_progress request."""
        service = RequestService(db_session)
        request = service.create_request(
            user_id=requestor_user.id,
            data=valid_request_data,
        )

        # Change to in_progress
        service.update_request_status(
            request_id=request.id,
            user_id=procurement_user.id,
            user_role=procurement_user.role,
            data=RequestStatusUpdate(status=RequestStatus.IN_PROGRESS),
        )

        with pytest.raises(PermissionDeniedError) as exc_info:
            service.delete_request(
                request_id=request.id,
                user_id=requestor_user.id,
                user_role=requestor_user.role,
            )

        assert "open" in str(exc_info.value).lower()

    def test_other_requestor_cannot_delete(
        self, db_session, requestor_user, another_requestor, valid_request_data
    ):
        """Test other requestor cannot delete."""
        service = RequestService(db_session)
        request = service.create_request(
            user_id=requestor_user.id,
            data=valid_request_data,
        )

        with pytest.raises(PermissionDeniedError):
            service.delete_request(
                request_id=request.id,
                user_id=another_requestor.id,
                user_role=another_requestor.role,
            )
