"""
Offer parsing schemas.

Pydantic models for AI-powered vendor offer extraction results.
"""

from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator


class ParsedOrderLine(BaseModel):
    """Schema for a parsed order line from vendor offer."""

    line_type: Literal["standard", "alternative", "optional"] = Field(
        default="standard",
        description="Type of line: standard (in total), alternative (not in total), optional (not in total)",
    )
    description: str = Field(
        ...,
        description="Short title/header of the item/service",
    )
    detailed_description: Optional[str] = Field(
        None,
        description="Detailed specifications, features, or additional info",
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
    unit_price_net: Decimal = Field(
        ...,
        ge=0,
        description="Price per unit before tax",
        alias="unit_price",
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
    line_total_net: Optional[Decimal] = Field(
        None,
        description="Line total after discount, before tax",
        alias="total_price",
    )

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("unit_price_net", "amount", "line_total_net", "discount_percent", "discount_amount", mode="before")
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
    currency: str = Field(
        default="EUR",
        description="Currency of the offer",
    )
    order_lines: List[ParsedOrderLine] = Field(
        default=[],
        description="Extracted order lines",
    )

    # Totals section
    subtotal_net: Optional[Decimal] = Field(
        None,
        description="Sum of standard line totals before tax",
    )
    discount_total: Optional[Decimal] = Field(
        None,
        description="Offer-wide discount amount",
    )
    delivery_cost_net: Optional[Decimal] = Field(
        None,
        description="Delivery/shipping cost before tax",
    )
    delivery_tax_amount: Optional[Decimal] = Field(
        None,
        description="Tax amount on delivery",
    )
    tax_rate: Optional[Decimal] = Field(
        default=Decimal("19.00"),
        description="Tax rate percentage (default 19% for Germany)",
    )
    tax_amount: Optional[Decimal] = Field(
        None,
        description="Tax amount on items",
    )
    total_gross: Optional[Decimal] = Field(
        None,
        description="Total amount including all taxes",
        alias="total_amount",
    )

    # Terms and Conditions
    payment_terms: Optional[str] = Field(
        None,
        description="Payment terms (e.g., '30 days net')",
    )
    delivery_terms: Optional[str] = Field(
        None,
        description="Delivery time or terms (e.g., '2-3 weeks')",
    )
    validity_period: Optional[str] = Field(
        None,
        description="How long the offer is valid",
    )
    warranty_terms: Optional[str] = Field(
        None,
        description="Warranty information",
    )
    other_terms: Optional[str] = Field(
        None,
        description="Any other important terms or conditions",
    )

    # Metadata
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

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "vendor_name": "Dell Technologies GmbH",
                "vat_id": "DE123456789",
                "offer_date": "2024-01-10",
                "offer_number": "QT-2024-001234",
                "currency": "EUR",
                "order_lines": [
                    {
                        "line_type": "standard",
                        "description": "Dell XPS 15 Laptop",
                        "detailed_description": "Intel i7, 32GB RAM, 1TB SSD, 15.6\" 4K Display",
                        "unit_price_net": "1299.99",
                        "amount": "5",
                        "unit": "pcs",
                        "discount_percent": "10",
                        "discount_amount": "649.99",
                        "line_total_net": "5849.96",
                    },
                    {
                        "line_type": "alternative",
                        "description": "Dell XPS 17 Laptop (Alternative)",
                        "detailed_description": "Intel i9, 64GB RAM, 2TB SSD, 17\" 4K Display",
                        "unit_price_net": "2499.99",
                        "amount": "5",
                        "unit": "pcs",
                        "line_total_net": "12499.95",
                    },
                ],
                "subtotal_net": "5849.96",
                "discount_total": None,
                "delivery_cost_net": "49.99",
                "delivery_tax_amount": "9.50",
                "tax_rate": "19.00",
                "tax_amount": "1111.49",
                "total_gross": "7020.94",
                "confidence_score": 0.95,
            }
        }
    )

    @field_validator(
        "subtotal_net", "discount_total", "delivery_cost_net", "delivery_tax_amount",
        "tax_rate", "tax_amount", "total_gross", mode="before"
    )
    @classmethod
    def convert_totals_to_decimal(cls, v):
        """Convert total amounts to Decimal."""
        if v is not None:
            return Decimal(str(v))
        return v


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
    offer_date: Optional[str] = Field(None, description="Date of the vendor offer")
    offer_number: Optional[str] = Field(None, description="Vendor's offer/quote reference number")
    currency: str = Field(default="EUR", description="Currency of the offer")
    order_lines: List[ParsedOrderLine] = Field(
        default=[],
        description="Extracted order lines",
    )

    # Totals
    subtotal_net: Optional[Decimal] = Field(
        None,
        description="Sum of standard line totals before tax",
    )
    discount_total: Optional[Decimal] = Field(
        None,
        description="Offer-wide discount amount",
    )
    delivery_cost_net: Optional[Decimal] = Field(
        None,
        description="Delivery/shipping cost before tax",
    )
    delivery_tax_amount: Optional[Decimal] = Field(
        None,
        description="Tax amount on delivery",
    )
    tax_rate: Optional[Decimal] = Field(
        None,
        description="Tax rate percentage",
    )
    tax_amount: Optional[Decimal] = Field(
        None,
        description="Tax amount on items",
    )
    total_gross: Optional[Decimal] = Field(
        None,
        description="Total amount including all taxes",
    )

    # Terms and Conditions
    payment_terms: Optional[str] = Field(
        None,
        description="Payment terms (e.g., '30 days net')",
    )
    delivery_terms: Optional[str] = Field(
        None,
        description="Delivery time or terms (e.g., '2-3 weeks')",
    )
    validity_period: Optional[str] = Field(
        None,
        description="How long the offer is valid",
    )
    warranty_terms: Optional[str] = Field(
        None,
        description="Warranty information",
    )
    other_terms: Optional[str] = Field(
        None,
        description="Any other important terms or conditions",
    )

    # Metadata
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
                "currency": "EUR",
                "order_lines": [
                    {
                        "line_type": "standard",
                        "description": "Dell XPS 15 Laptop",
                        "detailed_description": "Intel i7, 32GB RAM, 1TB SSD",
                        "unit_price_net": "1299.99",
                        "amount": "5",
                        "unit": "pcs",
                        "line_total_net": "6499.95",
                    }
                ],
                "subtotal_net": "6499.95",
                "delivery_cost_net": "49.99",
                "delivery_tax_amount": "9.50",
                "tax_rate": "19.00",
                "tax_amount": "1234.99",
                "total_gross": "7794.43",
                "token_savings": {
                    "json_chars": 250,
                    "toon_chars": 150,
                    "savings_percent": 40.0,
                },
                "format_used": "toon",
            }
        }
    )
