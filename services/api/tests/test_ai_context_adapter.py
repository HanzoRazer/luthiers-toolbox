"""
AI Context Adapter - Pytest Tests

Tests for the AI context adapter interface including:
- Schema validation
- Redaction enforcement
- Provider functionality
- Assembler integration
"""

import pytest
from typing import Dict, Any

from app.ai_context.schemas import (
    Actor,
    ActorKind,
    ActorRole,
    AdapterWarning,
    ContextAttachment,
    ContextEnvelope,
    ContextRequest,
    ContextSource,
    ForbiddenCategory,
    RedactionLevel,
    RedactionPolicy,
    Scope,
    SourceKind,
    WarningCode,
    compute_bundle_sha256,
    generate_request_id,
    utc_now_iso,
)
from app.ai_context.redactor import StrictRedactor
from app.ai_context.providers import (
    governance_notes_provider,
    ui_state_hint_provider,
)
from app.ai_context.assembler import DefaultAssembler


# -------------------------
# Fixtures
# -------------------------

@pytest.fixture
def strict_policy() -> RedactionPolicy:
    """Create strict redaction policy."""
    return RedactionPolicy(
        redaction_level=RedactionLevel.STRICT,
        forbidden_categories=(
            ForbiddenCategory.TOOLPATHS,
            ForbiddenCategory.GCODE,
            ForbiddenCategory.MACHINE_SECRETS,
            ForbiddenCategory.CREDENTIAL_MATERIAL,
            ForbiddenCategory.PLAYER_PEDAGOGY,
            ForbiddenCategory.PERSONAL_DATA,
        ),
    )


@pytest.fixture
def sample_request() -> ContextRequest:
    """Create sample context request."""
    return ContextRequest(
        request_id=generate_request_id(),
        intent="Explain why export is blocked",
        actor=Actor(
            kind=ActorKind.HUMAN,
            role=ActorRole.BUILDER,
            auth_context="toolbox_session",
        ),
        scope=Scope(
            run_id="run_123",
            pattern_id="pattern_456",
        ),
    )


@pytest.fixture
def redactor() -> StrictRedactor:
    """Create strict redactor instance."""
    return StrictRedactor()


@pytest.fixture
def assembler() -> DefaultAssembler:
    """Create default assembler instance."""
    return DefaultAssembler()


# -------------------------
# Schema Tests
# -------------------------

class TestSchemas:
    """Test schema serialization and validation."""
    
    def test_actor_to_dict(self):
        """Actor should serialize correctly."""
        actor = Actor(
            kind=ActorKind.HUMAN,
            role=ActorRole.BUILDER,
            auth_context="test",
        )
        d = actor.to_dict()
        
        assert d["kind"] == "human"
        assert d["role"] == "builder"
        assert d["auth_context"] == "test"
    
    def test_scope_to_dict_omits_none(self):
        """Scope should omit None values."""
        scope = Scope(run_id="run_123")
        d = scope.to_dict()
        
        assert d == {"run_id": "run_123"}
        assert "pattern_id" not in d
    
    def test_context_source_to_dict(self):
        """ContextSource should serialize correctly."""
        source = ContextSource(
            source_id="test",
            kind=SourceKind.RUN_SUMMARY,
            content_type="application/json",
            payload={"status": "ok"},
        )
        d = source.to_dict()
        
        assert d["source_id"] == "test"
        assert d["kind"] == "run_summary"
        assert d["payload"] == {"status": "ok"}
    
    def test_bundle_sha256_deterministic(self):
        """Bundle hash should be deterministic."""
        sources = [
            ContextSource(
                source_id="s1",
                kind=SourceKind.RUN_SUMMARY,
                content_type="application/json",
                payload={"a": 1},
            ),
        ]
        attachments = []
        
        hash1 = compute_bundle_sha256(sources, attachments)
        hash2 = compute_bundle_sha256(sources, attachments)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex
    
    def test_request_id_format(self):
        """Request ID should follow format."""
        req_id = generate_request_id()
        assert req_id.startswith("ctxreq_")


# -------------------------
# Redaction Tests
# -------------------------

