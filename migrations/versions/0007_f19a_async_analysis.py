"""Async analysis progress and thumbnails.

Revision ID: 0007_f19a_async_analysis
Revises: 0006_f16_complete_reviews
"""
from alembic import op
import sqlalchemy as sa

revision = '0007_f19a_async_analysis'
down_revision = '0006_f16_complete_reviews'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('analyses', sa.Column('thumbnail_path', sa.Text(), nullable=True))
    op.add_column('analyses', sa.Column('progress', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('analyses', sa.Column('stage', sa.String(length=32), nullable=True))
    op.create_check_constraint('ck_analyses_progress', 'analyses', 'progress >= 0 AND progress <= 100')
    op.execute("UPDATE analyses SET progress = 100 WHERE status = 'COMPLETED'")


def downgrade():
    op.drop_constraint('ck_analyses_progress', 'analyses', type_='check')
    op.drop_column('analyses', 'stage')
    op.drop_column('analyses', 'progress')
    op.drop_column('analyses', 'thumbnail_path')
