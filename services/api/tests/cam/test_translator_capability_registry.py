"""
Tests for Translator Capability Registry (CAM Dev Order 7B + MRP-3A)

Tests the declarative translator capability registry and introspection endpoints.

Core invariants tested:
  7B entries (validation_only, execution_disabled):
    - execution_supported=False
    - artifact_generation_supported=False
    - machine_output_supported=False

  MRP-3A entries (governed_execution):
    - execution_supported=True
    - artifact_generation_supported=True
    - machine_output_supported=False (still no G-code)

  All entries:
    - machine_output_supported=False
    - No DXF/G-code tokens generated
    - Registry does not alter operation registry
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.cam.translator_capability_registry import (
    TranslatorCapability,
    TRANSLATOR_CAPABILITY_REGISTRY,
    get_translator_capability,
    list_translator_capabilities,
    list_translator_ids,
    list_translators_by_category,
    list_translators_by_output_class,
    list_translators_for_operation,
    list_governed_translators,
    list_execution_capable_translators,
)
from app.cam.cam_operation_registry import CAM_OPERATION_REGISTRY


client = TestClient(app)


# Helper to filter 7B-only entries
def get_7b_entries():
    """Get entries with 7B execution states (validation_only, execution_disabled)."""
    return [
        cap for cap in TRANSLATOR_CAPABILITY_REGISTRY.values()
        if cap.execution_state in ("validation_only", "execution_disabled")
    ]


def get_mrp3a_entries():
    """Get entries with MRP-3A governed_execution state."""
    return [
        cap for cap in TRANSLATOR_CAPABILITY_REGISTRY.values()
        if cap.execution_state == "governed_execution"
    ]


# -----------------------------------------------------------------------------
# Registry Existence Tests
# -----------------------------------------------------------------------------

class TestRegistryEntries:
    """Tests that required registry entries exist."""

    def test_dxf_r12_exists(self):
        """DXF R12 translator must be registered."""
        cap = get_translator_capability("dxf_r12")
        assert cap is not None
        assert cap.translator_id == "dxf_r12"
        assert cap.output_class == "dxf"
        assert cap.output_format_version == "R12"

    def test_dxf_r2000_exists(self):
        """DXF R2000 translator must be registered."""
        cap = get_translator_capability("dxf_r2000")
        assert cap is not None
        assert cap.translator_id == "dxf_r2000"
        assert cap.output_class == "dxf"
        assert cap.output_format_version == "R2000"

    def test_grbl_placeholder_exists(self):
        """GRBL placeholder must be registered."""
        cap = get_translator_capability("gcode_grbl_placeholder")
        assert cap is not None
        assert cap.translator_id == "gcode_grbl_placeholder"
        assert cap.output_class == "gcode"
        assert cap.translator_category == "postprocessor"

    def test_unsupported_translator_returns_none(self):
        """Unsupported translator ID must return None."""
        cap = get_translator_capability("nonexistent_translator")
        assert cap is None


# -----------------------------------------------------------------------------
# 7B Invariant Tests
# -----------------------------------------------------------------------------

class TestExecutionInvariants:
    """Tests that execution invariants are enforced by state."""

    def test_7b_entries_have_execution_supported_false(self):
        """7B entries (validation_only, execution_disabled) must have execution_supported=False."""
        for cap in get_7b_entries():
            assert cap.execution_supported is False, (
                f"Translator '{cap.translator_id}' has execution_supported=True, "
                f"violating 7B invariant for state '{cap.execution_state}'"
            )

    def test_7b_entries_have_artifact_generation_supported_false(self):
        """7B entries must have artifact_generation_supported=False."""
        for cap in get_7b_entries():
            assert cap.artifact_generation_supported is False, (
                f"Translator '{cap.translator_id}' has artifact_generation_supported=True, "
                f"violating 7B invariant for state '{cap.execution_state}'"
            )

    def test_all_entries_have_machine_output_supported_false(self):
        """All registry entries must have machine_output_supported=False."""
        for translator_id, cap in TRANSLATOR_CAPABILITY_REGISTRY.items():
            assert cap.machine_output_supported is False, (
                f"Translator '{translator_id}' has machine_output_supported=True"
            )

    def test_grbl_placeholder_execution_disabled(self):
        """GRBL placeholder must have execution_state='execution_disabled'."""
        cap = get_translator_capability("gcode_grbl_placeholder")
        assert cap.execution_state == "execution_disabled"

    def test_grbl_placeholder_empty_operations(self):
        """GRBL placeholder must have empty supported_operations."""
        cap = get_translator_capability("gcode_grbl_placeholder")
        assert cap.supported_operations == []

    def test_grbl_placeholder_maturity_is_placeholder(self):
        """GRBL placeholder must have maturity='placeholder'."""
        cap = get_translator_capability("gcode_grbl_placeholder")
        assert cap.maturity == "placeholder"


# -----------------------------------------------------------------------------
# MRP-3A Invariant Tests
# -----------------------------------------------------------------------------

class TestMRP3AInvariants:
    """Tests that MRP-3A governed translator invariants are enforced."""

    def test_governed_entries_have_execution_supported_true(self):
        """MRP-3A governed entries must have execution_supported=True."""
        governed = get_mrp3a_entries()
        assert len(governed) > 0, "Expected at least one governed translator"
        for cap in governed:
            assert cap.execution_supported is True, (
                f"Translator '{cap.translator_id}' has execution_supported=False, "
                f"violating MRP-3A invariant for governed_execution"
            )

    def test_governed_entries_have_artifact_generation_true(self):
        """MRP-3A governed entries must have artifact_generation_supported=True."""
        for cap in get_mrp3a_entries():
            assert cap.artifact_generation_supported is True, (
                f"Translator '{cap.translator_id}' has artifact_generation_supported=False, "
                f"violating MRP-3A invariant for governed_execution"
            )

    def test_governed_entries_still_no_machine_output(self):
        """MRP-3A governed entries must still have machine_output_supported=False."""
        for cap in get_mrp3a_entries():
            assert cap.machine_output_supported is False, (
                f"Translator '{cap.translator_id}' has machine_output_supported=True"
            )

    def test_governed_entries_have_governed_maturity(self):
        """MRP-3A governed entries must have maturity='governed' or higher."""
        for cap in get_mrp3a_entries():
            assert cap.maturity in ("governed", "canonical"), (
                f"Translator '{cap.translator_id}' has maturity='{cap.maturity}', "
                f"expected 'governed' or 'canonical' for governed_execution"
            )


# -----------------------------------------------------------------------------
# Model Validator Tests
# -----------------------------------------------------------------------------

class TestModelValidation:
    """Tests that model validators enforce invariants."""

    def test_validation_only_rejects_execution_supported_true(self):
        """validation_only state must reject execution_supported=True."""
        with pytest.raises(ValidationError) as exc_info:
            TranslatorCapability(
                translator_id="test_invalid",
                translator_name="Invalid Test",
                translator_category="translator",
                output_class="dxf",
                execution_state="validation_only",
                execution_supported=True,
            )
        assert "execution_supported must be False" in str(exc_info.value)

    def test_validation_only_rejects_artifact_generation_true(self):
        """validation_only state must reject artifact_generation_supported=True."""
        with pytest.raises(ValidationError) as exc_info:
            TranslatorCapability(
                translator_id="test_invalid",
                translator_name="Invalid Test",
                translator_category="translator",
                output_class="dxf",
                execution_state="validation_only",
                artifact_generation_supported=True,
            )
        assert "artifact_generation_supported must be False" in str(exc_info.value)

    def test_validation_only_rejects_machine_output_true(self):
        """validation_only state must reject machine_output_supported=True."""
        with pytest.raises(ValidationError) as exc_info:
            TranslatorCapability(
                translator_id="test_invalid",
                translator_name="Invalid Test",
                translator_category="translator",
                output_class="dxf",
                execution_state="validation_only",
                machine_output_supported=True,
            )
        assert "machine_output_supported must be False" in str(exc_info.value)

    def test_machine_output_always_rejected(self):
        """machine_output_supported=True must always be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TranslatorCapability(
                translator_id="test_invalid",
                translator_name="Invalid Test",
                translator_category="translator",
                output_class="dxf",
                execution_state="execution_planned",
                machine_output_supported=True,
            )
        assert "machine_output_supported must be False" in str(exc_info.value)

    def test_execution_disabled_rejects_execution_supported_true(self):
        """execution_disabled state must reject execution_supported=True."""
        with pytest.raises(ValidationError) as exc_info:
            TranslatorCapability(
                translator_id="test_invalid",
                translator_name="Invalid Test",
                translator_category="postprocessor",
                output_class="gcode",
                execution_state="execution_disabled",
                execution_supported=True,
            )
        assert "execution_supported must be False" in str(exc_info.value)

    def test_valid_translator_passes_validation(self):
        """Valid translator declaration must pass validation."""
        cap = TranslatorCapability(
            translator_id="test_valid",
            translator_name="Valid Test Translator",
            translator_category="translator",
            output_class="dxf",
            execution_state="validation_only",
            maturity="candidate",
            execution_supported=False,
            artifact_generation_supported=False,
            machine_output_supported=False,
        )
        assert cap.translator_id == "test_valid"


