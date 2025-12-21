"""
Commodity Group schemas.

Pydantic models for commodity group API operations.
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class CommodityGroupBase(BaseModel):
    """Base commodity group schema with common fields."""

    category: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Category code (e.g., 'A', 'B', 'C')",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable name of the commodity group",
    )
    description: Optional[str] = Field(
        None,
        description="Detailed description of the commodity group",
    )


class CommodityGroupCreate(CommodityGroupBase):
    """Schema for creating a commodity group."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category": "A",
                "name": "Office Supplies",
                "description": "General office supplies including stationery, paper, and basic equipment",
            }
        }
    )


class CommodityGroupUpdate(BaseModel):
    """Schema for updating a commodity group."""

    category: Optional[str] = Field(
        None,
        min_length=1,
        max_length=10,
        description="Category code",
    )
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Human-readable name",
    )
    description: Optional[str] = Field(
        None,
        description="Detailed description",
    )


class CommodityGroupResponse(CommodityGroupBase):
    """Schema for commodity group in API responses."""

    id: UUID = Field(..., description="Unique commodity group identifier")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "category": "A",
                "name": "Office Supplies",
                "description": "General office supplies including stationery, paper, and basic equipment",
            }
        },
    )


class CommodityGroupSuggestion(BaseModel):
    """Schema for AI-suggested commodity group."""

    commodity_group_id: Optional[UUID] = Field(
        None,
        description="Suggested commodity group ID (may be None if not found)",
    )
    category: str = Field(..., description="Category code of the suggestion")
    name: str = Field(..., description="Name of the suggested commodity group")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0)",
    )
    explanation: str = Field(..., description="Explanation for the suggestion")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "commodity_group_id": "550e8400-e29b-41d4-a716-446655440000",
                "category": "A",
                "name": "IT Equipment",
                "confidence": 0.92,
                "explanation": "Based on the order lines containing laptops and monitors, this request fits best in the IT Equipment category.",
            }
        }
    )


class CommoditySuggestionRequest(BaseModel):
    """Schema for requesting commodity group suggestion."""

    title: str = Field(..., description="Request title")
    order_lines: list = Field(..., description="List of order line dictionaries")
    vendor_name: Optional[str] = Field(None, description="Vendor name if available")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Office Equipment Purchase",
                "order_lines": [
                    {"description": "Dell XPS 15 Laptop", "unit_price": 1299.99, "amount": 5}
                ],
                "vendor_name": "Dell Technologies"
            }
        }
    )
