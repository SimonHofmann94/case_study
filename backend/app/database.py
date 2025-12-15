"""
Database configuration and session management.

This module sets up SQLAlchemy with async support for PostgreSQL.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,  # Connection pool size
    max_overflow=20,  # Max connections beyond pool_size
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for all database models
Base = declarative_base()


def get_db():
    """
    Dependency for getting database sessions.

    Yields:
        Session: SQLAlchemy database session

    Example:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.

    This function creates all tables defined in SQLAlchemy models.
    In production, use Alembic migrations instead.
    """
    from app.models import user  # noqa: F401 - Import to register models

    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