class TestRedaction:
    """Test redaction enforcement."""
    
    def test_redacts_toolpath_field(self, redactor, strict_policy):
        """Toolpath fields should be redacted."""
        source = ContextSource(
            source_id="test",
            kind=SourceKind.RUN_SUMMARY,
            content_type="application/json",
            payload={
                "run_id": "run_123",
                "toolpath_data": {"moves": [1, 2, 3]},
                "status": "ok",
            },
        )
        
        redacted, warnings = redactor.redact_sources([source], strict_policy)
        
        assert redacted[0].payload["toolpath_data"] == "[REDACTED]"
        assert redacted[0].payload["status"] == "ok"
        assert any(w.code == WarningCode.REDACTED_FIELD for w in warnings)
    
    def test_redacts_gcode_field(self, redactor, strict_policy):
        """G-code fields should be redacted."""
        source = ContextSource(
            source_id="test",
            kind=SourceKind.RUN_SUMMARY,
            content_type="application/json",
            payload={
                "gcode": "G21\nG90\nG0 X0 Y0",
                "summary": "Roughing pass",
            },
        )
        
        redacted, warnings = redactor.redact_sources([source], strict_policy)
        
        assert redacted[0].payload["gcode"] == "[REDACTED]"
        assert redacted[0].payload["summary"] == "Roughing pass"
    
    def test_redacts_credential_field(self, redactor, strict_policy):
        """Credential fields should be redacted."""
        source = ContextSource(
            source_id="test",
            kind=SourceKind.RUN_SUMMARY,
            content_type="application/json",
            payload={
                "config": {
                    "api_key": "secret123",
                    "endpoint": "https://api.example.com",
                },
            },
        )
        
        redacted, warnings = redactor.redact_sources([source], strict_policy)
        
        assert redacted[0].payload["config"]["api_key"] == "[REDACTED]"
        assert redacted[0].payload["config"]["endpoint"] == "https://api.example.com"
    
    def test_redacts_player_pedagogy(self, redactor, strict_policy):
        """Player/pedagogy fields should be redacted."""
        source = ContextSource(
            source_id="test",
            kind=SourceKind.RUN_SUMMARY,
            content_type="application/json",
            payload={
                "player_id": "player_abc",
                "lesson_progress": 75,
                "pattern_name": "Classic Rosette",
            },
        )
        
        redacted, warnings = redactor.redact_sources([source], strict_policy)
        
        assert redacted[0].payload["player_id"] == "[REDACTED]"
        assert redacted[0].payload["lesson_progress"] == "[REDACTED]"
        assert redacted[0].payload["pattern_name"] == "Classic Rosette"
    
    def test_redacts_action_patterns(self, redactor, strict_policy):
        """Action instructions should be redacted."""
        source = ContextSource(
            source_id="test",
            kind=SourceKind.GOVERNANCE_NOTES,
            content_type="application/json",
            payload={
                "instructions": "To fix, POST /api/runs/123/approve",
                "explanation": "The run needs approval",
            },
        )
        
        redacted, warnings = redactor.redact_sources([source], strict_policy)
        
        assert "POST /api/" not in redacted[0].payload["instructions"]
        assert "[ACTION_REDACTED]" in redacted[0].payload["instructions"]
    
    def test_redacts_nested_forbidden_fields(self, redactor, strict_policy):
        """Nested forbidden fields should be redacted."""
        source = ContextSource(
            source_id="test",
            kind=SourceKind.RUN_SUMMARY,
            content_type="application/json",
            payload={
                "level1": {
                    "level2": {
                        "password": "secret",
                        "name": "test",
                    },
                },
            },
        )
        
        redacted, warnings = redactor.redact_sources([source], strict_policy)
        
        nested = redacted[0].payload["level1"]["level2"]
        assert nested["password"] == "[REDACTED]"
        assert nested["name"] == "test"
    
    def test_filters_gcode_attachments(self, redactor, strict_policy):
        """G-code attachments should be filtered."""
        attachments = [
            ContextAttachment(
                attachment_id="att_1",
                kind="file",
                mime="application/x-gcode",
                sha256="a" * 64,
                url="/api/files/test.ngc",
            ),
            ContextAttachment(
                attachment_id="att_2",
                kind="image",
                mime="image/png",
                sha256="b" * 64,
                url="/api/files/preview.png",
            ),
        ]
        
        filtered, warnings = redactor.redact_attachments(attachments, strict_policy)
        
        assert len(filtered) == 1
        assert filtered[0].attachment_id == "att_2"
        assert any(w.code == WarningCode.REDACTED_ATTACHMENT for w in warnings)


# -------------------------
# Provider Tests
# -------------------------

