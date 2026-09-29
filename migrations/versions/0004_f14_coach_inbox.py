"""F1.4 coach inbox state.

Revision ID: 0004_f14_coach_inbox
Revises: 0003_f13_coach_requests
"""
from alembic import op
import sqlalchemy as sa

revision = '0004_f14_coach_inbox'
down_revision = '0003_f13_coach_requests'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index('uq_reviews_active_analysis_coach', table_name='reviews')
    op.drop_constraint('ck_reviews_status', 'reviews', type_='check')
    op.execute("UPDATE reviews SET status = 'IN_REVIEW' WHERE status = 'IN_PROGRESS'")
    op.create_check_constraint('ck_reviews_status', 'reviews', "status IN ('PENDING', 'IN_REVIEW', 'COMPLETED')")
    op.create_index(
        'uq_reviews_active_analysis_coach', 'reviews', ['analysis_id', 'coach_id'], unique=True,
        postgresql_where=sa.text("status IN ('PENDING', 'IN_REVIEW')"),
    )


def downgrade():
    op.drop_index('uq_reviews_active_analysis_coach', table_name='reviews')
    op.drop_constraint('ck_reviews_status', 'reviews', type_='check')
    op.execute("UPDATE reviews SET status = 'IN_PROGRESS' WHERE status = 'IN_REVIEW'")
    op.create_check_constraint('ck_reviews_status', 'reviews', "status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED')")
    op.create_index(
        'uq_reviews_active_analysis_coach', 'reviews', ['analysis_id', 'coach_id'], unique=True,
        postgresql_where=sa.text("status IN ('PENDING', 'IN_PROGRESS')"),
    )
