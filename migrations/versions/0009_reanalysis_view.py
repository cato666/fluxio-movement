"""Persist selected view and retain reanalysis ancestry.

Revision ID: 0009_reanalysis_view
Revises: 0008_f19c_ai_reasoning
"""
from alembic import op
import sqlalchemy as sa


revision = "0009_reanalysis_view"
down_revision = "0008_f19c_ai_reasoning"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("analyses", sa.Column("view", sa.String(length=16), server_default="side", nullable=False))
    op.add_column("analyses", sa.Column("source_analysis_id", sa.String(length=32), nullable=True))
    op.create_foreign_key("fk_analyses_source", "analyses", "analyses", ["source_analysis_id"], ["id"])
    op.create_index("ix_analyses_source_analysis_id", "analyses", ["source_analysis_id"])


def downgrade():
    op.drop_index("ix_analyses_source_analysis_id", table_name="analyses")
    op.drop_constraint("fk_analyses_source", "analyses", type_="foreignkey")
    op.drop_column("analyses", "source_analysis_id")
    op.drop_column("analyses", "view")
