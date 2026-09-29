"""F1.2 athlete analysis metadata and pending status.

Revision ID: 0002_f12_athlete_analysis
Revises: 0001_f1_persistence
"""
from alembic import op
import sqlalchemy as sa

revision = '0002_f12_athlete_analysis'
down_revision = '0001_f1_persistence'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('analyses', sa.Column('exercise', sa.String(length=100), nullable=True))
    op.add_column('analyses', sa.Column('load_kg', sa.Float(), nullable=True))
    op.add_column('analyses', sa.Column('objective', sa.Text(), nullable=True))
    op.add_column('analyses', sa.Column('analysis_json_path', sa.Text(), nullable=True))
    op.create_check_constraint('ck_analyses_load_kg', 'analyses', "load_kg >= 0 AND load_kg < 'Infinity'::float8")
    op.drop_constraint('ck_analyses_status', 'analyses', type_='check')
    op.create_check_constraint('ck_analyses_status', 'analyses', "status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')")
    # Files generated in F1.1 already have this location; keep older rows useful.
    op.execute("UPDATE analyses SET analysis_json_path = 'results/' || id || '/analysis.json' WHERE status = 'COMPLETED'")


def downgrade():
    # PENDING rows cannot satisfy the earlier status constraint.
    op.execute("UPDATE analyses SET status = 'FAILED', error = 'Interrupted before processing' WHERE status = 'PENDING'")
    op.drop_constraint('ck_analyses_status', 'analyses', type_='check')
    op.create_check_constraint('ck_analyses_status', 'analyses', "status IN ('PROCESSING', 'COMPLETED', 'FAILED')")
    op.drop_constraint('ck_analyses_load_kg', 'analyses', type_='check')
    op.drop_column('analyses', 'analysis_json_path')
    op.drop_column('analyses', 'objective')
    op.drop_column('analyses', 'load_kg')
    op.drop_column('analyses', 'exercise')
