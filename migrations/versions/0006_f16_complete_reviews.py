"""F1.6 completed coach reviews.

Revision ID: 0006_f16_complete_reviews
Revises: 0005_f15_coach_annotations
"""
from alembic import op
import sqlalchemy as sa

revision = '0006_f16_complete_reviews'
down_revision = '0005_f15_coach_annotations'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('reviews', sa.Column('strengths', sa.Text(), nullable=True))
    op.add_column('reviews', sa.Column('main_focus', sa.Text(), nullable=True))
    op.add_column('reviews', sa.Column('next_session', sa.Text(), nullable=True))
    op.execute("UPDATE reviews SET main_focus = COALESCE(NULLIF(trim(summary), ''), 'Revisión histórica') WHERE status = 'COMPLETED'")
    op.execute("UPDATE reviews SET next_session = 'Sin próxima sesión registrada' WHERE status = 'COMPLETED'")
    op.drop_constraint('ck_reviews_completed', 'reviews', type_='check')
    op.create_check_constraint(
        'ck_reviews_completed', 'reviews',
        "status != 'COMPLETED' OR (main_focus IS NOT NULL AND length(trim(main_focus)) > 0 AND next_session IS NOT NULL AND length(trim(next_session)) > 0 AND completed_at IS NOT NULL)",
    )


def downgrade():
    op.drop_constraint('ck_reviews_completed', 'reviews', type_='check')
    op.execute("UPDATE reviews SET summary = COALESCE(NULLIF(trim(summary), ''), 'Revisión finalizada') WHERE status = 'COMPLETED'")
    op.create_check_constraint(
        'ck_reviews_completed', 'reviews',
        "status != 'COMPLETED' OR (summary IS NOT NULL AND length(trim(summary)) > 0 AND completed_at IS NOT NULL)",
    )
    op.drop_column('reviews', 'next_session')
    op.drop_column('reviews', 'main_focus')
    op.drop_column('reviews', 'strengths')
