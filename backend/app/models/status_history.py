"""
Status History model.

This module contains the SQLAlchemy model for tracking
status changes of procurement requests.
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.database import Base
from app.models.request import RequestStatus


class StatusHistory(Base):
    """
    Status History model.

    Tracks all status changes for a procurement request,
    providing an audit trail of who changed what and when.

    Attributes:
        id: Unique status history entry identifier (UUID)
        request_id: Reference to the request
        status: The status that was set
        changed_by_user_id: Reference to the user who made the change
        changed_at: Timestamp of the status change
        notes: Optional notes about the status change
    """

    __tablename__ = "status_history"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique status history entry identifier",
    )

    request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Reference to the request",
    )

    status = Column(
        Enum(RequestStatus, name="request_status", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        doc="The status that was set",
    )

    changed_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Reference to the user who made the change",
    )

    changed_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
        doc="Timestamp of the status change",
    )

    notes = Column(
        Text,
        nullable=True,
        doc="Optional notes about the status change",
    )

    # Relationships
    request = relationship(
        "Request",
        back_populates="status_history",
    )

    changed_by = relationship(
        "User",
        back_populates="status_changes",
        lazy="joined",
    )

    def __repr__(self) -> str:
        """String representation of StatusHistory."""
        return f"<StatusHistory(id={self.id}, status={self.status}, changed_at={self.changed_at})>"
