"""Create procurement tables

Revision ID: 002
Revises: 001
Create Date: 2024-01-16 00:00:00.000000

This migration creates:
- commodity_groups: Classification categories for requests
- requests: Main procurement request table
- order_lines: Line items for each request
- status_history: Audit trail for status changes
- attachments: File attachments (vendor offers, etc.)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all procurement-related tables."""

    # Create RequestStatus enum type (if not exists for idempotency)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'request_status') THEN
                CREATE TYPE request_status AS ENUM ('open', 'in_progress', 'closed');
            END IF;
        END$$;
    """)

    # Create commodity_groups table
    op.create_table(
        'commodity_groups',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('category', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
    )
    op.create_index('ix_commodity_groups_category', 'commodity_groups', ['category'], unique=False)

    # Create requests table
    op.create_table(
        'requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('vendor_name', sa.String(length=255), nullable=False),
        sa.Column('vat_id', sa.String(length=20), nullable=False),
        sa.Column('commodity_group_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('department', sa.String(length=100), nullable=False),
        sa.Column('total_cost', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('status', postgresql.ENUM('open', 'in_progress', 'closed', name='request_status', create_type=False), nullable=False, server_default='open'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['commodity_group_id'], ['commodity_groups.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_requests_user_id', 'requests', ['user_id'], unique=False)
    op.create_index('ix_requests_commodity_group_id', 'requests', ['commodity_group_id'], unique=False)
    op.create_index('ix_requests_status', 'requests', ['status'], unique=False)
    op.create_index('ix_requests_created_at', 'requests', ['created_at'], unique=False)

    # Create order_lines table
    op.create_table(
        'order_lines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('request_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=False, server_default='pcs'),
        sa.Column('total_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['request_id'], ['requests.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_order_lines_request_id', 'order_lines', ['request_id'], unique=False)

    # Create status_history table
    op.create_table(
        'status_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('request_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', postgresql.ENUM('open', 'in_progress', 'closed', name='request_status', create_type=False), nullable=False),
        sa.Column('changed_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('changed_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['request_id'], ['requests.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['changed_by_user_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_status_history_request_id', 'status_history', ['request_id'], unique=False)
    op.create_index('ix_status_history_changed_by_user_id', 'status_history', ['changed_by_user_id'], unique=False)
    op.create_index('ix_status_history_changed_at', 'status_history', ['changed_at'], unique=False)

    # Create attachments table
    op.create_table(
        'attachments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('request_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['request_id'], ['requests.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_attachments_request_id', 'attachments', ['request_id'], unique=False)


def downgrade() -> None:
    """Drop all procurement-related tables."""
    # Drop tables in reverse order of creation (respect foreign keys)

    # Drop attachments
    op.drop_index('ix_attachments_request_id', table_name='attachments')
    op.drop_table('attachments')

    # Drop status_history
    op.drop_index('ix_status_history_changed_at', table_name='status_history')
    op.drop_index('ix_status_history_changed_by_user_id', table_name='status_history')
    op.drop_index('ix_status_history_request_id', table_name='status_history')
    op.drop_table('status_history')

    # Drop order_lines
    op.drop_index('ix_order_lines_request_id', table_name='order_lines')
    op.drop_table('order_lines')

    # Drop requests
    op.drop_index('ix_requests_created_at', table_name='requests')
    op.drop_index('ix_requests_status', table_name='requests')
    op.drop_index('ix_requests_commodity_group_id', table_name='requests')
    op.drop_index('ix_requests_user_id', table_name='requests')
    op.drop_table('requests')

    # Drop commodity_groups
    op.drop_index('ix_commodity_groups_category', table_name='commodity_groups')
    op.drop_table('commodity_groups')

    # Drop enum type
    op.execute('DROP TYPE request_status')
