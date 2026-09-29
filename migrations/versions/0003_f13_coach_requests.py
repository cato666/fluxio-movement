"""F1.3 coach review requests.

Revision ID: 0003_f13_coach_requests
Revises: 0002_f12_athlete_analysis
"""
from alembic import op
import sqlalchemy as sa

revision = '0003_f13_coach_requests'
down_revision = '0002_f12_athlete_analysis'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('coaches', sa.Column('bio', sa.Text(), nullable=True))
    op.execute("""
        UPDATE coaches SET bio = CASE user_id::text
          WHEN '00000000-0000-4000-8000-000000000002' THEN 'Técnica de levantamientos olímpicos y progresiones de fuerza.'
          WHEN '00000000-0000-4000-8000-000000000003' THEN 'Entrenamiento de fuerza para construir movimiento sólido y sostenible.'
          WHEN '00000000-0000-4000-8000-000000000004' THEN 'Rendimiento funcional y técnica aplicada a movimientos de CrossFit.'
        END
        WHERE bio IS NULL
    """)
    op.create_unique_constraint('uq_analyses_id_athlete', 'analyses', ['id', 'athlete_id'])
    op.add_column('reviews', sa.Column('athlete_id', sa.Uuid(), nullable=True))
    op.execute("UPDATE reviews SET athlete_id = analyses.athlete_id FROM analyses WHERE reviews.analysis_id = analyses.id")
    op.alter_column('reviews', 'athlete_id', nullable=False)
    op.create_foreign_key(
        'fk_reviews_analysis_athlete', 'reviews', 'analyses',
        ['analysis_id', 'athlete_id'], ['id', 'athlete_id'],
    )
    op.drop_constraint('ck_reviews_status', 'reviews', type_='check')
    op.execute("UPDATE reviews SET status = 'PENDING' WHERE status = 'REQUESTED'")
    op.create_check_constraint('ck_reviews_status', 'reviews', "status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED')")
    op.create_index(
        'uq_reviews_active_analysis_coach', 'reviews', ['analysis_id', 'coach_id'], unique=True,
        postgresql_where=sa.text("status IN ('PENDING', 'IN_PROGRESS')"),
    )


def downgrade():
    op.drop_index('uq_reviews_active_analysis_coach', table_name='reviews')
    op.execute("UPDATE reviews SET status = 'REQUESTED' WHERE status = 'PENDING'")
    op.drop_constraint('ck_reviews_status', 'reviews', type_='check')
    op.create_check_constraint('ck_reviews_status', 'reviews', "status IN ('REQUESTED', 'IN_PROGRESS', 'COMPLETED')")
    op.drop_constraint('fk_reviews_analysis_athlete', 'reviews', type_='foreignkey')
    op.drop_column('reviews', 'athlete_id')
    op.drop_constraint('uq_analyses_id_athlete', 'analyses', type_='unique')
    op.drop_column('coaches', 'bio')
