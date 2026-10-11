"""Additive idempotent reservations; historical interactions remain consumed."""
from alembic import op
import sqlalchemy as sa
revision = '0023_consumption_reservations'
down_revision = '0022_administration'
branch_labels = depends_on = None

def upgrade():
    op.add_column('plan_interactions', sa.Column('request_key', sa.String(100)))
    op.add_column('plan_interactions', sa.Column('channel', sa.String(16), nullable=False, server_default='web'))
    op.add_column('plan_interactions', sa.Column('budget_usd', sa.Numeric(18, 8)))
    op.add_column('plan_interactions', sa.Column('reservation_state', sa.String(16), nullable=False, server_default='UNCERTAIN'))
    op.add_column('plan_interactions', sa.Column('started_at', sa.DateTime(timezone=True)))
    op.add_column('plan_interactions', sa.Column('resource_id', sa.String(32)))
    op.create_unique_constraint('uq_plan_resource', 'plan_interactions', ['resource_id'])
    op.add_column('whatsapp_usage', sa.Column('reservation_state', sa.String(16)))
    op.create_unique_constraint('uq_plan_reservation', 'plan_interactions', ['user_id', 'operation', 'request_key'])

def downgrade():
    op.drop_column('whatsapp_usage', 'reservation_state')
    op.drop_constraint('uq_plan_resource', 'plan_interactions')
    op.drop_constraint('uq_plan_reservation', 'plan_interactions')
    for column in ('resource_id', 'started_at', 'reservation_state', 'budget_usd', 'channel', 'request_key'):
        op.drop_column('plan_interactions', column)
