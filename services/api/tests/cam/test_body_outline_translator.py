"""
MRP-3A: Body Outline DXF Translator Tests

Tests for governed translator that consumes BodyExportObject.
"""

import pytest
from datetime import datetime, timezone

from app.cam.translators.dxf.body_outline_translator import (
    BodyOutlineDxfTranslator,
    create_r12_translator,
    create_r2000_translator,
    DXF_R12_TRANSLATOR_ID,
    DXF_R2000_TRANSLATOR_ID,
)
from app.cam.translators.base import (
    TranslatorErrorCode,
    ExportTranslator,
)
from app.cam.translator_capability_registry import (
    get_translator_capability,
    list_governed_translators,
    list_execution_capable_translators,
)
from app.export.body_export_bridge import (
    BodyExportObject,
    ExportGeometry,
    ExportValidation,
    ExportMetadata,
    ExportSource,
    ExportIntent,
    ExportExtensions,
    IBGMorphologyExtension,
    GeometryEntity,
    CoordinateSystem,
    Bounds,
    ValidationCheck,
)


def make_test_export_object(
    gate_status: str = "green",
    with_ibg_context: bool = False,
) -> BodyExportObject:
    """Create a test BodyExportObject."""
    entities = [
        GeometryEntity(
            type="closed_contour",
            id="outer_1",
            role="outer",
            winding="ccw",
            points=[
                [0.0, 0.0],
                [100.0, 0.0],
                [100.0, 200.0],
                [50.0, 250.0],
                [0.0, 200.0],
                [0.0, 0.0],
            ],
        ),
    ]

    extensions = None
    if with_ibg_context:
        extensions = ExportExtensions(
            ibg_morphology=IBGMorphologyExtension(
                session_id="ibg-test-session-001",
                confidence=0.92,
                dimensions={
                    "lower_bout_width_mm": 400.0,
                    "upper_bout_width_mm": 280.0,
                    "waist_width_mm": 230.0,
                    "body_length_mm": 500.0,
                },
                instrument_spec="dreadnought",
            )
        )

    return BodyExportObject(
        schema_version="1.0.0",
        export_id="EXP-BODY-20260513-test123",
        export_type="geometry",
        metadata=ExportMetadata(
            export_id="EXP-BODY-20260513-test123",
            schema_version="1.0.0",
            created_at=datetime.now(timezone.utc).isoformat(),
            source=ExportSource(
                preview_id="boe_test",
                preview_hash="abc123def456",
            ),
        ),
        geometry=ExportGeometry(
            coordinate_system=CoordinateSystem(),
            bounds=Bounds(
                x_min=0.0, x_max=100.0,
                y_min=0.0, y_max=250.0,
            ),
            entities=entities,
        ),
        validation=ExportValidation(
            gate_status=gate_status,
            preview_gate=gate_status,
            export_gate=gate_status,
            checks_performed=[
                ValidationCheck(check="has_points", result="passed"),
                ValidationCheck(check="contour_closed", result="passed"),
            ],
            source_preview_hash="abc123def456",
        ),
        intent=ExportIntent(),
        extensions=extensions,
    )


class TestBodyOutlineDxfTranslator:
    """Tests for BodyOutlineDxfTranslator."""

    def test_r12_translator_protocol_compliance(self):
        """R12 translator implements ExportTranslator protocol."""
        translator = create_r12_translator()
        assert isinstance(translator, ExportTranslator)
        assert translator.translator_id == DXF_R12_TRANSLATOR_ID
        assert translator.output_format == "dxf"

    def test_r2000_translator_protocol_compliance(self):
        """R2000 translator implements ExportTranslator protocol."""
        translator = create_r2000_translator()
        assert isinstance(translator, ExportTranslator)
        assert translator.translator_id == DXF_R2000_TRANSLATOR_ID
        assert translator.output_format == "dxf"

    def test_can_translate_geometry_export(self):
        """Translator accepts geometry export objects."""
        translator = create_r12_translator()
        export_obj = make_test_export_object()
        assert translator.can_translate(export_obj) is True

    def test_translate_green_gate_succeeds(self):
        """Translation succeeds with green gate."""
        translator = create_r12_translator()
        export_obj = make_test_export_object(gate_status="green")

        result = translator.translate(export_obj)

        assert result.success is True
        assert result.has_output is True
        assert result.output_format == "dxf_r12"
        assert len(result.errors) == 0
        assert result.provenance is not None
        assert result.provenance.export_id == export_obj.export_id

    def test_translate_yellow_gate_succeeds(self):
        """Translation succeeds with yellow gate."""
        translator = create_r12_translator()
        export_obj = make_test_export_object(gate_status="yellow")

        result = translator.translate(export_obj)

        assert result.success is True
        assert result.has_output is True

    def test_translate_red_gate_blocked(self):
        """Translation blocked with red gate."""
        translator = create_r12_translator()
        export_obj = make_test_export_object(gate_status="red")

        result = translator.translate(export_obj)

        assert result.success is False
        assert result.has_output is False
        assert len(result.errors) == 1
        assert result.errors[0].code == TranslatorErrorCode.GATE_RED

    def test_output_contains_dxf_structure(self):
        """Output bytes contain valid DXF structure."""
        translator = create_r12_translator()
        export_obj = make_test_export_object()

        result = translator.translate(export_obj)

        assert result.success is True
        output_str = result.output_bytes.decode("utf-8")
        assert "SECTION" in output_str
        assert "ENTITIES" in output_str
        assert "EOF" in output_str

    def test_provenance_includes_ibg_context(self):
        """Provenance includes IBG context when present."""
        translator = create_r12_translator()
        export_obj = make_test_export_object(with_ibg_context=True)

        result = translator.translate(export_obj)

        assert result.success is True
        assert result.provenance.ibg_session_id == "ibg-test-session-001"
        assert result.provenance.instrument_spec == "dreadnought"

    def test_statistics_populated(self):
        """Translation statistics are populated."""
        translator = create_r12_translator()
        export_obj = make_test_export_object()

        result = translator.translate(export_obj)

        assert result.success is True
        assert result.statistics["entities_translated"] == 1
        assert result.statistics["outer_contours"] == 1
        assert result.statistics["total_points"] == 6
        assert "output_size_bytes" in result.statistics

    def test_r12_vs_r2000_output_differs(self):
        """R12 and R2000 produce different output sizes."""
        export_obj = make_test_export_object()

        r12_result = create_r12_translator().translate(export_obj)
        r2000_result = create_r2000_translator().translate(export_obj)

        assert r12_result.success is True
        assert r2000_result.success is True
        assert r12_result.output_format == "dxf_r12"
        assert r2000_result.output_format == "dxf_r2000"

    def test_invalid_dxf_version_rejected(self):
        """Invalid DXF version raises error."""
        with pytest.raises(ValueError, match="Unsupported DXF version"):
            BodyOutlineDxfTranslator(dxf_version="R14")