# -----------------------------------------------------------------------------
# Registry Helper Function Tests
# -----------------------------------------------------------------------------

class TestHelperFunctions:
    """Tests for registry helper functions."""

    def test_list_translator_capabilities(self):
        """list_translator_capabilities returns all entries."""
        caps = list_translator_capabilities()
        assert len(caps) == 5  # 3 original 7B + 2 MRP-3A
        ids = [c.translator_id for c in caps]
        assert "dxf_r12" in ids
        assert "dxf_r2000" in ids
        assert "gcode_grbl_placeholder" in ids
        assert "body_outline_dxf_r12" in ids
        assert "body_outline_dxf_r2000" in ids

    def test_list_translator_ids(self):
        """list_translator_ids returns all IDs."""
        ids = list_translator_ids()
        assert len(ids) == 5
        assert "dxf_r12" in ids
        assert "dxf_r2000" in ids
        assert "gcode_grbl_placeholder" in ids
        assert "body_outline_dxf_r12" in ids
        assert "body_outline_dxf_r2000" in ids

    def test_list_translators_by_category_translator(self):
        """list_translators_by_category filters translators."""
        translators = list_translators_by_category("translator")
        assert len(translators) == 4  # dxf_r12, dxf_r2000, body_outline_*
        for t in translators:
            assert t.translator_category == "translator"

    def test_list_translators_by_category_postprocessor(self):
        """list_translators_by_category filters postprocessors."""
        postprocessors = list_translators_by_category("postprocessor")
        assert len(postprocessors) == 1
        assert postprocessors[0].translator_id == "gcode_grbl_placeholder"

    def test_list_translators_by_output_class_dxf(self):
        """list_translators_by_output_class filters by DXF."""
        dxf_translators = list_translators_by_output_class("dxf")
        assert len(dxf_translators) == 4  # dxf_r12, dxf_r2000, body_outline_*
        for t in dxf_translators:
            assert t.output_class == "dxf"

    def test_list_translators_by_output_class_gcode(self):
        """list_translators_by_output_class filters by G-code."""
        gcode_translators = list_translators_by_output_class("gcode")
        assert len(gcode_translators) == 1
        assert gcode_translators[0].translator_id == "gcode_grbl_placeholder"

    def test_list_translators_for_operation_nut_slot(self):
        """list_translators_for_operation returns translators supporting nut_slot."""
        translators = list_translators_for_operation("nut_slot")
        assert len(translators) == 2
        ids = [t.translator_id for t in translators]
        assert "dxf_r12" in ids
        assert "dxf_r2000" in ids

    def test_list_translators_for_operation_body_profiling(self):
        """list_translators_for_operation returns MRP-3A translators for body_profiling."""
        translators = list_translators_for_operation("body_profiling")
        assert len(translators) == 2
        ids = [t.translator_id for t in translators]
        assert "body_outline_dxf_r12" in ids
        assert "body_outline_dxf_r2000" in ids

    def test_list_translators_for_operation_unsupported(self):
        """list_translators_for_operation returns empty for unsupported operation."""
        translators = list_translators_for_operation("nonexistent_operation")
        assert translators == []

    def test_list_governed_translators(self):
        """list_governed_translators returns MRP-3A governed entries."""
        governed = list_governed_translators()
        assert len(governed) == 2
        for t in governed:
            assert t.execution_state == "governed_execution"

    def test_list_execution_capable_translators(self):
        """list_execution_capable_translators returns only execution-capable entries."""
        capable = list_execution_capable_translators()
        assert len(capable) == 2  # Only MRP-3A body outline translators
        for t in capable:
            assert t.execution_supported is True


