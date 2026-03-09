"""
Create Supabase Auth tables: user_profiles, projects, feature_flags

Revision ID: 0001_supabase_auth
Revises:
Create Date: 2026-03-09

Phase 3 SaaS Infrastructure:
- user_profiles: Extends Supabase auth.users with tier info
- projects: User-owned instrument design projects
- feature_flags: Tier-based feature access control
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

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
    op.create_table(
        "user_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tier", sa.String(20), nullable=False, server_default="free"),
        sa.Column("tier_started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("tier_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("display_name", sa.String(128), nullable=True),
        sa.Column("avatar_url", sa.Text, nullable=True),
        sa.Column("stripe_customer_id", sa.String(128), nullable=True),
        sa.Column("preferences", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("tier IN ('free', 'pro')", name="tier_check"),
    )

    # =========================================================================
    # projects - User-owned instrument design projects
    # =========================================================================
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("instrument_type", sa.String(64), nullable=True),
        sa.Column("data", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("features_used", postgresql.ARRAY(sa.Text), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Index("idx_projects_owner", "owner_id"),
        sa.Index("idx_projects_instrument", "instrument_type"),
    )

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
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("rollout_percentage", sa.Integer, nullable=False, server_default="100"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("min_tier IN ('free', 'pro')", name="min_tier_check"),
        sa.CheckConstraint("rollout_percentage BETWEEN 0 AND 100", name="rollout_check"),
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
    op.drop_table("feature_flags")
    op.drop_table("projects")
    op.drop_table("user_profiles")
