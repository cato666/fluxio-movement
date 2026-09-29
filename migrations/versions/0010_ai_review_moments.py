"""Persist ranked AI review moments.

Revision ID: 0010_ai_review_moments
Revises: 0009_reanalysis_view
"""
from alembic import op
import sqlalchemy as sa

revision = "0010_ai_review_moments"
down_revision = "0009_reanalysis_view"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("ai_review_moments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("analysis_id", sa.String(32), sa.ForeignKey("analyses.id"), nullable=False),
        sa.Column("observation_id", sa.Uuid(), sa.ForeignKey("ai_observations.id"), nullable=False, unique=True),
        sa.Column("repetition_number", sa.Integer()), sa.Column("timestamp_s", sa.Float(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False), sa.Column("confidence", sa.String(16), nullable=False),
        sa.Column("priority_score", sa.Float(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("timestamp_s >= 0 AND timestamp_s < 'Infinity'::float8", name="ck_ai_review_moments_timestamp"),
        sa.CheckConstraint("confidence IN ('low', 'medium', 'high')", name="ck_ai_review_moments_confidence"),
    )
    op.create_index("ix_ai_review_moments_analysis_id", "ai_review_moments", ["analysis_id"])

def downgrade():
    op.drop_table("ai_review_moments")
