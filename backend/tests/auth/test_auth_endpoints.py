"""
Tests for authentication API endpoints.

This module tests the /auth endpoints including user registration,
login, and current user retrieval.
"""

import pytest
from fastapi import status

from app.auth.models import UserRole
from app.auth.security import create_access_token


class TestRegisterEndpoint:
    """Tests for POST /auth/register endpoint."""

    def test_register_success(self, client, test_user_data):
        """Test successful user registration."""
        response = client.post("/auth/register", json=test_user_data)

        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert "user" in data
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        user = data["user"]
        assert user["email"] == test_user_data["email"]
        assert user["full_name"] == test_user_data["full_name"]
        assert user["role"] == test_user_data["role"]
        assert user["department"] == test_user_data["department"]
        assert user["is_active"] is True
        assert "id" in user
        assert "created_at" in user
        assert "updated_at" in user

        # Ensure password is not returned
        assert "password" not in user
        assert "hashed_password" not in user

    def test_register_duplicate_email(self, client, test_user_data):
        """Test registration fails with duplicate email."""
        # Register first user
        client.post("/auth/register", json=test_user_data)

        # Try to register again with same email
        response = client.post("/auth/register", json=test_user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"].lower()

    def test_register_weak_password(self, client, test_user_data):
        """Test registration fails with weak password."""
        test_user_data["password"] = "weak"

        response = client.post("/auth/register", json=test_user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client, test_user_data):
        """Test registration fails with invalid email format."""
        test_user_data["email"] = "not-an-email"

        response = client.post("/auth/register", json=test_user_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_missing_fields(self, client):
        """Test registration fails with missing required fields."""
        incomplete_data = {
            "email": "test@example.com",
            # missing password, full_name, role
        }

        response = client.post("/auth/register", json=incomplete_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_procurement_user(self, client, test_procurement_user_data):
        """Test registration of procurement team user."""
        response = client.post("/auth/register", json=test_procurement_user_data)

        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["user"]["role"] == "procurement_team"


class TestLoginEndpoint:
    """Tests for POST /auth/login endpoint."""

    def test_login_success(self, client, test_user_data, create_test_user):
        """Test successful user login."""
        # Create user first
        create_test_user(
            email=test_user_data["email"],
            password=test_user_data["password"],
            full_name=test_user_data["full_name"],
            role=UserRole.REQUESTOR,
        )

        # Login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
        }
        response = client.post("/auth/login", json=login_data)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "user" in data
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        user = data["user"]
        assert user["email"] == test_user_data["email"]
        assert user["full_name"] == test_user_data["full_name"]

    def test_login_wrong_password(self, client, test_user_data, create_test_user):
        """Test login fails with incorrect password."""
        # Create user
        create_test_user(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )

        # Try to login with wrong password
        login_data = {
            "email": test_user_data["email"],
            "password": "WrongPassword123!",
        }
        response = client.post("/auth/login", json=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        """Test login fails for non-existent user."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "SomePassword123!",
        }
        response = client.post("/auth/login", json=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_inactive_user(self, client, test_user_data, create_test_user):
        """Test login fails for inactive user."""
        # Create inactive user
        create_test_user(
            email=test_user_data["email"],
            password=test_user_data["password"],
            is_active=False,
        )

        # Try to login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
        }
        response = client.post("/auth/login", json=login_data)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "inactive" in response.json()["detail"].lower()

    def test_login_invalid_email_format(self, client):
        """Test login fails with invalid email format."""
        login_data = {
            "email": "not-an-email",
            "password": "SomePassword123!",
        }
        response = client.post("/auth/login", json=login_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetMeEndpoint:
    """Tests for GET /auth/me endpoint."""

    def test_get_me_success(self, client, create_test_user):
        """Test successful retrieval of current user."""
        # Create user
        user = create_test_user(
            email="test@example.com",
            password="TestPass123!",
            full_name="Test User",
            role=UserRole.REQUESTOR,
        )

        # Generate token
        token = create_access_token(user.id, user.email, user.role)

        # Get current user
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["email"] == user.email
        assert data["full_name"] == user.full_name
        assert data["role"] == user.role.value
        assert "id" in data
        assert "created_at" in data

    def test_get_me_no_token(self, client):
        """Test /auth/me fails without authentication token."""
        response = client.get("/auth/me")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_me_invalid_token(self, client):
        """Test /auth/me fails with invalid token."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_me_inactive_user(self, client, create_test_user):
        """Test /auth/me fails for inactive user even with valid token."""
        # Create user
        user = create_test_user(
            email="test@example.com",
            password="TestPass123!",
            is_active=True,
        )

        # Generate token while user is active
        token = create_access_token(user.id, user.email, user.role)

        # Deactivate user
        user.is_active = False
        from tests.conftest import TestingSessionLocal
        session = TestingSessionLocal()
        session.add(user)
        session.commit()

        # Try to get user info
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "inactive" in response.json()["detail"].lower()

    def test_get_me_procurement_user(self, client, create_test_user):
        """Test /auth/me works for procurement team user."""
        # Create procurement user
        user = create_test_user(
            email="procurement@example.com",
            password="ProcurePass123!",
            role=UserRole.PROCUREMENT_TEAM,
        )

        # Generate token
        token = create_access_token(user.id, user.email, user.role)

        # Get current user
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["role"] == "procurement_team"
