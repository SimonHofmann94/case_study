"""
Pytest configuration and shared fixtures for testing.

This module provides fixtures for database setup, test client, and
common test data used across all test modules.
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.auth.models import User, UserRole
from app.auth.security import hash_password

# Use PostgreSQL for testing (matches production and supports UUID)
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://procurement:procurement_pass@localhost:5432/procurement_test"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Create a fresh database session for each test.

    Yields:
        Session: Database session for testing
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    Create a test client with database session override.

    Args:
        db_session: Database session fixture

    Yields:
        TestClient: FastAPI test client
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """
    Sample user data for testing.

    Returns:
        dict: User registration data
    """
    return {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "full_name": "Test User",
        "role": "requestor",
        "department": "Engineering"
    }


@pytest.fixture
def test_procurement_user_data():
    """
    Sample procurement user data for testing.

    Returns:
        dict: Procurement user registration data
    """
    return {
        "email": "procurement@example.com",
        "password": "ProcurePass123!",
        "full_name": "Procurement User",
        "role": "procurement_team",
        "department": "Procurement"
    }


@pytest.fixture
def create_test_user(db_session):
    """
    Factory fixture to create test users in the database.

    Args:
        db_session: Database session fixture

    Returns:
        callable: Function to create test users
    """
    def _create_user(
        email: str = "user@example.com",
        password: str = "TestPass123!",
        full_name: str = "Test User",
        role: UserRole = UserRole.REQUESTOR,
        department: str = "Test Department",
        is_active: bool = True
    ) -> User:
        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=role,
            department=department,
            is_active=is_active,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _create_user
