"""Add enhanced order line and offer fields

Revision ID: 003
Revises: 002
Create Date: 2025-12-20

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to order_lines table
    op.add_column('order_lines', sa.Column('line_type', sa.String(20), nullable=False, server_default='standard'))
    op.add_column('order_lines', sa.Column('detailed_description', sa.Text(), nullable=True))
    op.add_column('order_lines', sa.Column('discount_percent', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('order_lines', sa.Column('discount_amount', sa.Numeric(precision=12, scale=2), nullable=True))

    # Add new columns to requests table
    op.add_column('requests', sa.Column('currency', sa.String(3), nullable=False, server_default='EUR'))
    op.add_column('requests', sa.Column('subtotal_net', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('requests', sa.Column('discount_total', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('requests', sa.Column('delivery_cost_net', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('requests', sa.Column('delivery_tax_amount', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('requests', sa.Column('tax_rate', sa.Numeric(precision=5, scale=2), nullable=True, server_default='19.00'))
    op.add_column('requests', sa.Column('tax_amount', sa.Numeric(precision=12, scale=2), nullable=True))


def downgrade() -> None:
    # Remove columns from requests table
    op.drop_column('requests', 'tax_amount')
    op.drop_column('requests', 'tax_rate')
    op.drop_column('requests', 'delivery_tax_amount')
    op.drop_column('requests', 'delivery_cost_net')
    op.drop_column('requests', 'discount_total')
    op.drop_column('requests', 'subtotal_net')
    op.drop_column('requests', 'currency')

    # Remove columns from order_lines table
    op.drop_column('order_lines', 'discount_amount')
    op.drop_column('order_lines', 'discount_percent')
    op.drop_column('order_lines', 'detailed_description')
    op.drop_column('order_lines', 'line_type')
