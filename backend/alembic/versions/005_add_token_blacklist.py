"""Add token blacklist table for logout/token revocation.

This migration creates the token_blacklist table which stores revoked JWT tokens.

Why this table exists:
- JWT tokens are stateless and valid until expiry
- When users logout, we need to invalidate their token
- This table stores revoked token JTIs (JWT IDs)
- The auth system checks this table on every request

Cleanup note:
- Expired tokens can be safely deleted (expires_at < now)
- Consider a scheduled job to clean up expired entries

Revision ID: 005
Revises: 004
Create Date: 2024-01-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create token_blacklist table."""
    op.create_table(
        'token_blacklist',
        # Primary key
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            comment='Unique blacklist entry identifier'
        ),
        # Token identifier (the JWT ID claim)
        sa.Column(
            'token_jti',
            sa.String(255),
            nullable=False,
            unique=True,
            index=True,
            comment='JWT ID (jti) - unique token identifier'
        ),
        # User who owned the token
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            index=True,
            comment='User who owned the revoked token'
        ),
        # When the token was revoked
        sa.Column(
            'revoked_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.text('now()'),
            comment='When the token was revoked'
        ),
        # Original token expiry (for cleanup)
        sa.Column(
            'expires_at',
            sa.DateTime(),
            nullable=False,
            comment='Original token expiry (for cleanup)'
        ),
        # Reason for revocation
        sa.Column(
            'reason',
            sa.String(50),
            nullable=False,
            server_default='logout',
            comment='Reason for revocation: logout, password_change, security, admin'
        ),
    )

    # Index for cleanup queries (find expired tokens)
    op.create_index(
        'ix_token_blacklist_expires_at',
        'token_blacklist',
        ['expires_at']
    )


def downgrade() -> None:
    """Drop token_blacklist table."""
    op.drop_index('ix_token_blacklist_expires_at', table_name='token_blacklist')
    op.drop_table('token_blacklist')
