"""Add system administrator role.

Revision ID: 0012_system_admin
Revises: 0011_basic_auth
"""
from alembic import op

revision = '0012_system_admin'
down_revision = '0011_basic_auth'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('ck_users_role', 'users', type_='check')
    op.create_check_constraint('ck_users_role', 'users', "role IN ('ATHLETE', 'COACH', 'SYSTEM_ADMIN')")


def downgrade():
    op.drop_constraint('ck_users_role', 'users', type_='check')
    op.create_check_constraint('ck_users_role', 'users', "role IN ('ATHLETE', 'COACH')")
