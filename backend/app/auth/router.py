"""
Authentication API endpoints.

This module provides REST API endpoints for user authentication:
- User registration
- User login
- Current user retrieval
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.models import User
from app.auth.schemas import UserCreate, UserLogin, UserResponse, LoginResponse
from app.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    validate_password_strength,
)
from app.auth.dependencies import get_current_user
from app.utils.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=LoginResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email, password, and role",
)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db),
) -> LoginResponse:
    """
    Register a new user account.

    This endpoint:
    1. Validates password strength
    2. Checks if email already exists
    3. Hashes the password
    4. Creates the user in database
    5. Generates access token
    6. Returns user data with token

    Rate limit: 5 requests per minute per IP

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        LoginResponse: User data with access token

    Raises:
        HTTPException: 400 if email already exists or password is weak
    """
    # Validate password strength
    is_valid, error_message = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message,
        )

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    hashed_pw = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_pw,
        full_name=user_data.full_name,
        role=user_data.role,
        department=user_data.department,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate access token
    access_token = create_access_token(
        user_id=new_user.id,
        email=new_user.email,
        role=new_user.role,
    )

    # Prepare response
    user_response = UserResponse(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role,
        department=new_user.department,
        is_active=new_user.is_active,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at,
    )

    return LoginResponse(
        user=user_response,
        access_token=access_token,
        token_type="bearer",
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login user",
    description="Authenticate user with email and password",
)
@limiter.limit("10/minute")
async def login(
    request: Request,
    credentials: UserLogin,
    db: Session = Depends(get_db),
) -> LoginResponse:
    """
    Authenticate a user and return access token.

    This endpoint:
    1. Validates email and password
    2. Checks if user is active
    3. Generates access token
    4. Returns user data with token

    Rate limit: 10 requests per minute per IP

    Args:
        credentials: User login credentials
        db: Database session

    Returns:
        LoginResponse: User data with access token

    Raises:
        HTTPException: 401 if credentials are invalid or user is inactive
    """
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()

    # Verify user exists and password is correct
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Generate access token
    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role,
    )

    # Prepare response
    user_response = UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        department=user.department,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )

    return LoginResponse(
        user=user_response,
        access_token=access_token,
        token_type="bearer",
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the currently authenticated user's information",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Get current authenticated user information.

    This endpoint is protected and requires a valid JWT token.

    Args:
        current_user: Current authenticated user from JWT token

    Returns:
        UserResponse: Current user information
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        department=current_user.department,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )
