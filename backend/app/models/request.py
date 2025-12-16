"""
Procurement Request model.

This module contains the SQLAlchemy model for procurement requests
and the RequestStatus enum for tracking request lifecycle.
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.database import Base


class RequestStatus(str, enum.Enum):
    """Status values for procurement requests."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


# Valid status transitions
VALID_STATUS_TRANSITIONS = {
    RequestStatus.OPEN: [RequestStatus.IN_PROGRESS, RequestStatus.CLOSED],
    RequestStatus.IN_PROGRESS: [RequestStatus.CLOSED, RequestStatus.OPEN],
    RequestStatus.CLOSED: [],  # Closed requests cannot be reopened
}


class Request(Base):
    """
    Procurement Request model.

    Represents a procurement request submitted by a requestor,
    containing vendor information, order lines, and status tracking.

    Attributes:
        id: Unique request identifier (UUID)
        user_id: Reference to the user who created the request
        title: Brief title/description of the request
        vendor_name: Name of the vendor
        vat_id: VAT identification number (format: DE + 9 digits)
        commodity_group_id: Reference to the commodity group classification
        department: Department making the request
        total_cost: Total cost of all order lines
        status: Current status of the request
        notes: Optional additional notes
        created_at: Request creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "requests"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique request identifier",
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Reference to the user who created the request",
    )

    title = Column(
        String(255),
        nullable=False,
        doc="Brief title/description of the request",
    )

    vendor_name = Column(
        String(255),
        nullable=False,
        doc="Name of the vendor",
    )

    vat_id = Column(
        String(20),
        nullable=False,
        doc="VAT identification number (format: DE + 9 digits)",
    )

    commodity_group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("commodity_groups.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Reference to the commodity group classification",
    )

    department = Column(
        String(100),
        nullable=False,
        doc="Department making the request",
    )

    total_cost = Column(
        Numeric(precision=12, scale=2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Total cost of all order lines",
    )

    status = Column(
        Enum(RequestStatus, name="request_status", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=RequestStatus.OPEN,
        index=True,
        doc="Current status of the request",
    )

    notes = Column(
        Text,
        nullable=True,
        doc="Optional additional notes",
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        doc="Request creation timestamp",
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        doc="Last update timestamp",
    )

    # Relationships
    user = relationship(
        "User",
        back_populates="requests",
        lazy="joined",
    )

    commodity_group = relationship(
        "CommodityGroup",
        back_populates="requests",
        lazy="joined",
    )

    order_lines = relationship(
        "OrderLine",
        back_populates="request",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    status_history = relationship(
        "StatusHistory",
        back_populates="request",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="StatusHistory.changed_at.desc()",
    )

    attachments = relationship(
        "Attachment",
        back_populates="request",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        """String representation of Request."""
        return f"<Request(id={self.id}, title={self.title}, status={self.status})>"

    def can_transition_to(self, new_status: RequestStatus) -> bool:
        """Check if transition to new_status is valid."""
        return new_status in VALID_STATUS_TRANSITIONS.get(self.status, [])
