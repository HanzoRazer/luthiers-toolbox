"""
Tests for DXF Lifecycle Guard — Runtime Boundary Phase 2A

Tests validation-only behavior. No side effects, no mutation, no logging.
"""

import pytest

from app.util.dxf_lifecycle_guard import (
    DxfLifecycleContext,
    DxfLifecycleGuardError,
    validate_dxf_lifecycle_context,
    assert_dxf_lifecycle_context,
    VALID_EXPORT_TYPES,
    VALID_LIFECYCLE_STATUSES,
    VALID_RUNTIME_CALLABLES,
    VALID_PROVENANCE_STATUSES,
    VALID_AUTHORITY_CONTEXTS,
)


def make_valid_context(**overrides) -> DxfLifecycleContext:
    """Create a valid context with optional overrides."""
    defaults = {
        "source_module": "test.module",
        "export_type": "dxf-create-save",
        "dxf_version": "R2010",
        "lifecycle_status": "COMPAT_ONLY",
        "runtime_callable": "router_endpoint",
        "authority_context": "user_request",
        "provenance_status": "NO",
    }
    defaults.update(overrides)
    return DxfLifecycleContext(**defaults)


class TestDxfLifecycleContext:
    """Tests for context dataclass."""

    def test_context_is_frozen(self):
        context = make_valid_context()
        with pytest.raises(AttributeError):
            context.source_module = "other"

    def test_context_equality(self):
        c1 = make_valid_context()
        c2 = make_valid_context()
        assert c1 == c2

    def test_context_with_all_fields(self):
        context = DxfLifecycleContext(
            source_module="app.routers.test",
            export_type="dxf-create-save",
            dxf_version="R2010",
            lifecycle_status="COMPAT_ONLY",
            runtime_callable="router_endpoint",
            authority_context="user_request",
            provenance_status="NO",
        )
        assert context.source_module == "app.routers.test"
        assert context.dxf_version == "R2010"


class TestValidateDxfLifecycleContext:
    """Tests for validate_dxf_lifecycle_context()."""

    def test_valid_context_returns_empty_list(self):
        context = make_valid_context()
        errors = validate_dxf_lifecycle_context(context)
        assert errors == []

    def test_missing_source_module(self):
        context = make_valid_context(source_module="")
        errors = validate_dxf_lifecycle_context(context)
        assert len(errors) == 1
        assert "source_module" in errors[0]

    def test_missing_export_type(self):
        context = make_valid_context(export_type="")
        errors = validate_dxf_lifecycle_context(context)
        assert len(errors) == 1
        assert "export_type" in errors[0]

    def test_invalid_export_type(self):
        context = make_valid_context(export_type="invalid-type")
        errors = validate_dxf_lifecycle_context(context)
        assert len(errors) == 1
        assert "invalid-type" in errors[0]

    def test_missing_dxf_version(self):
        context = make_valid_context(dxf_version="")
        errors = validate_dxf_lifecycle_context(context)
        assert len(errors) == 1
        assert "dxf_version" in errors[0]

    def test_missing_lifecycle_status(self):
        context = make_valid_context(lifecycle_status="")
        errors = validate_dxf_lifecycle_context(context)
        assert len(errors) == 1
        assert "lifecycle_status" in errors[0]

    def test_invalid_lifecycle_status(self):
        context = make_valid_context(lifecycle_status="INVALID")
        errors = validate_dxf_lifecycle_context(context)
        assert len(errors) == 1
        assert "INVALID" in errors[0]

    def test_missing_runtime_callable(self):
        context = make_valid_context(runtime_callable="")
        errors = validate_dxf_lifecycle_context(context)
        assert len(errors) == 1
        assert "runtime_callable" in errors[0]

    def test_invalid_runtime_callable(self):
        context = make_valid_context(runtime_callable="invalid_callable")
        errors = validate_dxf_lifecycle_context(context)
        assert len(errors) == 1
        assert "invalid_callable" in errors[0]

    def test_missing_authority_context(self):
        context = make_valid_context(authority_context="")
        errors = validate_dxf_lifecycle_context(context)
        assert len(errors) == 1
        assert "authority_context" in errors[0]

    def test_invalid_authority_context(self):
        context = make_valid_context(authority_context="invalid_auth")
        errors = validate_dxf_lifecycle_context(context)
        assert len(errors) == 1
        assert "invalid_auth" in errors[0]

    def test_missing_provenance_status(self):
        context = make_valid_context(provenance_status="")
        errors = validate_dxf_lifecycle_context(context)
        assert len(errors) == 1
        assert "provenance_status" in errors[0]

    def test_invalid_provenance_status(self):
        context = make_valid_context(provenance_status="MAYBE")
        errors = validate_dxf_lifecycle_context(context)
        assert len(errors) == 1
        assert "MAYBE" in errors[0]

    def test_multiple_errors(self):
        context = DxfLifecycleContext(
            source_module="",
            export_type="invalid",
            dxf_version="",
            lifecycle_status="INVALID",
            runtime_callable="",
            authority_context="",
            provenance_status="",
        )
        errors = validate_dxf_lifecycle_context(context)
        assert len(errors) >= 5

    def test_all_valid_export_types(self):
        for export_type in VALID_EXPORT_TYPES:
            context = make_valid_context(export_type=export_type)
            errors = validate_dxf_lifecycle_context(context)
            assert errors == [], f"Failed for export_type={export_type}"

    def test_all_valid_lifecycle_statuses(self):
        for status in VALID_LIFECYCLE_STATUSES:
            context = make_valid_context(lifecycle_status=status)
            errors = validate_dxf_lifecycle_context(context)
            assert errors == [], f"Failed for lifecycle_status={status}"

    def test_all_valid_runtime_callables(self):
        for callable_type in VALID_RUNTIME_CALLABLES:
            context = make_valid_context(runtime_callable=callable_type)
            errors = validate_dxf_lifecycle_context(context)
            assert errors == [], f"Failed for runtime_callable={callable_type}"

    def test_all_valid_provenance_statuses(self):
        for status in VALID_PROVENANCE_STATUSES:
            context = make_valid_context(provenance_status=status)
            errors = validate_dxf_lifecycle_context(context)
            assert errors == [], f"Failed for provenance_status={status}"

    def test_all_valid_authority_contexts(self):
        for auth in VALID_AUTHORITY_CONTEXTS:
            context = make_valid_context(authority_context=auth)
            errors = validate_dxf_lifecycle_context(context)
            assert errors == [], f"Failed for authority_context={auth}"


