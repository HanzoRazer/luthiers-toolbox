"""
Create Supabase Auth tables: user_profiles, projects, feature_flags

Revision ID: 0001_supabase_auth
Revises:
Create Date: 2026-03-09

Phase 3 SaaS Infrastructure:
- user_profiles: Extends Supabase auth.users with tier info
- projects: User-owned instrument design projects
- feature_flags: Tier-based feature access control

Database-agnostic: Works with SQLite (dev) and PostgreSQL (prod)
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = "0001_supabase_auth"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create auth tables for Supabase integration."""

    # =========================================================================
    # user_profiles - Extends Supabase auth.users
    # =========================================================================
    # Use String(36) for UUID compatibility with SQLite
    # Use JSON for SQLite, JSONB for PostgreSQL
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tier", sa.String(20), nullable=False, server_default="free"),
        sa.Column("tier_started_at", sa.DateTime(), nullable=True),
        sa.Column("tier_expires_at", sa.DateTime(), nullable=True),
        sa.Column("display_name", sa.String(128), nullable=True),
        sa.Column("avatar_url", sa.Text, nullable=True),
        sa.Column("stripe_customer_id", sa.String(128), nullable=True),
        sa.Column("preferences", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # =========================================================================
    # projects - User-owned instrument design projects
    # =========================================================================
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("instrument_type", sa.String(64), nullable=True),
        sa.Column("data", sa.JSON, nullable=True),
        sa.Column("features_used", sa.JSON, nullable=True),  # Array as JSON for SQLite
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("archived_at", sa.DateTime(), nullable=True),
    )

    # Create indexes
    op.create_index("idx_projects_owner", "projects", ["owner_id"])
    op.create_index("idx_projects_instrument", "projects", ["instrument_type"])

    # =========================================================================
    # feature_flags - Tier-based feature access control
    # =========================================================================
    op.create_table(
        "feature_flags",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("feature_key", sa.String(64), unique=True, nullable=False),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("min_tier", sa.String(20), nullable=False, server_default="free"),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("rollout_percentage", sa.Integer, nullable=False, server_default="100"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # =========================================================================
    # Seed initial feature flags
    # =========================================================================
    op.execute("""
        INSERT INTO feature_flags (feature_key, display_name, description, min_tier)
        VALUES
            ('basic_dxf_export', 'Basic DXF Export', 'Export designs to DXF format', 'free'),
            ('gcode_generation', 'G-code Generation', 'Generate G-code for CNC machines', 'free'),
            ('blueprint_import', 'Blueprint Import', 'Import blueprints and plans', 'free'),
            ('ai_vision', 'AI Vision Analysis', 'AI-powered vision analysis features', 'pro'),
            ('batch_processing', 'Batch Processing', 'Process multiple files at once', 'pro'),
            ('advanced_cam', 'Advanced CAM Features', 'Advanced CAM toolpaths and strategies', 'pro'),
            ('custom_posts', 'Custom Post Processors', 'Create custom post processors', 'pro')
    """)


def downgrade() -> None:
    """Drop auth tables."""
    op.drop_index("idx_projects_instrument", table_name="projects")
    op.drop_index("idx_projects_owner", table_name="projects")
    op.drop_table("feature_flags")
    op.drop_table("projects")
    op.drop_table("user_profiles")
