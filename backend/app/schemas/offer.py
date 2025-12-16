"""
Offer parsing schemas.

Pydantic models for AI-powered vendor offer extraction results.
"""

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator


class ParsedOrderLine(BaseModel):
    """Schema for a parsed order line from vendor offer."""

    description: str = Field(
        ...,
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
        description="Quantity",
    )
    unit: str = Field(
        default="pcs",
        description="Unit of measurement",
    )
    total_price: Optional[Decimal] = Field(
        None,
        description="Total price (may be calculated)",
    )

    @field_validator("unit_price", "amount", "total_price", mode="before")
    @classmethod
    def convert_to_decimal(cls, v):
        """Convert numeric values to Decimal."""
        if v is not None:
            return Decimal(str(v))
        return v


class ParsedVendorOffer(BaseModel):
    """Schema for parsed vendor offer data from AI extraction."""

    vendor_name: str = Field(
        ...,
        description="Extracted vendor name",
    )
    vat_id: Optional[str] = Field(
        None,
        description="Extracted VAT ID (may need validation)",
    )
    offer_date: Optional[str] = Field(
        None,
        description="Date of the offer (if found)",
    )
    offer_number: Optional[str] = Field(
        None,
        description="Offer/quote number (if found)",
    )
    order_lines: List[ParsedOrderLine] = Field(
        default=[],
        description="Extracted order lines",
    )
    total_amount: Optional[Decimal] = Field(
        None,
        description="Total amount from the offer",
    )
    currency: str = Field(
        default="EUR",
        description="Currency of the offer",
    )
    raw_text: Optional[str] = Field(
        None,
        description="Raw text extracted from the document",
    )
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score of the extraction",
    )

    @field_validator("total_amount", mode="before")
    @classmethod
    def convert_total_to_decimal(cls, v):
        """Convert total amount to Decimal."""
        if v is not None:
            return Decimal(str(v))
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "vendor_name": "Dell Technologies GmbH",
                "vat_id": "DE123456789",
                "offer_date": "2024-01-10",
                "offer_number": "QT-2024-001234",
                "order_lines": [
                    {
                        "description": "Dell XPS 15 Laptop (Intel i7, 32GB RAM, 1TB SSD)",
                        "unit_price": "1299.99",
                        "amount": "5",
                        "unit": "pcs",
                        "total_price": "6499.95",
                    },
                    {
                        "description": "Dell UltraSharp 27\" 4K Monitor",
                        "unit_price": "449.99",
                        "amount": "5",
                        "unit": "pcs",
                        "total_price": "2249.95",
                    },
                ],
                "total_amount": "8749.90",
                "currency": "EUR",
                "confidence_score": 0.95,
            }
        }
    )


class OfferParseRequest(BaseModel):
    """Schema for requesting offer parsing."""

    document_text: Optional[str] = Field(
        None,
        description="Text content of the document (if already extracted)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_text": "Vendor: Dell Technologies...",
            }
        }
    )


class OfferParseResponse(BaseModel):
    """Schema for offer parsing response."""

    vendor_name: str = Field(..., description="Extracted vendor name")
    vat_id: Optional[str] = Field(None, description="Extracted VAT ID")
    order_lines: List[ParsedOrderLine] = Field(
        default=[],
        description="Extracted order lines",
    )
    token_savings: Optional[dict] = Field(
        None,
        description="Token savings statistics when TOON format was used",
    )
    format_used: str = Field(
        default="json",
        description="Format used for parsing (toon or json)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "vendor_name": "Dell Technologies GmbH",
                "vat_id": "DE123456789",
                "order_lines": [
                    {
                        "description": "Dell XPS 15 Laptop",
                        "unit_price": "1299.99",
                        "amount": "5",
                        "unit": "pcs",
                    }
                ],
                "token_savings": {
                    "json_chars": 250,
                    "toon_chars": 150,
                    "savings_percent": 40.0,
                },
                "format_used": "toon",
            }
        }
    )
