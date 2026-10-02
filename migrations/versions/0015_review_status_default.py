"""Align the review default and AI reasoning index with existing models.

Revision ID: 0015_review_status_default
Revises: 0014_ai_observation_evidence
"""
from alembic import op

revision = '0015_review_status_default'
down_revision = '0014_ai_observation_evidence'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('reviews', 'status', server_default='PENDING')
    op.drop_constraint('ai_reasoning_runs_analysis_id_key', 'ai_reasoning_runs', type_='unique')
    op.create_index('ix_ai_reasoning_runs_analysis_id', 'ai_reasoning_runs', ['analysis_id'], unique=True)


def downgrade():
    op.drop_index('ix_ai_reasoning_runs_analysis_id', table_name='ai_reasoning_runs')
    op.create_unique_constraint('ai_reasoning_runs_analysis_id_key', 'ai_reasoning_runs', ['analysis_id'])
    op.alter_column('reviews', 'status', server_default='REQUESTED')