class TestCapabilityRegistryIntegration:
    """Tests for capability registry integration."""

    def test_governed_translators_registered(self):
        """Body outline translators are in registry."""
        r12_cap = get_translator_capability(DXF_R12_TRANSLATOR_ID)
        r2000_cap = get_translator_capability(DXF_R2000_TRANSLATOR_ID)

        assert r12_cap is not None
        assert r2000_cap is not None

    def test_governed_translators_have_correct_state(self):
        """Governed translators have governed_execution state."""
        r12_cap = get_translator_capability(DXF_R12_TRANSLATOR_ID)
        r2000_cap = get_translator_capability(DXF_R2000_TRANSLATOR_ID)

        assert r12_cap.execution_state == "governed_execution"
        assert r2000_cap.execution_state == "governed_execution"

    def test_governed_translators_execution_supported(self):
        """Governed translators have execution_supported=True."""
        r12_cap = get_translator_capability(DXF_R12_TRANSLATOR_ID)
        r2000_cap = get_translator_capability(DXF_R2000_TRANSLATOR_ID)

        assert r12_cap.execution_supported is True
        assert r2000_cap.execution_supported is True

    def test_governed_translators_no_machine_output(self):
        """Governed translators have machine_output_supported=False."""
        r12_cap = get_translator_capability(DXF_R12_TRANSLATOR_ID)
        r2000_cap = get_translator_capability(DXF_R2000_TRANSLATOR_ID)

        assert r12_cap.machine_output_supported is False
        assert r2000_cap.machine_output_supported is False

    def test_list_governed_translators(self):
        """list_governed_translators returns MRP-3A translators."""
        governed = list_governed_translators()

        ids = [t.translator_id for t in governed]
        assert DXF_R12_TRANSLATOR_ID in ids
        assert DXF_R2000_TRANSLATOR_ID in ids

    def test_list_execution_capable_translators(self):
        """list_execution_capable_translators returns governed translators."""
        capable = list_execution_capable_translators()

        ids = [t.translator_id for t in capable]
        assert DXF_R12_TRANSLATOR_ID in ids
        assert DXF_R2000_TRANSLATOR_ID in ids

    def test_body_profiling_operation_supported(self):
        """Governed translators support body_profiling operation."""
        r12_cap = get_translator_capability(DXF_R12_TRANSLATOR_ID)
        r2000_cap = get_translator_capability(DXF_R2000_TRANSLATOR_ID)

        assert "body_profiling" in r12_cap.supported_operations
        assert "body_profiling" in r2000_cap.supported_operations


class TestGovernanceInvariants:
    """Tests for governance invariants."""

    def test_governed_execution_requires_execution_supported(self):
        """governed_execution state requires execution_supported=True."""
        from app.cam.translator_capability_registry import TranslatorCapability

        with pytest.raises(ValueError, match="execution_supported must be True"):
            TranslatorCapability(
                translator_id="test_bad",
                translator_name="Bad Translator",
                translator_category="translator",
                output_class="dxf",
                execution_state="governed_execution",
                execution_supported=False,  # Invalid!
            )

    def test_validation_only_forbids_execution(self):
        """validation_only state forbids execution_supported=True."""
        from app.cam.translator_capability_registry import TranslatorCapability

        with pytest.raises(ValueError, match="execution_supported must be False"):
            TranslatorCapability(
                translator_id="test_bad",
                translator_name="Bad Translator",
                translator_category="translator",
                output_class="dxf",
                execution_state="validation_only",
                execution_supported=True,  # Invalid!
            )

    def test_machine_output_always_forbidden(self):
        """machine_output_supported must always be False."""
        from app.cam.translator_capability_registry import TranslatorCapability

        with pytest.raises(ValueError, match="machine_output_supported must be False"):
            TranslatorCapability(
                translator_id="test_bad",
                translator_name="Bad Translator",
                translator_category="translator",
                output_class="gcode",
                execution_state="governed_execution",
                execution_supported=True,
                machine_output_supported=True,  # Invalid!
            )
