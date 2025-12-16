"""
Status History schemas.

Pydantic models for status history API operations.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.models.request import RequestStatus


class StatusHistoryBase(BaseModel):
    """Base status history schema with common fields."""

    status: RequestStatus = Field(..., description="The status that was set")
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional notes about the status change",
    )


class StatusHistoryCreate(StatusHistoryBase):
    """Schema for creating a status history entry (internal use)."""

    request_id: UUID = Field(..., description="Reference to the request")
    changed_by_user_id: UUID = Field(..., description="Reference to the user who made the change")


class StatusHistoryResponse(StatusHistoryBase):
    """Schema for status history in API responses."""

    id: UUID = Field(..., description="Unique status history entry identifier")
    request_id: UUID = Field(..., description="Reference to the request")
    changed_by_user_id: Optional[UUID] = Field(
        None,
        description="Reference to the user who made the change",
    )
    changed_at: datetime = Field(..., description="Timestamp of the status change")
    changed_by_name: Optional[str] = Field(
        None,
        description="Name of the user who made the change",
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "770e8400-e29b-41d4-a716-446655440002",
                "request_id": "660e8400-e29b-41d4-a716-446655440001",
                "status": "in_progress",
                "changed_by_user_id": "550e8400-e29b-41d4-a716-446655440000",
                "changed_at": "2024-01-16T14:30:00",
                "notes": "Starting procurement process",
                "changed_by_name": "Jane Smith",
            }
        },
    )
