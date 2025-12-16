"""
User authentication models.

This module contains the SQLAlchemy model for users with authentication
and role-based access control.
"""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """User roles for access control."""

    REQUESTOR = "requestor"
    PROCUREMENT_TEAM = "procurement_team"


class User(Base):
    """
    User model for authentication and authorization.

    Attributes:
        id: Unique user identifier (UUID)
        email: User's email address (unique, used for login)
        hashed_password: Bcrypt hashed password
        full_name: User's full name
        role: User role (requestor or procurement_team)
        department: Department name (mainly for requestors)
        is_active: Whether the user account is active
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique user identifier",
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="User's email address (used for login)",
    )

    hashed_password = Column(
        String(255),
        nullable=False,
        doc="Bcrypt hashed password",
    )

    full_name = Column(
        String(255),
        nullable=False,
        doc="User's full name",
    )

    role = Column(
        Enum(UserRole, name="userrole", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=UserRole.REQUESTOR,
        doc="User role for access control",
    )

    department = Column(
        String(100),
        nullable=True,
        doc="Department name (primarily for requestors)",
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        doc="Whether the user account is active",
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        doc="Account creation timestamp",
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        doc="Last update timestamp",
    )

    # Relationships
    requests = relationship(
        "Request",
        back_populates="user",
        lazy="dynamic",
    )

    status_changes = relationship(
        "StatusHistory",
        back_populates="changed_by",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
