"""Provider usage for training calls, independent of saved sessions."""
from alembic import op
import sqlalchemy as sa

revision = '0018_training_ai_usage'
down_revision = '0017_training_interpretation'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('training_ai_usage',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('athlete_id', sa.UUID(), sa.ForeignKey('athletes.user_id'), nullable=False),
        sa.Column('operation', sa.String(16), nullable=False),
        sa.Column('model', sa.String(120), nullable=False),
        sa.Column('status', sa.String(16), nullable=False),
        sa.Column('input_tokens', sa.Integer()), sa.Column('output_tokens', sa.Integer()),
        sa.Column('reasoning_tokens', sa.Integer()), sa.Column('duration_seconds', sa.Float()),
        sa.Column('latency_ms', sa.Integer()), sa.Column('error', sa.String(80)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("operation IN ('INTERPRET', 'TRANSCRIBE')", name='ck_training_usage_operation'),
        sa.CheckConstraint("status IN ('RUNNING', 'COMPLETED', 'FAILED')", name='ck_training_usage_status'))
    op.create_index('ix_training_ai_usage_athlete_id', 'training_ai_usage', ['athlete_id'])


def downgrade():
    op.drop_table('training_ai_usage')
