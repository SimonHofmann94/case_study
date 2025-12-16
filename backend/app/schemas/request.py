"""
Procurement Request schemas.

Pydantic models for request API operations.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.models.request import RequestStatus
from app.schemas.order_line import OrderLineCreate, OrderLineResponse
from app.schemas.commodity_group import CommodityGroupResponse


class RequestBase(BaseModel):
    """Base request schema with common fields."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Brief title/description of the request",
    )
    vendor_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the vendor",
    )
    vat_id: str = Field(
        ...,
        min_length=11,
        max_length=20,
        pattern=r"^DE\d{9}$",
        description="VAT identification number (format: DE + 9 digits)",
    )
    department: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Department making the request",
    )
    notes: Optional[str] = Field(
        None,
        description="Optional additional notes",
    )


class RequestCreate(RequestBase):
    """Schema for creating a request."""

    commodity_group_id: Optional[UUID] = Field(
        None,
        description="Reference to the commodity group classification",
    )
    order_lines: List[OrderLineCreate] = Field(
        ...,
        min_length=1,
        description="List of order lines (at least one required)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "IT Equipment Purchase Q1 2024",
                "vendor_name": "Dell Technologies",
                "vat_id": "DE123456789",
                "department": "IT",
                "commodity_group_id": "550e8400-e29b-41d4-a716-446655440000",
                "notes": "Urgent request for new developer workstations",
                "order_lines": [
                    {
                        "description": "Dell XPS 15 Laptop",
                        "unit_price": "1299.99",
                        "amount": "5",
                        "unit": "pcs",
                    },
                    {
                        "description": "Dell UltraSharp 27\" Monitor",
                        "unit_price": "449.99",
                        "amount": "5",
                        "unit": "pcs",
                    },
                ],
            }
        }
    )


class RequestUpdate(BaseModel):
    """Schema for updating a request."""

    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Brief title/description of the request",
    )
    vendor_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Name of the vendor",
    )
    vat_id: Optional[str] = Field(
        None,
        min_length=11,
        max_length=20,
        pattern=r"^DE\d{9}$",
        description="VAT identification number",
    )
    department: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Department making the request",
    )
    commodity_group_id: Optional[UUID] = Field(
        None,
        description="Reference to the commodity group classification",
    )
    notes: Optional[str] = Field(
        None,
        description="Optional additional notes",
    )


class RequestStatusUpdate(BaseModel):
    """Schema for updating request status."""

    status: RequestStatus = Field(..., description="New status for the request")
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Notes about the status change",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "in_progress",
                "notes": "Starting procurement process, reviewing vendor qualifications",
            }
        }
    )


class RequestResponse(RequestBase):
    """Schema for request in API responses."""

    id: UUID = Field(..., description="Unique request identifier")
    user_id: UUID = Field(..., description="Reference to the user who created the request")
    commodity_group_id: Optional[UUID] = Field(
        None,
        description="Reference to the commodity group classification",
    )
    total_cost: Decimal = Field(..., description="Total cost of all order lines")
    status: RequestStatus = Field(..., description="Current status of the request")
    created_at: datetime = Field(..., description="Request creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "660e8400-e29b-41d4-a716-446655440001",
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "IT Equipment Purchase Q1 2024",
                "vendor_name": "Dell Technologies",
                "vat_id": "DE123456789",
                "department": "IT",
                "commodity_group_id": "550e8400-e29b-41d4-a716-446655440000",
                "total_cost": "8749.90",
                "status": "open",
                "notes": "Urgent request for new developer workstations",
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00",
            }
        },
    )


class RequestDetailResponse(RequestResponse):
    """Schema for detailed request in API responses (includes related data)."""

    order_lines: List[OrderLineResponse] = Field(
        default=[],
        description="List of order lines",
    )
    commodity_group: Optional[CommodityGroupResponse] = Field(
        None,
        description="Commodity group details",
    )

    model_config = ConfigDict(
        from_attributes=True,
    )


class RequestListResponse(BaseModel):
    """Schema for paginated list of requests."""

    items: List[RequestResponse] = Field(..., description="List of requests")
    total: int = Field(..., description="Total number of requests")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Number of items per page")
    pages: int = Field(..., ge=0, description="Total number of pages")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 50,
                "page": 1,
                "page_size": 10,
                "pages": 5,
            }
        }
    )
