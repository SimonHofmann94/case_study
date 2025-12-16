"""
Attachment schemas.

Pydantic models for file attachment API operations.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class AttachmentBase(BaseModel):
    """Base attachment schema with common fields."""

    filename: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Original filename",
    )
    mime_type: str = Field(
        ...,
        max_length=100,
        description="MIME type of the file",
    )
    file_size: int = Field(
        ...,
        gt=0,
        description="File size in bytes",
    )


class AttachmentCreate(AttachmentBase):
    """Schema for creating an attachment (internal use)."""

    request_id: UUID = Field(..., description="Reference to the parent request")
    file_path: str = Field(
        ...,
        max_length=500,
        description="Path to the stored file on disk",
    )


class AttachmentResponse(AttachmentBase):
    """Schema for attachment in API responses."""

    id: UUID = Field(..., description="Unique attachment identifier")
    request_id: UUID = Field(..., description="Reference to the parent request")
    uploaded_at: datetime = Field(..., description="Upload timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "880e8400-e29b-41d4-a716-446655440003",
                "request_id": "660e8400-e29b-41d4-a716-446655440001",
                "filename": "vendor_offer_2024.pdf",
                "mime_type": "application/pdf",
                "file_size": 1048576,
                "uploaded_at": "2024-01-15T10:35:00",
            }
        },
    )
