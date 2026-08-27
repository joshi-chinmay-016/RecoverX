"""Add composite performance indexes for Phase 7 production readiness.

Revision ID: 007
Revises: 006
Create Date: 2025-08-26 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Composite index on payments for tenant-scoped status & time-series queries
    op.create_index(
        'ix_payments_merchant_status_created',
        'payments',
        ['merchant_id', 'status', 'created_at'],
        if_not_exists=True,
    )

    # 2. Composite index on recovery_cases for payment lifecycle queries
    op.create_index(
        'ix_recovery_cases_payment_status',
        'recovery_cases',
        ['payment_id', 'status'],
        if_not_exists=True,
    )

    # 3. Composite index on revenue_intelligence_results for queue prioritization
    op.create_index(
        'ix_rev_intel_priority_score_created',
        'revenue_intelligence_results',
        ['priority', 'opportunity_score', 'created_at'],
        if_not_exists=True,
    )

    # 4. Composite index on recovery_actions for tenant-scoped execution monitoring
    op.create_index(
        'ix_recovery_actions_merchant_status',
        'recovery_actions',
        ['merchant_id', 'status'],
        if_not_exists=True,
    )

    # 5. Composite index on learning_outcome_records for empirical Bayesian aggregation
    op.create_index(
        'ix_learning_outcomes_lookup',
        'learning_outcome_records',
        ['merchant_id', 'failure_category', 'action_type', 'occurred_at'],
        if_not_exists=True,
    )


def downgrade():
    op.drop_index('ix_learning_outcomes_lookup', table_name='learning_outcome_records', if_exists=True)
    op.drop_index('ix_recovery_actions_merchant_status', table_name='recovery_actions', if_exists=True)
    op.drop_index('ix_rev_intel_priority_score_created', table_name='revenue_intelligence_results', if_exists=True)
    op.drop_index('ix_recovery_cases_payment_status', table_name='recovery_cases', if_exists=True)
    op.drop_index('ix_payments_merchant_status_created', table_name='payments', if_exists=True)
