"""
Tests for authentication security utilities.

This module tests password hashing, verification, JWT token generation,
and token decoding functionality.
"""

import pytest
from datetime import timedelta
from uuid import uuid4

from app.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    validate_password_strength,
)
from app.auth.models import UserRole


class TestPasswordHashing:
    """Tests for password hashing and verification."""

    def test_hash_password(self):
        """Test that password hashing produces a different string."""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_different_hashes(self):
        """Test that same password produces different hashes (due to salt)."""
        password = "SecurePassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "SecurePassword123!"
        wrong_password = "WrongPassword123!"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty(self):
        """Test password verification with empty password."""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert verify_password("", hashed) is False


class TestPasswordValidation:
    """Tests for password strength validation."""

    def test_validate_password_valid(self):
        """Test validation of a strong password."""
        is_valid, message = validate_password_strength("SecurePass123!")

        assert is_valid is True
        assert message == "Password is valid"

    def test_validate_password_too_short(self):
        """Test validation fails for password too short."""
        is_valid, message = validate_password_strength("Short1!")

        assert is_valid is False
        assert "at least 8 characters" in message

    def test_validate_password_no_uppercase(self):
        """Test validation fails without uppercase letter."""
        is_valid, message = validate_password_strength("lowercase123!")

        assert is_valid is False
        assert "uppercase letter" in message

    def test_validate_password_no_lowercase(self):
        """Test validation fails without lowercase letter."""
        is_valid, message = validate_password_strength("UPPERCASE123!")

        assert is_valid is False
        assert "lowercase letter" in message

    def test_validate_password_no_digit(self):
        """Test validation fails without digit."""
        is_valid, message = validate_password_strength("NoDigitsHere!")

        assert is_valid is False
        assert "digit" in message

    def test_validate_password_no_special(self):
        """Test validation fails without special character."""
        is_valid, message = validate_password_strength("NoSpecial123")

        assert is_valid is False
        assert "special character" in message


class TestJWTTokens:
    """Tests for JWT token generation and decoding."""

    def test_create_access_token(self):
        """Test JWT token creation."""
        user_id = uuid4()
        email = "test@example.com"
        role = UserRole.REQUESTOR

        token = create_access_token(user_id, email, role)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_token_valid(self):
        """Test decoding a valid JWT token."""
        user_id = uuid4()
        email = "test@example.com"
        role = UserRole.REQUESTOR

        token = create_access_token(user_id, email, role)
        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["email"] == email
        assert payload["role"] == role.value
        assert "exp" in payload
        assert "iat" in payload

    def test_decode_token_invalid(self):
        """Test decoding an invalid JWT token."""
        invalid_token = "invalid.token.here"

        payload = decode_token(invalid_token)

        assert payload is None

    def test_decode_token_expired(self):
        """Test decoding an expired JWT token."""
        user_id = uuid4()
        email = "test@example.com"
        role = UserRole.REQUESTOR

        # Create token that expires immediately
        token = create_access_token(
            user_id,
            email,
            role,
            expires_delta=timedelta(seconds=-1)
        )

        payload = decode_token(token)

        # Should return None for expired token
        assert payload is None

    def test_token_contains_correct_claims(self):
        """Test that token contains all required claims."""
        user_id = uuid4()
        email = "test@example.com"
        role = UserRole.PROCUREMENT_TEAM

        token = create_access_token(user_id, email, role)
        payload = decode_token(token)

        assert payload is not None
        assert "sub" in payload  # subject (user_id)
        assert "email" in payload
        assert "role" in payload
        assert "exp" in payload  # expiration
        assert "iat" in payload  # issued at

    def test_different_roles_in_token(self):
        """Test token generation for different user roles."""
        user_id = uuid4()
        email = "test@example.com"

        # Test requestor role
        token_requestor = create_access_token(user_id, email, UserRole.REQUESTOR)
        payload_requestor = decode_token(token_requestor)
        assert payload_requestor["role"] == "requestor"

        # Test procurement team role
        token_procurement = create_access_token(user_id, email, UserRole.PROCUREMENT_TEAM)
        payload_procurement = decode_token(token_procurement)
        assert payload_procurement["role"] == "procurement_team"
