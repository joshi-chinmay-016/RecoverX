"""Add identity, merchant memberships and RBAC for Phase 6.

Revision ID: 006
Revises: 005
Create Date: 2025-08-25 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    # 0. Extend auditeventtype enum with Phase 6 values
    for event_val in [
        'USER_LOGIN_SUCCESS',
        'USER_LOGIN_FAILURE',
        'TOKEN_REJECTED',
        'ROLE_CHANGED',
        'MEMBERSHIP_CREATED',
        'MEMBERSHIP_DISABLED',
        'POLICY_CHANGED',
    ]:
        op.execute(sa.text(f"ALTER TYPE auditeventtype ADD VALUE IF NOT EXISTS '{event_val}'"))

    # 1. Create UserRole enum type
    user_role_enum = postgresql.ENUM('ADMIN', 'OPERATOR', 'ANALYST', name='userrole', create_type=False)
    user_role_enum.create(op.get_bind(), checkfirst=True)

    # 2. Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 3. Create merchant_memberships table
    op.create_table(
        'merchant_memberships',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('merchant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('merchants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', user_role_enum, nullable=False, server_default='ANALYST'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('user_id', 'merchant_id', name='uq_user_merchant_membership')
    )
    op.create_index('ix_merchant_memberships_user_id', 'merchant_memberships', ['user_id'])
    op.create_index('ix_merchant_memberships_merchant_id', 'merchant_memberships', ['merchant_id'])
    op.create_index('ix_merchant_memberships_role', 'merchant_memberships', ['role'])


def downgrade():
    op.drop_table('merchant_memberships')
    op.drop_table('users')
    op.execute("DROP TYPE IF EXISTS userrole")
