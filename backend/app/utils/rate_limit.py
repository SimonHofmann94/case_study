"""
Rate limiting utilities using slowapi.

This module provides a shared rate limiter instance that can be used
across the application for API endpoint rate limiting.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Shared rate limiter instance
# Uses client IP address as the key for rate limiting
limiter = Limiter(key_func=get_remote_address)
