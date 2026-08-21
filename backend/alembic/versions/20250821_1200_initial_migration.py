"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2025-08-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create merchants table
    op.create_table(
        'merchants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('external_id', sa.String(), nullable=False, unique=True),
        sa.Column('currency', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )
    op.create_index(op.f('ix_merchants_external_id'), 'merchants', ['external_id'], unique=True)

    # Create customers table
    op.create_table(
        'customers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('external_customer_id', sa.String(), nullable=False, unique=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )
    op.create_index(op.f('ix_customers_external_customer_id'), 'customers', ['external_customer_id'], unique=True)

    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('razorpay_payment_id', sa.String(), nullable=False, unique=True),
        sa.Column('razorpay_order_id', sa.String(), nullable=True),
        sa.Column('merchant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('amount_minor', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(), nullable=False),
        sa.Column('status', sa.Enum('CREATED', 'AUTHORIZED', 'CAPTURED', 'FAILED', name='paymentstatus'), nullable=False),
        sa.Column('method', sa.String(), nullable=True),
        sa.Column('failure_code', sa.String(), nullable=True),
        sa.Column('failure_description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], )
    )
    op.create_index(op.f('ix_payments_razorpay_payment_id'), 'payments', ['razorpay_payment_id'], unique=True)

    # Create payment_attempts table
    op.create_table(
        'payment_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('payment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('CREATED', 'AUTHORIZED', 'CAPTURED', 'FAILED', name='paymentstatus'), nullable=False),
        sa.Column('failure_code', sa.String(), nullable=True),
        sa.Column('failure_description', sa.String(), nullable=True),
        sa.Column('method', sa.String(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ),
        sa.UniqueConstraint('payment_id', 'attempt_number', name='uq_payment_attempt')
    )

    # Create webhook_events table
    op.create_table(
        'webhook_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('provider_event_id', sa.String(), nullable=False, unique=True),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('payload', postgresql.JSONB(), nullable=False),
        sa.Column('signature_verified', sa.Boolean(), nullable=False),
        sa.Column('processing_status', sa.Enum('RECEIVED', 'PROCESSING', 'PROCESSED', 'FAILED', 'IGNORED', name='processingstatus'), nullable=False),
        sa.Column('received_at', sa.DateTime(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )
    op.create_index(op.f('ix_webhook_events_provider_event_id'), 'webhook_events', ['provider_event_id'], unique=True)
    op.create_index(op.f('ix_webhook_events_event_type'), 'webhook_events', ['event_type'], unique=False)

    # Create recovery_cases table
    op.create_table(
        'recovery_cases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('payment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.Enum('OPEN', 'RESOLVED', 'CLOSED', name='recoverycasestatus'), nullable=False),
        sa.Column('amount_at_risk_minor', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], )
    )

    # Create audit_events table
    op.create_table(
        'audit_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.Enum('WEBHOOK_RECEIVED', 'PAYMENT_CREATED', 'PAYMENT_STATUS_CHANGED', 'RECOVERY_CASE_CREATED', 'AGENT_DECISION', 'POLICY_DECISION', 'ACTION_EXECUTED', 'RECOVERY_VERIFIED', name='auditeventtype'), nullable=False),
        sa.Column('actor_type', sa.Enum('SYSTEM', 'WEBHOOK', 'AGENT', 'USER', name='actortype'), nullable=False),
        sa.Column('audit_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )
    op.create_index(op.f('ix_audit_events_entity_type'), 'audit_events', ['entity_type'], unique=False)
    op.create_index(op.f('ix_audit_events_entity_id'), 'audit_events', ['entity_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_audit_events_entity_id'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_entity_type'), table_name='audit_events')
    op.drop_table('audit_events')
    
    op.drop_table('recovery_cases')
    
    op.drop_index(op.f('ix_webhook_events_event_type'), table_name='webhook_events')
    op.drop_index(op.f('ix_webhook_events_provider_event_id'), table_name='webhook_events')
    op.drop_table('webhook_events')
    
    op.drop_table('payment_attempts')
    
    op.drop_index(op.f('ix_payments_razorpay_payment_id'), table_name='payments')
    op.drop_table('payments')
    
    op.drop_index(op.f('ix_customers_external_customer_id'), table_name='customers')
    op.drop_table('customers')
    
    op.drop_index(op.f('ix_merchants_external_id'), table_name='merchants')
    op.drop_table('merchants')