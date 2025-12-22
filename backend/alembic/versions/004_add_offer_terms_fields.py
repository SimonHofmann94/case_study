"""Add offer terms and conditions fields

Revision ID: 004
Revises: 003
Create Date: 2025-12-22

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add offer metadata and terms columns to requests table
    op.add_column('requests', sa.Column('offer_date', sa.String(50), nullable=True))
    op.add_column('requests', sa.Column('payment_terms', sa.String(255), nullable=True))
    op.add_column('requests', sa.Column('delivery_terms', sa.String(255), nullable=True))
    op.add_column('requests', sa.Column('validity_period', sa.String(255), nullable=True))
    op.add_column('requests', sa.Column('warranty_terms', sa.String(255), nullable=True))
    op.add_column('requests', sa.Column('other_terms', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove terms columns from requests table
    op.drop_column('requests', 'other_terms')
    op.drop_column('requests', 'warranty_terms')
    op.drop_column('requests', 'validity_period')
    op.drop_column('requests', 'delivery_terms')
    op.drop_column('requests', 'payment_terms')
    op.drop_column('requests', 'offer_date')
