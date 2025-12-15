"""
User authentication schemas.

Pydantic models for user registration, login, and API responses.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.auth.models import UserRole


class UserBase(BaseModel):
    """Base user schema with common fields."""

    email: EmailStr = Field(..., description="User's email address")
    full_name: str = Field(..., min_length=2, max_length=255, description="User's full name")
    role: UserRole = Field(default=UserRole.REQUESTOR, description="User role")
    department: Optional[str] = Field(None, max_length=100, description="User's department")


class UserCreate(UserBase):
    """Schema for user registration."""

    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="User password (min 8 characters)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "john.doe@company.com",
                "full_name": "John Doe",
                "password": "SecurePassword123!",
                "role": "requestor",
                "department": "IT",
            }
        }
    )


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User password")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "john.doe@company.com",
                "password": "SecurePassword123!",
            }
        }
    )


class UserResponse(UserBase):
    """Schema for user data in API responses."""

    id: UUID = Field(..., description="Unique user identifier")
    is_active: bool = Field(..., description="Whether the user account is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "john.doe@company.com",
                "full_name": "John Doe",
                "role": "requestor",
                "department": "IT",
                "is_active": True,
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00",
            }
        },
    )


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token (optional)")
    token_type: str = Field(default="bearer", description="Token type")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
            }
        }
    )


class TokenData(BaseModel):
    """Schema for data extracted from JWT token."""

    user_id: Optional[UUID] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None


class LoginResponse(BaseModel):
    """Schema for login response with user data and token."""

    user: UserResponse = Field(..., description="User information")
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "email": "john.doe@company.com",
                    "full_name": "John Doe",
                    "role": "requestor",
                    "department": "IT",
                    "is_active": True,
                    "created_at": "2024-01-15T10:30:00",
                    "updated_at": "2024-01-15T10:30:00",
                },
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
            }
        }
    )