# -----------------------------------------------------------------------------
# Registry Isolation Tests
# -----------------------------------------------------------------------------

class TestRegistryIsolation:
    """Tests that translator registry does not affect operation registry."""

    def test_operation_registry_unchanged(self):
        """CAM_OPERATION_REGISTRY must not be affected by translator registry."""
        assert "nut_slot" in CAM_OPERATION_REGISTRY
        assert "drilling" in CAM_OPERATION_REGISTRY

    def test_registries_are_separate(self):
        """Translator and operation registries must be separate dictionaries."""
        assert TRANSLATOR_CAPABILITY_REGISTRY is not CAM_OPERATION_REGISTRY

    def test_translator_registry_does_not_contain_operations(self):
        """Translator registry must not contain operation IDs as keys."""
        for op_id in CAM_OPERATION_REGISTRY.keys():
            assert op_id not in TRANSLATOR_CAPABILITY_REGISTRY


# -----------------------------------------------------------------------------
# No Execution Token Tests
# -----------------------------------------------------------------------------

class TestNoExecutionTokens:
    """Tests that no DXF/G-code tokens are generated."""

    def test_no_dxf_content_in_registry(self):
        """Registry entries must not contain DXF content strings."""
        for cap in list_translator_capabilities():
            cap_str = cap.model_dump_json()
            assert "SECTION" not in cap_str
            assert "ENTITIES" not in cap_str
            assert "ENDSEC" not in cap_str
            assert "LINE" not in cap_str or "polyline" in cap_str.lower()

    def test_no_gcode_content_in_registry(self):
        """Registry entries must not contain G-code content strings."""
        for cap in list_translator_capabilities():
            cap_str = cap.model_dump_json()
            assert "G00" not in cap_str
            assert "G01" not in cap_str
            assert "G90" not in cap_str
            assert "M03" not in cap_str


