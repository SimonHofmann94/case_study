"""
Authentication dependencies for FastAPI routes.

This module provides dependency functions for protecting routes and
extracting the current user from JWT tokens.

Security features:
- JWT token validation
- Token blacklist checking (for logout support)
- User active status verification
- Role-based access control
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.models import User, UserRole, TokenBlacklist
from app.auth.schemas import TokenData
from app.auth.security import decode_token

# HTTP Bearer token security scheme
security = HTTPBearer()


def is_token_blacklisted(db: Session, token_jti: str) -> bool:
    """
    Check if a token has been revoked (blacklisted).

    Why: When users log out, their token is added to the blacklist.
    We check this on every request to prevent use of revoked tokens.

    Args:
        db: Database session
        token_jti: JWT ID (unique token identifier)

    Returns:
        bool: True if token is blacklisted (should be rejected)
    """
    blacklisted = db.query(TokenBlacklist).filter(
        TokenBlacklist.token_jti == token_jti
    ).first()
    return blacklisted is not None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.

    This dependency:
    1. Extracts the JWT token from the Authorization header
    2. Validates and decodes the token
    3. Checks if the token has been revoked (logout)
    4. Fetches the user from the database
    5. Verifies the user is active

    Args:
        credentials: HTTP Bearer token from Authorization header
        db: Database session

    Returns:
        User: The authenticated user

    Raises:
        HTTPException: 401 if token is invalid, revoked, or user not found/inactive

    Example:
        @app.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"user_id": current_user.id}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Extract token from credentials
    token = credentials.credentials

    # Decode and validate token
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    # Extract user ID from token
    user_id_str: Optional[str] = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    # Check if token has been revoked (user logged out)
    # Why: Even valid tokens should be rejected if user explicitly logged out
    token_jti = payload.get("jti")
    if token_jti and is_token_blacklisted(db, token_jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    # Fetch user from database
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise credentials_exception

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to get the current active user.

    This is a convenience dependency that ensures the user is active.
    In practice, get_current_user already checks this, but this can
    be extended for additional checks.

    Args:
        current_user: User from get_current_user dependency

    Returns:
        User: The active user

    Example:
        @app.get("/me")
        async def read_users_me(current_user: User = Depends(get_current_active_user)):
            return current_user
    """
    return current_user


async def require_role(allowed_roles: list[UserRole]):
    """
    Factory function to create a dependency that checks user roles.

    Args:
        allowed_roles: List of allowed user roles

    Returns:
        Dependency function that validates user role

    Example:
        # Only procurement team can access
        @app.put("/requests/{id}/status")
        async def update_status(
            current_user: User = Depends(require_role([UserRole.PROCUREMENT_TEAM]))
        ):
            ...
    """

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{current_user.role.value}' not authorized for this operation",
            )
        return current_user

    return role_checker


def get_procurement_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to ensure current user is a procurement team member.

    Args:
        current_user: User from get_current_user dependency

    Returns:
        User: The procurement team user

    Raises:
        HTTPException: 403 if user is not procurement team

    Example:
        @app.get("/admin/requests")
        async def get_all_requests(user: User = Depends(get_procurement_user)):
            # Only procurement team can access
            ...
    """
    if current_user.role != UserRole.PROCUREMENT_TEAM:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation requires procurement team role",
        )
    return current_user


def get_requestor_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to ensure current user is a requestor.

    Args:
        current_user: User from get_current_user dependency

    Returns:
        User: The requestor user

    Raises:
        HTTPException: 403 if user is not a requestor

    Example:
        @app.post("/requests")
        async def create_request(user: User = Depends(get_requestor_user)):
            # Only requestors can create requests
            ...
    """
    if current_user.role != UserRole.REQUESTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation requires requestor role",
        )
    return current_user
