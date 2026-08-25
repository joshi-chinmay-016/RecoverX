"""Add agent runs tables for Phase 3.

Revision ID: 003
Revises: 002
Create Date: 2025-08-22 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Safely create enum if it doesn't already exist
    sa.Enum(
        'CREATED', 'INVESTIGATING', 'PLANNING', 'VALIDATING', 'COMPLETED', 'BLOCKED', 'FAILED',
        name='agentrunstatus'
    ).create(op.get_bind(), checkfirst=True)

    agent_run_status_enum = postgresql.ENUM(
        'CREATED', 'INVESTIGATING', 'PLANNING', 'VALIDATING', 'COMPLETED', 'BLOCKED', 'FAILED',
        name='agentrunstatus',
        create_type=False
    )

    # Create agent_runs table
    op.create_table(
        'agent_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('run_id', sa.String(), nullable=False),
        sa.Column('opportunity_id', sa.String(), nullable=False),
        sa.Column('payment_id', sa.String(), nullable=False),
        sa.Column('merchant_id', sa.String(), nullable=False),
        sa.Column('current_step', sa.Integer(), default=0),
        sa.Column('status', agent_run_status_enum, nullable=False),
        sa.Column('context', postgresql.JSONB(), nullable=True),
        sa.Column('tool_calls_summary', postgresql.JSONB(), nullable=True),
        sa.Column('reasoning_summary', sa.Text(), nullable=True),
        sa.Column('decision_trace', postgresql.JSONB(), nullable=True),
        sa.Column('proposed_plan', postgresql.JSONB(), nullable=True),
        sa.Column('validation_result', postgresql.JSONB(), nullable=True),
        sa.Column('errors', postgresql.JSONB(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('agent_version', sa.String(), nullable=False),
        sa.Column('prompt_version', sa.String(), nullable=False),
        sa.Column('policy_version', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    
    # Create indexes
    op.create_index('ix_agent_runs_run_id', 'agent_runs', ['run_id'])
    op.create_index('ix_agent_runs_opportunity_id', 'agent_runs', ['opportunity_id'])
    op.create_index('ix_agent_runs_payment_id', 'agent_runs', ['payment_id'])
    op.create_index('ix_agent_runs_merchant_id', 'agent_runs', ['merchant_id'])
    op.create_index('ix_agent_runs_status', 'agent_runs', ['status'])
    op.create_index('ix_agent_runs_created_at', 'agent_runs', ['created_at'])
    
    # Create agent_tool_calls table
    op.create_table(
        'agent_tool_calls',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('run_id', sa.String(), nullable=False),
        sa.Column('agent_run_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agent_runs.id'), nullable=False),
        sa.Column('tool_name', sa.String(), nullable=False),
        sa.Column('input_summary', sa.Text(), nullable=True),
        sa.Column('output_summary', sa.Text(), nullable=True),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    
    # Create indexes
    op.create_index('ix_agent_tool_calls_run_id', 'agent_tool_calls', ['run_id'])


def downgrade():
    op.drop_index('ix_agent_tool_calls_run_id', table_name='agent_tool_calls')
    op.drop_table('agent_tool_calls')
    
    op.drop_index('ix_agent_runs_created_at', table_name='agent_runs')
    op.drop_index('ix_agent_runs_status', table_name='agent_runs')
    op.drop_index('ix_agent_runs_merchant_id', table_name='agent_runs')
    op.drop_index('ix_agent_runs_payment_id', table_name='agent_runs')
    op.drop_index('ix_agent_runs_opportunity_id', table_name='agent_runs')
    op.drop_index('ix_agent_runs_run_id', table_name='agent_runs')
    op.drop_table('agent_runs')
    
    sa.Enum(name='agentrunstatus').drop(op.get_bind(), checkfirst=True)