class TestAssertDxfLifecycleContext:
    """Tests for assert_dxf_lifecycle_context()."""

    def test_valid_context_does_not_raise(self):
        context = make_valid_context()
        assert_dxf_lifecycle_context(context)

    def test_invalid_context_raises_error(self):
        context = make_valid_context(source_module="")
        with pytest.raises(DxfLifecycleGuardError) as exc_info:
            assert_dxf_lifecycle_context(context)
        assert "source_module" in str(exc_info.value)

    def test_error_contains_all_failures(self):
        context = DxfLifecycleContext(
            source_module="",
            export_type="",
            dxf_version="",
            lifecycle_status="",
            runtime_callable="",
            authority_context="",
            provenance_status="",
        )
        with pytest.raises(DxfLifecycleGuardError) as exc_info:
            assert_dxf_lifecycle_context(context)
        assert len(exc_info.value.errors) >= 5

    def test_error_message_includes_errors(self):
        context = make_valid_context(export_type="bad")
        with pytest.raises(DxfLifecycleGuardError) as exc_info:
            assert_dxf_lifecycle_context(context)
        assert "bad" in str(exc_info.value)


class TestDxfLifecycleGuardError:
    """Tests for DxfLifecycleGuardError exception."""

    def test_error_stores_errors_list(self):
        errors = ["error1", "error2"]
        exc = DxfLifecycleGuardError(errors)
        assert exc.errors == errors

    def test_error_message_includes_all_errors(self):
        errors = ["first error", "second error"]
        exc = DxfLifecycleGuardError(errors)
        assert "first error" in str(exc)
        assert "second error" in str(exc)


class TestProductionContextPatterns:
    """Tests for common production context patterns."""

    def test_router_endpoint_pattern(self):
        context = DxfLifecycleContext(
            source_module="app.routers.instruments.guitar.smart_guitar_dxf_router",
            export_type="dxf-create-save",
            dxf_version="R2010",
            lifecycle_status="COMPAT_ONLY",
            runtime_callable="router_endpoint",
            authority_context="user_request",
            provenance_status="NO",
        )
        errors = validate_dxf_lifecycle_context(context)
        assert errors == []

    def test_runtime_service_pattern(self):
        context = DxfLifecycleContext(
            source_module="app.cam.dxf_writer",
            export_type="dxf-create-save",
            dxf_version="R2000",
            lifecycle_status="COMPAT_ONLY",
            runtime_callable="runtime_service",
            authority_context="pipeline_stage",
            provenance_status="NO",
        )
        errors = validate_dxf_lifecycle_context(context)
        assert errors == []

    def test_read_modify_save_pattern(self):
        context = DxfLifecycleContext(
            source_module="app.cam.line_deduplicator",
            export_type="dxf-read-modify-save",
            dxf_version="R2010",
            lifecycle_status="DIRECT_SAVE_GAP",
            runtime_callable="runtime_service",
            authority_context="pipeline_stage",
            provenance_status="NO",
        )
        errors = validate_dxf_lifecycle_context(context)
        assert errors == []

    def test_blocked_provenance_pattern(self):
        context = DxfLifecycleContext(
            source_module="app.instrument_geometry.body.ibg.body_contour_solver",
            export_type="dxf-create-save",
            dxf_version="R2000",
            lifecycle_status="BLOCKED_PROVENANCE",
            runtime_callable="runtime_service",
            authority_context="pipeline_stage",
            provenance_status="BLOCKED",
        )
        errors = validate_dxf_lifecycle_context(context)
        assert errors == []

    def test_test_fixture_pattern(self):
        context = DxfLifecycleContext(
            source_module="tests.test_dxf_export",
            export_type="dxf-create-save",
            dxf_version="R12",
            lifecycle_status="TEST_ONLY",
            runtime_callable="test_only",
            authority_context="unknown",
            provenance_status="N/A",
        )
        errors = validate_dxf_lifecycle_context(context)
        assert errors == []
