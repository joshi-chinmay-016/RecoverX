"""Add recovery actions and execution attempts for Phase 4.

Revision ID: 004
Revises: 003
Create Date: 2025-08-23 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Safely create ActionType enum if not exists
    sa.Enum(
        'RETRY_PAYMENT',
        'REQUEST_ALTERNATE_PAYMENT_METHOD',
        'SEND_PAYMENT_REMINDER',
        'REQUEST_REAUTHENTICATION',
        'WAIT_AND_RETRY',
        'MANUAL_REVIEW',
        'CLOSE_RECOVERY_CASE',
        'ESCALATE',
        name='actiontype'
    ).create(op.get_bind(), checkfirst=True)

    action_type_enum = postgresql.ENUM(
        'RETRY_PAYMENT',
        'REQUEST_ALTERNATE_PAYMENT_METHOD',
        'SEND_PAYMENT_REMINDER',
        'REQUEST_REAUTHENTICATION',
        'WAIT_AND_RETRY',
        'MANUAL_REVIEW',
        'CLOSE_RECOVERY_CASE',
        'ESCALATE',
        name='actiontype',
        create_type=False
    )

    # 2. Safely create ActionStatus enum
    sa.Enum(
        'PROPOSED',
        'POLICY_CHECK',
        'AUTHORIZED',
        'QUEUED',
        'EXECUTING',
        'SUCCEEDED',
        'FAILED',
        'RETRYABLE',
        'BLOCKED',
        'REQUIRES_APPROVAL',
        'CANCELLED',
        'UNKNOWN',
        name='actionstatus'
    ).create(op.get_bind(), checkfirst=True)

    action_status_enum = postgresql.ENUM(
        'PROPOSED',
        'POLICY_CHECK',
        'AUTHORIZED',
        'QUEUED',
        'EXECUTING',
        'SUCCEEDED',
        'FAILED',
        'RETRYABLE',
        'BLOCKED',
        'REQUIRES_APPROVAL',
        'CANCELLED',
        'UNKNOWN',
        name='actionstatus',
        create_type=False
    )

    # 3. Safely create ExecutionAttemptStatus enum
    sa.Enum(
        'PENDING',
        'EXECUTING',
        'SUCCESS',
        'FAILURE',
        'TIMEOUT',
        'UNKNOWN',
        name='executionattemptstatus'
    ).create(op.get_bind(), checkfirst=True)

    attempt_status_enum = postgresql.ENUM(
        'PENDING',
        'EXECUTING',
        'SUCCESS',
        'FAILURE',
        'TIMEOUT',
        'UNKNOWN',
        name='executionattemptstatus',
        create_type=False
    )

    # 4. Create recovery_actions table
    op.create_table(
        'recovery_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('action_id', sa.String(), nullable=False),
        sa.Column('opportunity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('revenue_intelligence_results.id'), nullable=False),
        sa.Column('payment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payments.id'), nullable=False),
        sa.Column('merchant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('merchants.id'), nullable=False),
        sa.Column('recovery_plan_id', sa.String(), nullable=True),
        sa.Column('agent_run_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agent_runs.id'), nullable=True),
        sa.Column('action_type', action_type_enum, nullable=False),
        sa.Column('status', action_status_enum, nullable=False, server_default='PROPOSED'),
        sa.Column('parameters', postgresql.JSONB(), nullable=True),
        sa.Column('policy_decision', postgresql.JSONB(), nullable=True),
        sa.Column('idempotency_key', sa.String(), nullable=False),
        sa.Column('execution_attempts_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('provider_reference', sa.String(), nullable=True),
        sa.Column('last_result', postgresql.JSONB(), nullable=True),
        sa.Column('last_error_code', sa.String(), nullable=True),
        sa.Column('last_error_message', sa.Text(), nullable=True),
        sa.Column('policy_version', sa.String(), nullable=False, server_default='policy-v1'),
        sa.Column('execution_version', sa.String(), nullable=False, server_default='execution-v1'),
        sa.Column('requested_at', sa.DateTime(), nullable=False),
        sa.Column('authorized_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    op.create_index('ix_recovery_actions_action_id', 'recovery_actions', ['action_id'], unique=True)
    op.create_index('ix_recovery_actions_idempotency_key', 'recovery_actions', ['idempotency_key'], unique=True)
    op.create_index('ix_recovery_actions_opportunity_id', 'recovery_actions', ['opportunity_id'])
    op.create_index('ix_recovery_actions_payment_id', 'recovery_actions', ['payment_id'])
    op.create_index('ix_recovery_actions_merchant_id', 'recovery_actions', ['merchant_id'])
    op.create_index('ix_recovery_actions_status', 'recovery_actions', ['status'])

    # 5. Create execution_attempts table
    op.create_table(
        'execution_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('action_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('recovery_actions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=False),
        sa.Column('idempotency_key', sa.String(), nullable=False),
        sa.Column('adapter_name', sa.String(), nullable=False),
        sa.Column('status', attempt_status_enum, nullable=False, server_default='PENDING'),
        sa.Column('request_payload', postgresql.JSONB(), nullable=True),
        sa.Column('response_payload', postgresql.JSONB(), nullable=True),
        sa.Column('provider_reference', sa.String(), nullable=True),
        sa.Column('error_code', sa.String(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('is_retryable', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('execution_latency_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    op.create_index('ix_execution_attempts_action_id', 'execution_attempts', ['action_id'])
    op.create_index('ix_execution_attempts_idempotency_key', 'execution_attempts', ['idempotency_key'])


def downgrade():
    op.drop_table('execution_attempts')
    op.drop_table('recovery_actions')
    op.execute('DROP TYPE IF EXISTS executionattemptstatus')
    op.execute('DROP TYPE IF EXISTS actionstatus')
    op.execute('DROP TYPE IF EXISTS actiontype')
