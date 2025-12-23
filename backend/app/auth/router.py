"""
Authentication API endpoints.

This module provides REST API endpoints for user authentication:
- User registration
- User login
- User logout (token revocation)
- Current user retrieval

Security features:
- Rate limiting on login/register to prevent brute force
- Token revocation on logout
- Password strength validation
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.models import User, TokenBlacklist
from app.auth.schemas import UserCreate, UserLogin, UserResponse, LoginResponse
from app.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    validate_password_strength,
    decode_token,
)
from app.auth.dependencies import get_current_user
from app.auth.lockout import is_account_locked, record_login_attempt
from app.utils.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.

    Handles X-Forwarded-For header for requests behind proxies.

    Args:
        request: FastAPI request object

    Returns:
        str: Client IP address
    """
    # Check for forwarded header (behind proxy/load balancer)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For can contain multiple IPs; first is the client
        return forwarded.split(",")[0].strip()

    # Direct connection
    if request.client:
        return request.client.host

    return "unknown"


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
    1. Checks if account is locked (too many failed attempts)
    2. Validates email and password
    3. Records the login attempt (success or failure)
    4. Checks if user is active
    5. Generates access token
    6. Returns user data with token

    Security measures:
    - Rate limit: 10 requests per minute per IP
    - Account lockout after 5 failed attempts (configurable)
    - Lockout duration: 15 minutes (configurable)

    Args:
        credentials: User login credentials
        db: Database session

    Returns:
        LoginResponse: User data with access token

    Raises:
        HTTPException: 401 if credentials are invalid
        HTTPException: 403 if user is inactive
        HTTPException: 429 if account is locked
    """
    client_ip = get_client_ip(request)

    # Check if account is locked due to too many failed attempts
    # Why: Prevents brute-force attacks by temporarily blocking after failures
    locked, remaining_seconds = is_account_locked(db, credentials.email)
    if locked:
        remaining_minutes = (remaining_seconds // 60) + 1
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account temporarily locked due to too many failed attempts. "
                   f"Try again in {remaining_minutes} minute(s).",
            headers={"Retry-After": str(remaining_seconds)},
        )

    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()

    # Verify user exists and password is correct
    if not user or not verify_password(credentials.password, user.hashed_password):
        # Record failed attempt before responding
        # Why: Track failures even for non-existent emails to prevent enumeration
        record_login_attempt(db, credentials.email, success=False, ip_address=client_ip)

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

    # Record successful login (clears failed attempts)
    record_login_attempt(db, credentials.email, success=True, ip_address=client_ip)

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


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout user",
    description="Revoke the current access token, invalidating the session",
)
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> dict:
    """
    Logout the current user by revoking their access token.

    Why token revocation matters:
    - JWT tokens are valid until they expire
    - Without revocation, a stolen token remains usable
    - This endpoint adds the token to a blacklist
    - Subsequent requests with this token will be rejected

    How it works:
    1. Extract the token's unique ID (JTI)
    2. Add the JTI to the token_blacklist table
    3. Future requests check this table and reject blacklisted tokens

    Args:
        credentials: HTTP Bearer token from Authorization header
        db: Database session

    Returns:
        dict: Confirmation message

    Raises:
        HTTPException: 401 if token is invalid
    """
    # Decode the token to get its claims
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token metadata
    token_jti = payload.get("jti")
    user_id = payload.get("sub")
    exp_timestamp = payload.get("exp")

    # If token doesn't have JTI (old token format), still allow logout
    # but we can't blacklist it - it will expire naturally
    if not token_jti:
        return {"message": "Logged out successfully (token will expire naturally)"}

    # Check if already blacklisted
    existing = db.query(TokenBlacklist).filter(
        TokenBlacklist.token_jti == token_jti
    ).first()

    if existing:
        return {"message": "Already logged out"}

    # Calculate expiry datetime from timestamp
    expires_at = datetime.utcfromtimestamp(exp_timestamp) if exp_timestamp else datetime.utcnow()

    # Add token to blacklist
    blacklist_entry = TokenBlacklist(
        token_jti=token_jti,
        user_id=user_id,
        revoked_at=datetime.utcnow(),
        expires_at=expires_at,
        reason="logout",
    )

    db.add(blacklist_entry)
    db.commit()

    return {"message": "Logged out successfully"}
