"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2025-01-01 00:00:00.000000

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
    """Create initial database schema."""
    
    # Create search_queries table
    op.create_table('search_queries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('criteria_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('mode', sa.Enum('SYNC', 'ASYNC', name='searchmode'), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', name='searchstatus'), nullable=False),
        sa.Column('error_text', sa.Text(), nullable=True),
        sa.Column('total_providers', sa.String(), nullable=False),
        sa.Column('completed_providers', sa.String(), nullable=False),
        sa.Column('total_listings', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_search_queries_id'), 'search_queries', ['id'], unique=False)
    
    # Create provider_runs table
    op.create_table('provider_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('search_query_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_name', sa.String(length=100), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'TIMEOUT', name='providerrunstatus'), nullable=False),
        sa.Column('error_text', sa.Text(), nullable=True),
        sa.Column('request_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('raw_payload_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('listings_found', sa.Integer(), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['raw_payload_id'], ['raw_payloads.id'], ),
        sa.ForeignKeyConstraint(['search_query_id'], ['search_queries.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_provider_runs_id'), 'provider_runs', ['id'], unique=False)
    
    # Create raw_payloads table
    op.create_table('raw_payloads',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_name', sa.String(length=100), nullable=False),
        sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('request_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('response_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('http_status', sa.Integer(), nullable=False),
        sa.Column('response_hash', sa.String(length=64), nullable=False),
        sa.Column('response_size_bytes', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_raw_payloads_response_hash', 'raw_payloads', ['response_hash'], unique=False)
    op.create_index(op.f('ix_raw_payloads_id'), 'raw_payloads', ['id'], unique=False)
    
    # Create listings table
    op.create_table('listings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('canonical_key', sa.String(length=500), nullable=False),
        sa.Column('address_line1', sa.String(length=200), nullable=False),
        sa.Column('address_line2', sa.String(length=200), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('state', sa.String(length=2), nullable=False),
        sa.Column('postal_code', sa.String(length=20), nullable=False),
        sa.Column('country', sa.String(length=2), nullable=False),
        sa.Column('latitude', sa.Numeric(precision=10, scale=8), nullable=True),
        sa.Column('longitude', sa.Numeric(precision=11, scale=8), nullable=True),
        sa.Column('property_type', sa.String(length=50), nullable=False),
        sa.Column('bedrooms', sa.Integer(), nullable=True),
        sa.Column('bathrooms', sa.Numeric(precision=3, scale=1), nullable=True),
        sa.Column('sqft', sa.Integer(), nullable=True),
        sa.Column('lot_sqft', sa.Integer(), nullable=True),
        sa.Column('year_built', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('list_price', sa.Integer(), nullable=True),
        sa.Column('first_seen_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('images', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('canonical_key')
    )
    op.create_index('ix_listing_location', 'listings', ['city', 'state'], unique=False)
    op.create_index('ix_listing_price', 'listings', ['list_price'], unique=False)
    op.create_index('ix_listing_property_type', 'listings', ['property_type'], unique=False)
    op.create_index('ix_listing_status', 'listings', ['status'], unique=False)
    op.create_index(op.f('ix_listings_id'), 'listings', ['id'], unique=False)
    op.create_index('ix_listings_canonical_key', 'listings', ['canonical_key'], unique=False)
    
    # Create listing_sources table
    op.create_table('listing_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('listing_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_name', sa.String(length=100), nullable=False),
        sa.Column('provider_listing_id', sa.String(length=200), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('list_price', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('raw_payload_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('first_seen_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['listing_id'], ['listings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['raw_payload_id'], ['raw_payloads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_listing_sources_id'), 'listing_sources', ['id'], unique=False)


def downgrade() -> None:
    """Drop all tables."""
    
    op.drop_index(op.f('ix_listing_sources_id'), table_name='listing_sources')
    op.drop_table('listing_sources')
    
    op.drop_index('ix_listing_status', table_name='listings')
    op.drop_index('ix_listing_property_type', table_name='listings')
    op.drop_index('ix_listing_price', table_name='listings')
    op.drop_index('ix_listing_location', table_name='listings')
    op.drop_index('ix_listings_canonical_key', table_name='listings')
    op.drop_index(op.f('ix_listings_id'), table_name='listings')
    op.drop_table('listings')
    
    op.drop_index('ix_raw_payloads_response_hash', table_name='raw_payloads')
    op.drop_index(op.f('ix_raw_payloads_id'), table_name='raw_payloads')
    op.drop_table('raw_payloads')
    
    op.drop_index(op.f('ix_provider_runs_id'), table_name='provider_runs')
    op.drop_table('provider_runs')
    
    op.drop_index(op.f('ix_search_queries_id'), table_name='search_queries')
    op.drop_table('search_queries')
