"""Private whiteboard images and editable workout blocks."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '0017_training_interpretation'
down_revision = '0016_training_sessions'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('training_images',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('athlete_id', sa.UUID(), sa.ForeignKey('athletes.user_id'), nullable=False),
        sa.Column('path', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_index('ix_training_images_athlete_id', 'training_images', ['athlete_id'])
    op.add_column('training_sessions', sa.Column('blocks', JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.add_column('training_sessions', sa.Column('source_image_id', sa.UUID(), sa.ForeignKey('training_images.id')))


def downgrade():
    op.drop_column('training_sessions', 'source_image_id')
    op.drop_column('training_sessions', 'blocks')
    op.drop_table('training_images')
