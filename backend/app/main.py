"""
Main FastAPI application entry point.

This module sets up the FastAPI application with all necessary middleware,
routers, and configuration for the Procurement AI MVP.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.utils.rate_limit import limiter

# Import all models to register them with SQLAlchemy before importing routers
# This ensures relationship strings can be resolved
from app.models import (  # noqa: F401
    User,
    CommodityGroup,
    Request as RequestModel,
    OrderLine,
    StatusHistory,
    Attachment,
)

from app.auth.router import router as auth_router
from app.routers.requests import router as requests_router
from app.routers.commodity_groups import router as commodity_groups_router
from app.routers.offers import router as offers_router

# Initialize Sentry if DSN is provided
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=1.0 if settings.ENVIRONMENT == "development" else 0.1,
        profiles_sample_rate=1.0 if settings.ENVIRONMENT == "development" else 0.1,
    )

# Create FastAPI application instance
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered procurement request management system",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Add rate limiter state to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API health check."""
    return {
        "message": "Procurement AI MVP API",
        "version": settings.APP_VERSION,
        "status": "healthy",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring and orchestration.

    Returns:
        dict: Health status information
    """
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": settings.APP_VERSION,
    }


@app.on_event("startup")
async def startup_event():
    """Actions to perform on application startup."""
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📝 Environment: {settings.ENVIRONMENT}")
    print(f"🔧 Debug mode: {settings.DEBUG}")


@app.on_event("shutdown")
async def shutdown_event():
    """Actions to perform on application shutdown."""
    print(f"👋 Shutting down {settings.APP_NAME}")


# Include routers
app.include_router(auth_router)
app.include_router(requests_router)
app.include_router(commodity_groups_router)
app.include_router(offers_router)
