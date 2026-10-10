"""User administration and monthly plan quotas."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '0022_administration'
down_revision = '0021_weekly_shares'
branch_labels = depends_on = None


def upgrade():
    op.add_column('users', sa.Column('email', sa.String(254), unique=True))
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column('users', sa.Column('plan', sa.String(16), nullable=False, server_default='FREE'))
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(timezone=True)))
    op.create_check_constraint('ck_users_plan', 'users', "plan IN ('FREE', 'PAID')")
    op.create_table('admin_settings', sa.Column('key', sa.String(40), primary_key=True), sa.Column('value', JSONB(), nullable=False))
    op.create_table('admin_audit', sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('actor_id', sa.UUID(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('action', sa.String(40), nullable=False), sa.Column('target', sa.String(80), nullable=False),
        sa.Column('changes', JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_table('plan_interactions', sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('operation', sa.String(24), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_index('ix_plan_interactions_user_id', 'plan_interactions', ['user_id'])


def downgrade():
    for table in ('plan_interactions', 'admin_audit', 'admin_settings'):
        op.drop_table(table)
    op.drop_constraint('ck_users_plan', 'users')
    for column in ('last_login_at', 'plan', 'is_active', 'email'):
        op.drop_column('users', column)