class TestProviders:
    """Test context providers."""
    
    def test_governance_notes_provides_content(self, sample_request, strict_policy):
        """Governance notes provider should return content."""
        sources, attachments, warnings = governance_notes_provider.provide(
            sample_request, strict_policy
        )
        
        # Should provide at least one source
        assert len(sources) >= 1
        assert all(s.kind == SourceKind.GOVERNANCE_NOTES for s in sources)
    
    def test_ui_state_hint_infers_view(self, strict_policy):
        """UI state hint should infer likely view from scope."""
        req = ContextRequest(
            request_id=generate_request_id(),
            intent="Help with this run",
            actor=Actor(
                kind=ActorKind.HUMAN,
                role=ActorRole.BUILDER,
                auth_context="test",
            ),
            scope=Scope(run_id="run_123"),
        )
        
        sources, _, _ = ui_state_hint_provider.provide(req, strict_policy)
        
        assert len(sources) == 1
        hint = sources[0].payload
        assert hint["likely_view"] == "run_detail"
        assert hint["context_type"] == "run"
    
    def test_ui_state_hint_infers_concern(self, strict_policy):
        """UI state hint should infer user concern from intent."""
        req = ContextRequest(
            request_id=generate_request_id(),
            intent="Why is export blocked?",
            actor=Actor(
                kind=ActorKind.HUMAN,
                role=ActorRole.BUILDER,
                auth_context="test",
            ),
            scope=Scope(),
        )
        
        sources, _, _ = ui_state_hint_provider.provide(req, strict_policy)
        
        hint = sources[0].payload
        assert hint["user_concern"] == "blocker"


# -------------------------
# Assembler Tests
# -------------------------

class TestAssembler:
    """Test context assembler."""
    
    def test_builds_valid_envelope(self, assembler, sample_request, strict_policy):
        """Assembler should build valid envelope."""
        result = assembler.build(sample_request, strict_policy)
        
        envelope = result.envelope
        assert envelope.schema_id == "toolbox_ai_context_envelope"
        assert envelope.schema_version == "v1"
        assert envelope.request == sample_request
        assert envelope.policy == strict_policy
        assert len(envelope.sources) >= 1
        assert len(envelope.bundle_sha256) == 64
    
    def test_envelope_serializes_to_json(self, assembler, sample_request, strict_policy):
        """Envelope should serialize to valid JSON."""
        result = assembler.build(sample_request, strict_policy)
        
        json_str = result.envelope.to_json()
        
        import json
        parsed = json.loads(json_str)
        
        assert parsed["schema_id"] == "toolbox_ai_context_envelope"
        assert "context" in parsed
        assert "sources" in parsed["context"]
    
    def test_build_minimal_limits_providers(self, assembler, sample_request, strict_policy):
        """Minimal build should only use specified providers."""
        result = assembler.build_minimal(
            sample_request,
            provider_kinds=["ui_state_hint"],
            policy=strict_policy,
        )
        
        envelope = result.envelope
        assert len(envelope.sources) == 1
        assert envelope.sources[0].kind == SourceKind.UI_STATE_HINT
    
    def test_handles_provider_errors(self, assembler, strict_policy):
        """Assembler should handle provider errors gracefully."""
        # Create request that might cause issues
        req = ContextRequest(
            request_id="test",
            intent="test",
            actor=Actor(
                kind=ActorKind.HUMAN,
                role=ActorRole.BUILDER,
                auth_context="test",
            ),
            scope=Scope(run_id="nonexistent_run"),
        )
        
        # Should not raise, should return warnings instead
        result = assembler.build(req, strict_policy)
        
        assert result.envelope is not None


# -------------------------
# Integration Tests
# -------------------------

class TestIntegration:
    """End-to-end integration tests."""
    
    def test_full_pipeline_no_forbidden_leaks(self, assembler, sample_request, strict_policy):
        """Full pipeline should not leak forbidden content."""
        result = assembler.build(sample_request, strict_policy)

        # CAM terms are forbidden in data sources but allowed in documentation
        # (docs naturally describe toolpaths, gcode endpoints, etc.)
        cam_patterns = ["toolpath", "gcode"]

        # PII patterns are forbidden everywhere
        pii_patterns = ["api_key", "password", "player_id", "lesson_id", "email", "ssn"]

        for source in result.envelope.sources:
            payload_str = str(source.payload).lower()
            is_doc_source = source.source_id.startswith("docs_")

            # Check PII patterns in ALL sources
            for pattern in pii_patterns:
                if pattern in payload_str:
                    assert "[redacted]" in payload_str.lower(), \
                        f"Forbidden pattern '{pattern}' leaked in {source.source_id}"

            # Check CAM patterns only in non-doc sources
            if not is_doc_source:
                for pattern in cam_patterns:
                    if pattern in payload_str:
                        assert "[redacted]" in payload_str.lower(), \
                            f"Forbidden pattern '{pattern}' leaked in {source.source_id}"
    
    def test_envelope_integrity_hash_valid(self, assembler, sample_request, strict_policy):
        """Envelope integrity hash should be verifiable."""
        result = assembler.build(sample_request, strict_policy)
        
        # Recompute hash
        recomputed = compute_bundle_sha256(
            result.envelope.sources,
            result.envelope.attachments,
        )
        
        assert result.envelope.bundle_sha256 == recomputed


# -------------------------
# Pytest markers
# -------------------------

# Mark all tests in this module
pytestmark = [pytest.mark.unit, pytest.mark.ai_context]
