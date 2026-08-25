"""Add adaptive learning models and outcome records for Phase 5.

Revision ID: 005
Revises: 004
Create Date: 2025-08-24 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create learning_model_snapshots table
    op.create_table(
        'learning_model_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('merchant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('merchants.id'), nullable=True),
        sa.Column('model_version', sa.String(), nullable=False, server_default='adaptive-v1'),
        sa.Column('evidence_window_days', sa.Integer(), nullable=False, server_default='90'),
        sa.Column('total_samples', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('confirmed_recoveries', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('overall_recovery_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('brier_score', sa.Float(), nullable=True),
        sa.Column('category_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('strategy_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('drift_status', sa.String(), nullable=False, server_default='NORMAL'),
        sa.Column('drift_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_learning_model_snapshots_merchant_id', 'learning_model_snapshots', ['merchant_id'])

    # 2. Create learning_outcome_records table
    op.create_table(
        'learning_outcome_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('merchant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('merchants.id'), nullable=False),
        sa.Column('payment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payments.id'), nullable=False),
        sa.Column('recovery_action_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('recovery_actions.id'), nullable=True),
        sa.Column('failure_category', postgresql.ENUM(
            'TEMPORARY_FAILURE',
            'BANK_FAILURE',
            'INSUFFICIENT_FUNDS',
            'AUTHENTICATION_FAILURE',
            'PAYMENT_METHOD_FAILURE',
            'NETWORK_FAILURE',
            'LIMIT_EXCEEDED',
            'UNKNOWN',
            name='failurecategory',
            create_type=False
        ), nullable=False),
        sa.Column('action_type', postgresql.ENUM(
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
        ), nullable=False),
        sa.Column('amount_minor', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('payment_method', sa.String(), nullable=True),
        sa.Column('outcome_status', postgresql.ENUM(
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
        ), nullable=False),
        sa.Column('execution_latency_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('occurred_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('context_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_learning_outcome_records_merchant_id', 'learning_outcome_records', ['merchant_id'])
    op.create_index('ix_learning_outcome_records_payment_id', 'learning_outcome_records', ['payment_id'])
    op.create_index('ix_learning_outcome_records_failure_category', 'learning_outcome_records', ['failure_category'])
    op.create_index('ix_learning_outcome_records_action_type', 'learning_outcome_records', ['action_type'])
    op.create_index('ix_learning_outcome_records_outcome_status', 'learning_outcome_records', ['outcome_status'])
    op.create_index('ix_learning_outcome_records_occurred_at', 'learning_outcome_records', ['occurred_at'])


def downgrade():
    op.drop_table('learning_outcome_records')
    op.drop_table('learning_model_snapshots')
