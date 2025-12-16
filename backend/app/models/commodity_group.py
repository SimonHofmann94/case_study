"""
Commodity Group model.

This module contains the SQLAlchemy model for commodity groups
used for classifying procurement requests.
"""

from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class CommodityGroup(Base):
    """
    Commodity Group model for request classification.

    Based on the standard procurement commodity classification system.
    Each group has a category code (e.g., "A", "B") and a descriptive name.

    Attributes:
        id: Unique identifier (UUID)
        category: Category code (e.g., "A", "B", "C")
        name: Human-readable name of the commodity group
        description: Optional detailed description
    """

    __tablename__ = "commodity_groups"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique commodity group identifier",
    )

    category = Column(
        String(10),
        nullable=False,
        index=True,
        doc="Category code (e.g., 'A', 'B', 'C')",
    )

    name = Column(
        String(255),
        nullable=False,
        doc="Human-readable name of the commodity group",
    )

    description = Column(
        Text,
        nullable=True,
        doc="Detailed description of the commodity group",
    )

    # Relationships
    requests = relationship(
        "Request",
        back_populates="commodity_group",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        """String representation of CommodityGroup."""
        return f"<CommodityGroup(id={self.id}, category={self.category}, name={self.name})>"
