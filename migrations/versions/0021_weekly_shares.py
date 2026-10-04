"""Revocable weekly snapshots; raw access tokens are never stored."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '0021_weekly_shares'
down_revision = '0020_whatsapp_capture'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('weekly_shares',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('athlete_id', sa.UUID(), sa.ForeignKey('athletes.user_id'), nullable=False),
        sa.Column('token_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('week_start', sa.Date(), nullable=False),
        sa.Column('snapshot', JSONB(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_index('ix_weekly_shares_athlete_id', 'weekly_shares', ['athlete_id'])


def downgrade():
    op.drop_table('weekly_shares')
