"""
Order Line model.

This module contains the SQLAlchemy model for order lines
that belong to a procurement request.
"""

from decimal import Decimal
from sqlalchemy import Column, ForeignKey, Numeric, String
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
        description: Description of the item/service
        unit_price: Price per unit
        amount: Quantity ordered
        unit: Unit of measurement (e.g., "pcs", "kg", "hours")
        total_price: Calculated total (unit_price * amount)
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

    description = Column(
        String(500),
        nullable=False,
        doc="Description of the item/service",
    )

    unit_price = Column(
        Numeric(precision=10, scale=2),
        nullable=False,
        doc="Price per unit",
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

    total_price = Column(
        Numeric(precision=12, scale=2),
        nullable=False,
        doc="Calculated total (unit_price * amount)",
    )

    # Relationships
    request = relationship(
        "Request",
        back_populates="order_lines",
    )

    def __repr__(self) -> str:
        """String representation of OrderLine."""
        return f"<OrderLine(id={self.id}, description={self.description[:30]}..., total={self.total_price})>"

    def calculate_total(self) -> Decimal:
        """Calculate and return total price based on unit_price and amount."""
        return Decimal(str(self.unit_price)) * Decimal(str(self.amount))
