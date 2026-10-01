"""Add credentials and internal access flag.

Revision ID: 0011_basic_auth
Revises: 0010_ai_review_moments
"""
from alembic import op
import sqlalchemy as sa

revision = '0011_basic_auth'
down_revision = '0010_ai_review_moments'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('users', sa.Column('password_hash', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('is_internal', sa.Boolean(), nullable=False, server_default=sa.text('false')))

def downgrade():
    op.drop_column('users', 'is_internal')
    op.drop_column('users', 'password_hash')
