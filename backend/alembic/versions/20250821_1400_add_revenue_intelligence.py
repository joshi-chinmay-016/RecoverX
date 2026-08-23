"""Add revenue intelligence results table

Revision ID: 002
Revises: 001
Create Date: 2025-08-21 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums for intelligence
    failure_category_enum = sa.Enum(
        'PAYMENT_METHOD_FAILURE',
        'INSUFFICIENT_FUNDS',
        'BANK_FAILURE',
        'NETWORK_FAILURE',
        'AUTHENTICATION_FAILURE',
        'LIMIT_EXCEEDED',
        'TEMPORARY_FAILURE',
        'UNKNOWN',
        name='failurecategory'
    )
    
    priority_level_enum = sa.Enum(
        'LOW',
        'MEDIUM',
        'HIGH',
        'CRITICAL',
        name='prioritylevel'
    )
    
    # Create enums
    failure_category_enum.create(op.get_bind())
    priority_level_enum.create(op.get_bind())
    
    # Create revenue_intelligence_results table
    op.create_table(
        'revenue_intelligence_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('payment_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('recovery_case_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Classification
        sa.Column('failure_category', failure_category_enum, nullable=False),
        sa.Column('failure_reason', sa.String(), nullable=False),
        
        # Revenue metrics
        sa.Column('revenue_at_risk', sa.Integer(), nullable=False),
        sa.Column('recovery_probability', sa.Float(), nullable=False),
        sa.Column('estimated_recoverable_revenue', sa.Integer(), nullable=False),
        
        # Scoring
        sa.Column('opportunity_score', sa.Float(), nullable=False),
        sa.Column('priority', priority_level_enum, nullable=False),
        
        # Recommendation
        sa.Column('recommended_intervention', sa.String(), nullable=False),
        sa.Column('intervention_reason', sa.String(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        
        # Explainability
        sa.Column('explanation', sa.String(), nullable=False),
        sa.Column('factors', postgresql.JSONB(), nullable=False, server_default='[]'),
        
        # Model versioning
        sa.Column('model_version', sa.String(), nullable=False, server_default='rules-v1'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ),
        sa.ForeignKeyConstraint(['recovery_case_id'], ['recovery_cases.id'], )
    )
    
    # Create index for payment_id (already unique, but good for queries)
    op.create_index('ix_revenue_intelligence_results_payment_id', 'revenue_intelligence_results', ['payment_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_revenue_intelligence_results_payment_id', table_name='revenue_intelligence_results')
    op.drop_table('revenue_intelligence_results')
    
    # Drop enums
    sa.Enum(name='prioritylevel').drop(op.get_bind())
    sa.Enum(name='failurecategory').drop(op.get_bind())
