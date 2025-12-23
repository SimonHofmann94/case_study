"""
User authentication models.

This module contains the SQLAlchemy models for users with authentication,
role-based access control, and token management.

Models:
- User: User accounts with authentication
- TokenBlacklist: Revoked JWT tokens for logout functionality
"""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Enum, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """User roles for access control."""

    REQUESTOR = "requestor"
    PROCUREMENT_TEAM = "procurement_team"


class LoginAttempt(Base):
    """
    Track failed login attempts for account lockout.

    Why this exists:
    - Brute-force attacks try many passwords rapidly
    - Rate limiting alone isn't enough (attackers use multiple IPs)
    - This tracks attempts per user/IP combination
    - After threshold, account is temporarily locked

    Security considerations:
    - Lock accounts after N failed attempts (default: 5)
    - Lockout duration increases with repeated lockouts
    - Successful login resets the counter
    - Clean up old records periodically

    Attributes:
        id: Unique identifier for the attempt record
        email: Email address used (for tracking before user lookup)
        ip_address: IP address of the attempt
        attempted_at: When the attempt occurred
        success: Whether the attempt was successful
    """

    __tablename__ = "login_attempts"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique attempt identifier",
    )

    email = Column(
        String(255),
        nullable=False,
        index=True,
        doc="Email address used in login attempt",
    )

    ip_address = Column(
        String(45),  # IPv6 can be up to 45 chars
        nullable=True,
        index=True,
        doc="IP address of the attempt",
    )

    attempted_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
        doc="When the attempt occurred",
    )

    success = Column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether the login was successful",
    )


class TokenBlacklist(Base):
    """
    Blacklisted (revoked) JWT tokens.

    Why this exists:
    - JWT tokens are stateless and valid until expiry
    - When a user logs out, we need to invalidate their token
    - This table stores revoked tokens so we can reject them
    - Tokens are automatically cleaned up after expiry via scheduled task

    Security considerations:
    - Check this table on every authenticated request
    - Clean up expired tokens periodically to prevent table bloat
    - Store token JTI (unique ID) rather than full token for space efficiency

    Attributes:
        id: Unique identifier for the blacklist entry
        token_jti: JWT ID (jti claim) - unique identifier for the token
        user_id: User who owned the token (for audit purposes)
        revoked_at: When the token was revoked
        expires_at: When the token would have expired (for cleanup)
        reason: Why the token was revoked (logout, password_change, etc.)
    """

    __tablename__ = "token_blacklist"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique blacklist entry identifier",
    )

    token_jti = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        doc="JWT ID (jti) - unique token identifier",
    )

    user_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        doc="User who owned the revoked token",
    )

    revoked_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        doc="When the token was revoked",
    )

    expires_at = Column(
        DateTime,
        nullable=False,
        doc="Original token expiry (for cleanup)",
    )

    reason = Column(
        String(50),
        nullable=False,
        default="logout",
        doc="Reason for revocation: logout, password_change, security, admin",
    )

    # Index for cleanup queries (find expired tokens)
    __table_args__ = (
        Index("ix_token_blacklist_expires_at", "expires_at"),
    )


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
