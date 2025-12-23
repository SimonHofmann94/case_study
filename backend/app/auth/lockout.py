"""
Account lockout service.

This module provides protection against brute-force login attacks by:
1. Tracking failed login attempts per email
2. Temporarily locking accounts after too many failures
3. Resetting attempt counts on successful login

How it works:
- Each failed login creates a LoginAttempt record
- Before login, we check recent failure count
- If count >= threshold, reject login with lockout message
- Successful login clears the attempt history

Configuration (in config.py):
- MAX_LOGIN_ATTEMPTS: Number of failures before lockout (default: 5)
- LOCKOUT_DURATION_MINUTES: How long to lock the account (default: 15)
- LOCKOUT_WINDOW_MINUTES: Time window for counting attempts (default: 15)
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import settings
from app.auth.models import LoginAttempt

logger = logging.getLogger(__name__)


def get_recent_failed_attempts(db: Session, email: str) -> int:
    """
    Count recent failed login attempts for an email.

    Args:
        db: Database session
        email: Email address to check

    Returns:
        int: Number of failed attempts in the lockout window
    """
    window_start = datetime.utcnow() - timedelta(minutes=settings.LOCKOUT_WINDOW_MINUTES)

    count = db.query(func.count(LoginAttempt.id)).filter(
        LoginAttempt.email == email.lower(),
        LoginAttempt.success == False,
        LoginAttempt.attempted_at >= window_start,
    ).scalar()

    return count or 0


def get_lockout_remaining_seconds(db: Session, email: str) -> int:
    """
    Check if an account is locked and return remaining lockout time.

    Args:
        db: Database session
        email: Email address to check

    Returns:
        int: Seconds remaining in lockout (0 if not locked)
    """
    failed_count = get_recent_failed_attempts(db, email)

    if failed_count < settings.MAX_LOGIN_ATTEMPTS:
        return 0

    # Find the most recent failed attempt
    latest_attempt = db.query(LoginAttempt).filter(
        LoginAttempt.email == email.lower(),
        LoginAttempt.success == False,
    ).order_by(LoginAttempt.attempted_at.desc()).first()

    if not latest_attempt:
        return 0

    # Calculate lockout end time
    lockout_end = latest_attempt.attempted_at + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
    remaining = (lockout_end - datetime.utcnow()).total_seconds()

    return max(0, int(remaining))


def is_account_locked(db: Session, email: str) -> Tuple[bool, Optional[int]]:
    """
    Check if an account is currently locked.

    Args:
        db: Database session
        email: Email address to check

    Returns:
        Tuple[bool, Optional[int]]: (is_locked, remaining_seconds)
    """
    remaining = get_lockout_remaining_seconds(db, email)

    if remaining > 0:
        logger.warning(f"Account locked for {email}: {remaining} seconds remaining")
        return True, remaining

    return False, None


def record_login_attempt(
    db: Session,
    email: str,
    success: bool,
    ip_address: Optional[str] = None,
) -> None:
    """
    Record a login attempt.

    On success: Clear all previous failed attempts for this email
    On failure: Add a new failed attempt record

    Args:
        db: Database session
        email: Email address used
        success: Whether the login was successful
        ip_address: IP address of the attempt
    """
    email_lower = email.lower()

    if success:
        # Clear failed attempts on successful login
        # Why: User proved they know the password, reset the counter
        db.query(LoginAttempt).filter(
            LoginAttempt.email == email_lower,
            LoginAttempt.success == False,
        ).delete()

        logger.info(f"Cleared failed login attempts for {email_lower} after successful login")
    else:
        # Record the failed attempt
        attempt = LoginAttempt(
            email=email_lower,
            ip_address=ip_address,
            attempted_at=datetime.utcnow(),
            success=False,
        )
        db.add(attempt)

        # Log warning if approaching lockout
        failed_count = get_recent_failed_attempts(db, email_lower) + 1
        remaining = settings.MAX_LOGIN_ATTEMPTS - failed_count

        if remaining <= 2:
            logger.warning(
                f"Failed login for {email_lower} from {ip_address}. "
                f"{remaining} attempts remaining before lockout."
            )

    db.commit()


def cleanup_old_attempts(db: Session, older_than_days: int = 7) -> int:
    """
    Clean up old login attempt records.

    Why: Prevent table from growing indefinitely.
    Should be called periodically (e.g., daily via scheduled task).

    Args:
        db: Database session
        older_than_days: Delete records older than this many days

    Returns:
        int: Number of records deleted
    """
    cutoff = datetime.utcnow() - timedelta(days=older_than_days)

    deleted = db.query(LoginAttempt).filter(
        LoginAttempt.attempted_at < cutoff
    ).delete()

    db.commit()

    logger.info(f"Cleaned up {deleted} old login attempt records")

    return deleted
