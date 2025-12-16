"""Create users table

Revision ID: 001
Revises:
Create Date: 2024-01-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create users table with all necessary columns and constraints."""
    # Create UserRole enum type (if not exists for idempotency)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole') THEN
                CREATE TYPE userrole AS ENUM ('requestor', 'procurement_team');
            END IF;
        END$$;
    """)

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', postgresql.ENUM('requestor', 'procurement_team', name='userrole', create_type=False), nullable=False),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )

    # Create index on email for faster lookups
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Create index on role for faster role-based queries
    op.create_index('ix_users_role', 'users', ['role'], unique=False)


def downgrade() -> None:
    """Drop users table and enum type."""
    # Drop indexes first
    op.drop_index('ix_users_role', table_name='users')
    op.drop_index('ix_users_email', table_name='users')

    # Drop table
    op.drop_table('users')

    # Drop enum type
    op.execute('DROP TYPE userrole')
