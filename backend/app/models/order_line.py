"""
Order Line model.

This module contains the SQLAlchemy model for order lines
that belong to a procurement request.
"""

from decimal import Decimal
from sqlalchemy import Column, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class OrderLine(Base):
    """
    Order Line model.

    Represents a single line item in a procurement request,
    containing product/service details and pricing.

    Attributes:
        id: Unique order line identifier (UUID)
        request_id: Reference to the parent request
        line_type: Type of line (standard, alternative, optional)
        description: Short title/header of the item/service
        detailed_description: Detailed specifications and features
        unit_price: Price per unit (net, before tax)
        amount: Quantity ordered
        unit: Unit of measurement (e.g., "pcs", "kg", "hours")
        discount_percent: Line discount percentage
        discount_amount: Calculated discount amount
        total_price: Calculated total after discount (unit_price * amount - discount)
    """

    __tablename__ = "order_lines"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique order line identifier",
    )

    request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Reference to the parent request",
    )

    line_type = Column(
        String(20),
        nullable=False,
        default="standard",
        doc="Type of line: standard (in total), alternative (not in total), optional (not in total)",
    )

    description = Column(
        String(500),
        nullable=False,
        doc="Short title/header of the item/service",
    )

    detailed_description = Column(
        Text,
        nullable=True,
        doc="Detailed specifications, features, or additional information",
    )

    unit_price = Column(
        Numeric(precision=10, scale=2),
        nullable=False,
        doc="Price per unit (net, before tax)",
    )

    amount = Column(
        Numeric(precision=10, scale=2),
        nullable=False,
        doc="Quantity ordered",
    )

    unit = Column(
        String(50),
        nullable=False,
        default="pcs",
        doc="Unit of measurement (e.g., 'pcs', 'kg', 'hours')",
    )

    discount_percent = Column(
        Numeric(precision=5, scale=2),
        nullable=True,
        doc="Line discount percentage (0-100)",
    )

    discount_amount = Column(
        Numeric(precision=12, scale=2),
        nullable=True,
        doc="Calculated discount amount",
    )

    total_price = Column(
        Numeric(precision=12, scale=2),
        nullable=False,
        doc="Line total after discount, before tax",
    )

    # Relationships
    request = relationship(
        "Request",
        back_populates="order_lines",
    )

    def __repr__(self) -> str:
        """String representation of OrderLine."""
        return f"<OrderLine(id={self.id}, type={self.line_type}, description={self.description[:30]}..., total={self.total_price})>"

    def calculate_total(self) -> Decimal:
        """Calculate and return total price based on unit_price, amount, and discount."""
        subtotal = Decimal(str(self.unit_price)) * Decimal(str(self.amount))
        if self.discount_amount:
            return subtotal - Decimal(str(self.discount_amount))
        elif self.discount_percent:
            discount = subtotal * (Decimal(str(self.discount_percent)) / Decimal("100"))
            return subtotal - discount
        return subtotal
