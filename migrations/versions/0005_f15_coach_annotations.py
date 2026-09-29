"""F1.5 coach annotations.

Revision ID: 0005_f15_coach_annotations
Revises: 0004_f14_coach_inbox
"""
from alembic import op
import sqlalchemy as sa

revision = '0005_f15_coach_annotations'
down_revision = '0004_f14_coach_inbox'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'coach_annotations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('review_id', sa.Uuid(), nullable=False),
        sa.Column('coach_id', sa.Uuid(), nullable=False),
        sa.Column('timestamp_s', sa.Float(), nullable=False),
        sa.Column('annotation_type', sa.String(length=16), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('repetition_number', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("timestamp_s >= 0 AND timestamp_s < 'Infinity'::float8", name='ck_coach_annotations_timestamp'),
        sa.CheckConstraint("annotation_type IN ('COMMENT', 'REVIEW', 'CORRECT', 'PRIORITY')", name='ck_coach_annotations_type'),
        sa.CheckConstraint('length(trim(text)) > 0', name='ck_coach_annotations_text'),
        sa.CheckConstraint('repetition_number IS NULL OR repetition_number > 0', name='ck_coach_annotations_repetition'),
        sa.ForeignKeyConstraint(['coach_id'], ['coaches.user_id']),
        sa.ForeignKeyConstraint(['review_id'], ['reviews.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_coach_annotations_review_id'), 'coach_annotations', ['review_id'], unique=False)
    op.create_index(op.f('ix_coach_annotations_coach_id'), 'coach_annotations', ['coach_id'], unique=False)
    op.create_index('ix_coach_annotations_review_timestamp', 'coach_annotations', ['review_id', 'timestamp_s'], unique=False)


def downgrade():
    op.drop_index('ix_coach_annotations_review_timestamp', table_name='coach_annotations')
    op.drop_index(op.f('ix_coach_annotations_coach_id'), table_name='coach_annotations')
    op.drop_index(op.f('ix_coach_annotations_review_id'), table_name='coach_annotations')
    op.drop_table('coach_annotations')
