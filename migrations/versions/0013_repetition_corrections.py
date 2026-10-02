"""Add coach-correctable repetition state.

Revision ID: 0013_repetition_corrections
Revises: 0012_system_admin
"""
from alembic import op
import sqlalchemy as sa

revision = '0013_repetition_corrections'
down_revision = '0012_system_admin'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('repetitions', sa.Column('source', sa.String(16), nullable=False, server_default='DETECTED'))
    op.add_column('repetitions', sa.Column('correction_status', sa.String(16), nullable=False, server_default='ACTIVE'))
    op.add_column('repetitions', sa.Column('correction_note', sa.Text(), nullable=True))
    op.create_check_constraint('ck_repetitions_source', 'repetitions', "source IN ('DETECTED', 'MANUAL')")
    op.create_check_constraint('ck_repetitions_correction_status', 'repetitions', "correction_status IN ('ACTIVE', 'DISCARDED')")


def downgrade():
    op.drop_constraint('ck_repetitions_correction_status', 'repetitions', type_='check')
    op.drop_constraint('ck_repetitions_source', 'repetitions', type_='check')
    op.drop_column('repetitions', 'correction_note')
    op.drop_column('repetitions', 'correction_status')
    op.drop_column('repetitions', 'source')
