"""Additive durable idempotency for optional keyed manual saves."""
from alembic import op
import sqlalchemy as sa

revision = '0024_training_save_requests'
down_revision = '0023_consumption_reservations'
branch_labels = depends_on = None


def upgrade():
    op.create_table('training_save_requests',
        sa.Column('athlete_id', sa.Uuid(), sa.ForeignKey('athletes.user_id'), primary_key=True),
        sa.Column('request_key', sa.Uuid(), primary_key=True),
        sa.Column('session_id', sa.Uuid(), nullable=False),
        sa.Column('payload_hash', sa.String(64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))


def downgrade():
    op.drop_table('training_save_requests')
