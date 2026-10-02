"""Persist numeric evidence for AI observations.

Revision ID: 0014_ai_observation_evidence
Revises: 0013_repetition_corrections
"""
from alembic import op
import sqlalchemy as sa


revision = '0014_ai_observation_evidence'
down_revision = '0013_repetition_corrections'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('ai_observations', sa.Column('evidence', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('ai_observations', 'evidence')
