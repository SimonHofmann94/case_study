"""
Order Line schemas.

Pydantic models for order line API operations.
"""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator


class OrderLineBase(BaseModel):
    """Base order line schema with common fields."""

    description: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Description of the item/service",
    )
    unit_price: Decimal = Field(
        ...,
        ge=0,
        description="Price per unit",
    )
    amount: Decimal = Field(
        ...,
        gt=0,
        description="Quantity ordered",
    )
    unit: str = Field(
        default="pcs",
        max_length=50,
        description="Unit of measurement (e.g., 'pcs', 'kg', 'hours')",
    )

    @field_validator("unit_price", "amount", mode="before")
    @classmethod
    def convert_to_decimal(cls, v):
        """Convert numeric values to Decimal."""
        if v is not None:
            return Decimal(str(v))
        return v


class OrderLineCreate(OrderLineBase):
    """Schema for creating an order line."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "description": "Dell XPS 15 Laptop",
                "unit_price": "1299.99",
                "amount": "5",
                "unit": "pcs",
            }
        }
    )


class OrderLineUpdate(BaseModel):
    """Schema for updating an order line."""

    description: Optional[str] = Field(
        None,
        min_length=1,
        max_length=500,
        description="Description of the item/service",
    )
    unit_price: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Price per unit",
    )
    amount: Optional[Decimal] = Field(
        None,
        gt=0,
        description="Quantity ordered",
    )
    unit: Optional[str] = Field(
        None,
        max_length=50,
        description="Unit of measurement",
    )

    @field_validator("unit_price", "amount", mode="before")
    @classmethod
    def convert_to_decimal(cls, v):
        """Convert numeric values to Decimal."""
        if v is not None:
            return Decimal(str(v))
        return v


class OrderLineResponse(OrderLineBase):
    """Schema for order line in API responses."""

    id: UUID = Field(..., description="Unique order line identifier")
    request_id: UUID = Field(..., description="Reference to the parent request")
    total_price: Decimal = Field(..., description="Calculated total (unit_price * amount)")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "request_id": "660e8400-e29b-41d4-a716-446655440001",
                "description": "Dell XPS 15 Laptop",
                "unit_price": "1299.99",
                "amount": "5",
                "unit": "pcs",
                "total_price": "6499.95",
            }
        },
    )
