"""Add login_attempts table for account lockout.

This migration creates the login_attempts table which tracks failed
login attempts for account lockout functionality.

Why this table exists:
- Prevents brute-force password attacks
- Tracks failed attempts per email/IP
- Enables temporary account lockout after threshold

Configuration (in app/config.py):
- MAX_LOGIN_ATTEMPTS: Failures before lockout (default: 5)
- LOCKOUT_DURATION_MINUTES: Lockout duration (default: 15)
- LOCKOUT_WINDOW_MINUTES: Window for counting (default: 15)

Cleanup note:
- Old records can be safely deleted after 7 days
- Consider a scheduled job to clean up old entries

Revision ID: 006
Revises: 005
Create Date: 2024-01-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create login_attempts table."""
    op.create_table(
        'login_attempts',
        # Primary key
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            comment='Unique attempt identifier'
        ),
        # Email used in attempt
        sa.Column(
            'email',
            sa.String(255),
            nullable=False,
            index=True,
            comment='Email address used in login attempt'
        ),
        # IP address of attempt
        sa.Column(
            'ip_address',
            sa.String(45),  # IPv6 can be up to 45 chars
            nullable=True,
            index=True,
            comment='IP address of the attempt'
        ),
        # When the attempt occurred
        sa.Column(
            'attempted_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.text('now()'),
            index=True,
            comment='When the attempt occurred'
        ),
        # Whether it was successful
        sa.Column(
            'success',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false'),
            comment='Whether the login was successful'
        ),
    )


def downgrade() -> None:
    """Drop login_attempts table."""
    op.drop_table('login_attempts')
