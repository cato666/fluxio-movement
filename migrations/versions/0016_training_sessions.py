"""Independent athlete training log."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0016_training_sessions'
down_revision = '0015_review_status_default'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('training_sessions',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('athlete_id', sa.UUID(), sa.ForeignKey('athletes.user_id'), nullable=False),
        sa.Column('trained_on', sa.Date(), nullable=False),
        sa.Column('title', sa.String(160), nullable=False),
        sa.Column('source_text', sa.Text(), nullable=False),
        sa.Column('workout', sa.Text(), nullable=False),
        sa.Column('result_text', sa.Text()),
        sa.Column('adaptations', sa.Text()),
        sa.Column('rpe', sa.Integer()),
        sa.Column('video_links', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('rpe IS NULL OR rpe BETWEEN 1 AND 10', name='ck_training_sessions_rpe'))
    op.create_index('ix_training_sessions_athlete_id', 'training_sessions', ['athlete_id'])


def downgrade():
    op.drop_table('training_sessions')
