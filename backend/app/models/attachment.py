"""
Attachment model.

This module contains the SQLAlchemy model for file attachments
associated with procurement requests.
"""

from datetime import datetime
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class Attachment(Base):
    """
    Attachment model.

    Represents a file attachment (e.g., vendor offer PDF) uploaded
    for a procurement request.

    Attributes:
        id: Unique attachment identifier (UUID)
        request_id: Reference to the parent request
        filename: Original filename
        file_path: Path to the stored file on disk
        mime_type: MIME type of the file
        file_size: File size in bytes
        uploaded_at: Upload timestamp
    """

    __tablename__ = "attachments"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique attachment identifier",
    )

    request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Reference to the parent request",
    )

    filename = Column(
        String(255),
        nullable=False,
        doc="Original filename",
    )

    file_path = Column(
        String(500),
        nullable=False,
        doc="Path to the stored file on disk",
    )

    mime_type = Column(
        String(100),
        nullable=False,
        doc="MIME type of the file",
    )

    file_size = Column(
        BigInteger,
        nullable=False,
        doc="File size in bytes",
    )

    uploaded_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        doc="Upload timestamp",
    )

    # Relationships
    request = relationship(
        "Request",
        back_populates="attachments",
    )

    def __repr__(self) -> str:
        """String representation of Attachment."""
        return f"<Attachment(id={self.id}, filename={self.filename}, size={self.file_size})>"