# -----------------------------------------------------------------------------
# Endpoint Tests
# -----------------------------------------------------------------------------

class TestEndpoints:
    """Tests for translator capability endpoints."""

    def test_list_capabilities_endpoint(self):
        """GET /api/cam/translators/capabilities returns all capabilities."""
        response = client.get("/api/cam/translators/capabilities")
        assert response.status_code == 200
        data = response.json()
        assert "translators" in data
        assert "total_count" in data
        assert data["total_count"] == 5  # 3 original + 2 MRP-3A
        assert data["translator_count"] == 4
        assert data["postprocessor_count"] == 1

    def test_list_capabilities_summary_endpoint(self):
        """GET /api/cam/translators/capabilities/summary returns summaries."""
        response = client.get("/api/cam/translators/capabilities/summary")
        assert response.status_code == 200
        data = response.json()
        assert "translators" in data
        assert len(data["translators"]) == 5

    def test_get_capability_endpoint_dxf_r12(self):
        """GET /api/cam/translators/capabilities/dxf_r12 returns entry."""
        response = client.get("/api/cam/translators/capabilities/dxf_r12")
        assert response.status_code == 200
        data = response.json()
        assert data["translator_id"] == "dxf_r12"
        assert data["output_class"] == "dxf"
        assert data["execution_supported"] is False

    def test_get_capability_endpoint_not_found(self):
        """GET /api/cam/translators/capabilities/nonexistent returns 404."""
        response = client.get("/api/cam/translators/capabilities/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_list_ids_endpoint(self):
        """GET /api/cam/translators/ids returns all IDs."""
        response = client.get("/api/cam/translators/ids")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        assert "dxf_r12" in data
        assert "dxf_r2000" in data
        assert "gcode_grbl_placeholder" in data
        assert "body_outline_dxf_r12" in data
        assert "body_outline_dxf_r2000" in data

    def test_by_category_translator_endpoint(self):
        """GET /api/cam/translators/by-category/translator returns translators."""
        response = client.get("/api/cam/translators/by-category/translator")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4  # dxf_r12, dxf_r2000, body_outline_*
        for entry in data:
            assert entry["translator_category"] == "translator"

    def test_by_category_postprocessor_endpoint(self):
        """GET /api/cam/translators/by-category/postprocessor returns postprocessors."""
        response = client.get("/api/cam/translators/by-category/postprocessor")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["translator_id"] == "gcode_grbl_placeholder"

    def test_by_output_dxf_endpoint(self):
        """GET /api/cam/translators/by-output/dxf returns DXF translators."""
        response = client.get("/api/cam/translators/by-output/dxf")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4  # dxf_r12, dxf_r2000, body_outline_*
        for entry in data:
            assert entry["output_class"] == "dxf"

    def test_by_output_gcode_endpoint(self):
        """GET /api/cam/translators/by-output/gcode returns G-code postprocessors."""
        response = client.get("/api/cam/translators/by-output/gcode")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["translator_id"] == "gcode_grbl_placeholder"

    def test_for_operation_nut_slot_endpoint(self):
        """GET /api/cam/translators/for-operation/nut_slot returns supporting translators."""
        response = client.get("/api/cam/translators/for-operation/nut_slot")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        ids = [entry["translator_id"] for entry in data]
        assert "dxf_r12" in ids
        assert "dxf_r2000" in ids

    def test_for_operation_unsupported_endpoint(self):
        """GET /api/cam/translators/for-operation/unsupported returns empty list."""
        response = client.get("/api/cam/translators/for-operation/unsupported")
        assert response.status_code == 200
        data = response.json()
        assert data == []


# -----------------------------------------------------------------------------
# Authorization Field Tests
# -----------------------------------------------------------------------------

class TestAuthorizationField:
    """Tests for the authorization_required field."""

    def test_7b_entries_require_authorization(self):
        """7B entries must have authorization_required=True."""
        for cap in get_7b_entries():
            assert cap.authorization_required is True, (
                f"Translator '{cap.translator_id}' has authorization_required=False"
            )

    def test_governed_entries_may_skip_authorization(self):
        """MRP-3A governed entries may have authorization_required=False."""
        governed = get_mrp3a_entries()
        assert len(governed) > 0, "Expected at least one governed translator"
        # MRP-3A entries explicitly set authorization_required=False
        # because governance approval is implicit in governed_execution state
        for cap in governed:
            assert cap.authorization_required is False, (
                f"Translator '{cap.translator_id}' should have authorization_required=False "
                f"for governed_execution (governance approval is implicit)"
            )
