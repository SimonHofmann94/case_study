"""
Order Line schemas.

Pydantic models for order line API operations.
"""

from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator


class OrderLineBase(BaseModel):
    """Base order line schema with common fields."""

    line_type: Literal["standard", "alternative", "optional"] = Field(
        default="standard",
        description="Type of line: standard (in total), alternative (not in total), optional (not in total)",
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Short title/header of the item/service",
    )
    detailed_description: Optional[str] = Field(
        None,
        description="Detailed specifications, features, or additional information",
    )
    unit_price: Decimal = Field(
        ...,
        ge=0,
        description="Price per unit (net, before tax)",
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
    discount_percent: Optional[Decimal] = Field(
        None,
        ge=0,
        le=100,
        description="Line discount percentage (0-100)",
    )
    discount_amount: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Calculated discount amount",
    )

    @field_validator("unit_price", "amount", "discount_percent", "discount_amount", mode="before")
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
                "line_type": "standard",
                "description": "Dell XPS 15 Laptop",
                "detailed_description": "Intel i7, 32GB RAM, 1TB SSD, 15.6\" 4K Display",
                "unit_price": "1299.99",
                "amount": "5",
                "unit": "pcs",
                "discount_percent": "10",
            }
        }
    )


class OrderLineUpdate(BaseModel):
    """Schema for updating an order line."""

    line_type: Optional[Literal["standard", "alternative", "optional"]] = Field(
        None,
        description="Type of line",
    )
    description: Optional[str] = Field(
        None,
        min_length=1,
        max_length=500,
        description="Short title/header of the item/service",
    )
    detailed_description: Optional[str] = Field(
        None,
        description="Detailed specifications, features, or additional information",
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
    discount_percent: Optional[Decimal] = Field(
        None,
        ge=0,
        le=100,
        description="Line discount percentage (0-100)",
    )
    discount_amount: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Calculated discount amount",
    )

    @field_validator("unit_price", "amount", "discount_percent", "discount_amount", mode="before")
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
    total_price: Decimal = Field(..., description="Line total after discount, before tax")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "request_id": "660e8400-e29b-41d4-a716-446655440001",
                "line_type": "standard",
                "description": "Dell XPS 15 Laptop",
                "detailed_description": "Intel i7, 32GB RAM, 1TB SSD, 15.6\" 4K Display",
                "unit_price": "1299.99",
                "amount": "5",
                "unit": "pcs",
                "discount_percent": "10",
                "discount_amount": "649.99",
                "total_price": "5849.96",
            }
        },
    )
