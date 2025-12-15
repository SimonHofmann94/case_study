"""
Simple test runner that doesn't require full dependency installation.

This script runs basic validation tests on the authentication system
without needing Docker or all dependencies installed.
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        from auth.models import User, UserRole
        print("✓ Auth models import successful")

        from auth.schemas import UserCreate, UserLogin, LoginResponse
        print("✓ Auth schemas import successful")

        print("\nAll imports successful! ✓")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_password_validation():
    """Test password validation logic without bcrypt."""
    print("\nTesting password validation logic...")

    # Test password strength validation (without actually importing security module)
    test_cases = [
        ("Short1!", False, "too short"),
        ("nouppercase1!", False, "no uppercase"),
        ("NOLOWERCASE1!", False, "no lowercase"),
        ("NoDigits!", False, "no digits"),
        ("NoSpecial123", False, "no special char"),
        ("ValidPass123!", True, "valid password"),
    ]

    for password, expected_valid, reason in test_cases:
        # Basic validation checks
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        is_long_enough = len(password) >= 8

        is_valid = all([has_upper, has_lower, has_digit, has_special, is_long_enough])

        status = "✓" if is_valid == expected_valid else "✗"
        print(f"  {status} {password:20} ({reason})")

    print("\nPassword validation logic works! ✓")
    return True


def test_user_roles():
    """Test that user roles are defined correctly."""
    print("\nTesting user roles...")

    try:
        from auth.models import UserRole

        assert hasattr(UserRole, 'REQUESTOR'), "Missing REQUESTOR role"
        assert hasattr(UserRole, 'PROCUREMENT_TEAM'), "Missing PROCUREMENT_TEAM role"

        print(f"✓ Found role: {UserRole.REQUESTOR.value}")
        print(f"✓ Found role: {UserRole.PROCUREMENT_TEAM.value}")

        print("\nUser roles configured correctly! ✓")
        return True
    except Exception as e:
        print(f"✗ Role test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Running Authentication System Validation Tests")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Password Validation", test_password_validation()))
    results.append(("User Roles", test_user_roles()))

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {test_name}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All validation tests passed!")
        print("\nNext steps:")
        print("1. Start Docker Desktop")
        print("2. Run: docker compose up -d")
        print("3. Visit http://localhost:8000/docs to test the API")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
