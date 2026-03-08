"""add_ai_graphics_and_runs_v2_tables

Revision ID: a1b2c3d4e5f6
Revises: bd61b4204c35
Create Date: 2025-12-20

Adds tables for:
- AI Graphics: ai_sessions, ai_suggestions, ai_fingerprints, ai_image_assets
- RMOS Runs V2: run_artifacts, run_advisory_attachments
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'bd61b4204c35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    
    # ==========================================================================
    # AI Graphics Tables
    # ==========================================================================
    
    # ai_sessions - AI exploration sessions
    op.create_table('ai_sessions',
        sa.Column('session_id', sa.String(length=64), nullable=False),
        sa.Column('fingerprint_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('history_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at_utc', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at_utc', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_activity_utc', sa.DateTime(timezone=True), nullable=False),
        sa.Column('session_json', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('session_id')
    )
    op.create_index('ix_ai_sessions_last_activity', 'ai_sessions', ['last_activity_utc'])
    
    # ai_suggestions - Individual AI suggestions history
    op.create_table('ai_suggestions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.String(length=64), nullable=False),
        sa.Column('suggestion_id', sa.String(length=64), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('risk_bucket', sa.String(length=16), nullable=True),
        sa.Column('worst_ring_risk', sa.String(length=16), nullable=True),
        sa.Column('created_at_utc', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ai_suggestions_session_id', 'ai_suggestions', ['session_id'])
    op.create_index('ix_ai_suggestions_suggestion_id', 'ai_suggestions', ['suggestion_id'])
    op.create_index('ix_ai_suggestions_session_created', 'ai_suggestions', ['session_id', 'created_at_utc'])
    op.create_index('ix_ai_suggestions_score', 'ai_suggestions', ['overall_score'])
    
    # ai_fingerprints - Explored design fingerprints
    op.create_table('ai_fingerprints',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.String(length=64), nullable=False),
        sa.Column('outer_diameter', sa.Float(), nullable=False),
        sa.Column('inner_diameter', sa.Float(), nullable=False),
        sa.Column('ring_widths_json', sa.Text(), nullable=False),
        sa.Column('fingerprint_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at_utc', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ai_fingerprints_session_id', 'ai_fingerprints', ['session_id'])
    op.create_index('ix_ai_fingerprints_fingerprint_hash', 'ai_fingerprints', ['fingerprint_hash'])
    op.create_index('ix_ai_fingerprints_session_hash', 'ai_fingerprints', ['session_id', 'fingerprint_hash'])
    
    # ai_image_assets - AI-generated image assets
    op.create_table('ai_image_assets',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('project_id', sa.String(length=64), nullable=True),
        sa.Column('image_url', sa.Text(), nullable=True),
        sa.Column('thumbnail_url', sa.Text(), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=True),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('engineered_prompt', sa.Text(), nullable=True),
        sa.Column('negative_prompt', sa.Text(), nullable=True),
        sa.Column('provider', sa.String(length=32), nullable=False),
        sa.Column('quality', sa.String(length=16), nullable=False),
        sa.Column('size', sa.String(length=16), nullable=False),
        sa.Column('style', sa.String(length=32), nullable=True),
        sa.Column('category', sa.String(length=32), nullable=True),
        sa.Column('body_shape', sa.String(length=64), nullable=True),
        sa.Column('finish', sa.String(length=64), nullable=True),
        sa.Column('status', sa.String(length=16), nullable=False, server_default='pending'),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('reviewed_by', sa.String(length=64), nullable=True),
        sa.Column('reviewed_at_utc', sa.DateTime(timezone=True), nullable=True),
        sa.Column('attached_to_run_id', sa.String(length=64), nullable=True),
        sa.Column('attached_at_utc', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at_utc', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at_utc', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ai_image_assets_project_id', 'ai_image_assets', ['project_id'])
    op.create_index('ix_ai_image_assets_content_hash', 'ai_image_assets', ['content_hash'])
    op.create_index('ix_ai_image_assets_provider', 'ai_image_assets', ['provider'])
    op.create_index('ix_ai_image_assets_category', 'ai_image_assets', ['category'])
    op.create_index('ix_ai_image_assets_status', 'ai_image_assets', ['status'])
    op.create_index('ix_ai_image_assets_attached_to_run_id', 'ai_image_assets', ['attached_to_run_id'])
    op.create_index('ix_ai_images_status_created', 'ai_image_assets', ['status', 'created_at_utc'])
    op.create_index('ix_ai_images_provider_category', 'ai_image_assets', ['provider', 'category'])
    op.create_index('ix_ai_images_rating', 'ai_image_assets', ['rating'])
    
    # ==========================================================================
    # RMOS Runs V2 Tables
    # ==========================================================================
    
    # run_artifacts - Immutable run artifacts
    op.create_table('run_artifacts',
        sa.Column('run_id', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('mode', sa.String(length=64), nullable=False),
        sa.Column('risk_level', sa.String(length=16), nullable=False),
        sa.Column('created_at_utc', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at_utc', sa.DateTime(timezone=True), nullable=False),
        sa.Column('tool_id', sa.String(length=128), nullable=False),
        sa.Column('material_id', sa.String(length=128), nullable=True),
        sa.Column('machine_id', sa.String(length=128), nullable=True),
        sa.Column('workflow_session_id', sa.String(length=64), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('feasibility_sha256', sa.String(length=64), nullable=False),
        sa.Column('toolpaths_sha256', sa.String(length=64), nullable=True),
        sa.Column('gcode_sha256', sa.String(length=64), nullable=True),
        sa.Column('explanation_status', sa.String(length=16), nullable=False, server_default='NONE'),
        sa.Column('has_advisory_inputs', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('artifact_json', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('run_id')
    )
    op.create_index('ix_run_artifacts_status', 'run_artifacts', ['status'])
    op.create_index('ix_run_artifacts_mode', 'run_artifacts', ['mode'])
    op.create_index('ix_run_artifacts_risk_level', 'run_artifacts', ['risk_level'])
    op.create_index('ix_run_artifacts_created_at_utc', 'run_artifacts', ['created_at_utc'])
    op.create_index('ix_run_artifacts_tool_id', 'run_artifacts', ['tool_id'])
    op.create_index('ix_run_artifacts_material_id', 'run_artifacts', ['material_id'])
    op.create_index('ix_run_artifacts_machine_id', 'run_artifacts', ['machine_id'])
    op.create_index('ix_run_artifacts_workflow_session_id', 'run_artifacts', ['workflow_session_id'])
    op.create_index('ix_runs_status_created', 'run_artifacts', ['status', 'created_at_utc'])
    op.create_index('ix_runs_mode_risk', 'run_artifacts', ['mode', 'risk_level'])
    op.create_index('ix_runs_tool_material', 'run_artifacts', ['tool_id', 'material_id'])
    op.create_index('ix_runs_session_created', 'run_artifacts', ['workflow_session_id', 'created_at_utc'])
    
    # run_advisory_attachments - Junction table for advisory inputs
    op.create_table('run_advisory_attachments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('run_id', sa.String(length=64), nullable=False),
        sa.Column('advisory_id', sa.String(length=64), nullable=False),
        sa.Column('kind', sa.String(length=32), nullable=False, server_default='unknown'),
        sa.Column('created_at_utc', sa.DateTime(timezone=True), nullable=False),
        sa.Column('request_id', sa.String(length=64), nullable=True),
        sa.Column('engine_id', sa.String(length=64), nullable=True),
        sa.Column('engine_version', sa.String(length=32), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_advisory_run_id', 'run_advisory_attachments', ['run_id'])
    op.create_index('ix_advisory_advisory_id', 'run_advisory_attachments', ['advisory_id'])


def downgrade() -> None:
    """Downgrade database schema."""
    
    # Drop RMOS Runs V2 tables
    op.drop_table('run_advisory_attachments')
    op.drop_table('run_artifacts')
    
    # Drop AI Graphics tables
    op.drop_table('ai_image_assets')
    op.drop_table('ai_fingerprints')
    op.drop_table('ai_suggestions')
    op.drop_table('ai_sessions')
