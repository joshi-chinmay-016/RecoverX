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
    # Safely create PostgreSQL enums if they do not exist
    sa.Enum(
        'PAYMENT_METHOD_FAILURE',
        'INSUFFICIENT_FUNDS',
        'BANK_FAILURE',
        'NETWORK_FAILURE',
        'AUTHENTICATION_FAILURE',
        'LIMIT_EXCEEDED',
        'TEMPORARY_FAILURE',
        'UNKNOWN',
        name='failurecategory'
    ).create(op.get_bind(), checkfirst=True)
    
    sa.Enum(
        'LOW',
        'MEDIUM',
        'HIGH',
        'CRITICAL',
        name='prioritylevel'
    ).create(op.get_bind(), checkfirst=True)

    failure_category_enum = postgresql.ENUM(
        'PAYMENT_METHOD_FAILURE',
        'INSUFFICIENT_FUNDS',
        'BANK_FAILURE',
        'NETWORK_FAILURE',
        'AUTHENTICATION_FAILURE',
        'LIMIT_EXCEEDED',
        'TEMPORARY_FAILURE',
        'UNKNOWN',
        name='failurecategory',
        create_type=False
    )
    
    priority_level_enum = postgresql.ENUM(
        'LOW',
        'MEDIUM',
        'HIGH',
        'CRITICAL',
        name='prioritylevel',
        create_type=False
    )
    
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
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recovery_case_id'], ['recovery_cases.id'], ondelete='SET NULL')
    )
    
    # Create indexes for efficient querying
    op.create_index(op.f('ix_revenue_intelligence_results_payment_id'), 'revenue_intelligence_results', ['payment_id'], unique=True)
    op.create_index(op.f('ix_revenue_intelligence_results_recovery_case_id'), 'revenue_intelligence_results', ['recovery_case_id'])
    op.create_index(op.f('ix_revenue_intelligence_results_priority'), 'revenue_intelligence_results', ['priority'])
    op.create_index(op.f('ix_revenue_intelligence_results_failure_category'), 'revenue_intelligence_results', ['failure_category'])
    op.create_index(op.f('ix_revenue_intelligence_results_opportunity_score'), 'revenue_intelligence_results', ['opportunity_score'])


def downgrade() -> None:
    # Drop table
    op.drop_table('revenue_intelligence_results')
    
    # Drop enums
    sa.Enum(name='prioritylevel').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='failurecategory').drop(op.get_bind(), checkfirst=True)
