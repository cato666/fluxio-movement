"""AI reasoning observations and usage.

Revision ID: 0008_f19c_ai_reasoning
Revises: 0007_f19a_async_analysis
"""
from alembic import op
import sqlalchemy as sa


revision = '0008_f19c_ai_reasoning'
down_revision = '0007_f19a_async_analysis'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('ai_observations', sa.Column('repetition_number', sa.Integer(), nullable=True))
    op.add_column('ai_observations', sa.Column('category', sa.String(length=80), nullable=True))
    op.add_column('ai_observations', sa.Column('severity', sa.String(length=16), nullable=True))
    op.add_column('ai_observations', sa.Column('title', sa.String(length=240), nullable=True))
    op.add_column('ai_observations', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('ai_observations', sa.Column('confidence', sa.String(length=16), nullable=True))
    op.add_column('ai_observations', sa.Column('model', sa.String(length=120), nullable=True))
    op.add_column('ai_observations', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.create_check_constraint('ck_ai_observations_severity', 'ai_observations', "severity IS NULL OR severity IN ('info', 'review', 'priority')")
    op.create_check_constraint('ck_ai_observations_confidence', 'ai_observations', "confidence IS NULL OR confidence IN ('low', 'medium', 'high')")
    op.create_table(
        'ai_reasoning_runs',
        sa.Column('id', sa.Uuid(), primary_key=True, nullable=False),
        sa.Column('analysis_id', sa.String(length=32), sa.ForeignKey('analyses.id'), nullable=False, unique=True),
        sa.Column('status', sa.String(length=16), nullable=False, server_default='PENDING'),
        sa.Column('model', sa.String(length=120), nullable=True),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('reasoning_tokens', sa.Integer(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'DISABLED')", name='ck_ai_reasoning_runs_status'),
    )


def downgrade():
    op.drop_table('ai_reasoning_runs')
    op.drop_constraint('ck_ai_observations_confidence', 'ai_observations', type_='check')
    op.drop_constraint('ck_ai_observations_severity', 'ai_observations', type_='check')
    for column in ('created_at', 'model', 'confidence', 'description', 'title', 'severity', 'category', 'repetition_number'):
        op.drop_column('ai_observations', column)
