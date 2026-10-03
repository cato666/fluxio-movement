"""Add typed note metadata and private WhatsApp video references."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0020_whatsapp_capture'
down_revision = '0019_whatsapp_foundation'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('training_sessions', sa.Column('athlete_notes', postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.create_table('whatsapp_media',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('athlete_id', sa.UUID(), sa.ForeignKey('athletes.user_id'), nullable=False),
        sa.Column('training_session_id', sa.UUID(), sa.ForeignKey('training_sessions.id', ondelete='SET NULL')),
        sa.Column('inbox_id', sa.UUID(), sa.ForeignKey('whatsapp_inbox.id'), nullable=False, unique=True),
        sa.Column('path', sa.Text(), nullable=False),
        sa.Column('media_type', sa.String(16), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_index('ix_whatsapp_media_athlete_id', 'whatsapp_media', ['athlete_id'])


def downgrade():
    op.drop_table('whatsapp_media')
    op.drop_column('training_sessions', 'athlete_notes')
