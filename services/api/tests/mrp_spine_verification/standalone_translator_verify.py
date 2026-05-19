#!/usr/bin/env python3
"""
MRP-3A: Standalone Translator Verification Script

Runs outside pytest to avoid Python 3.14/numpy module reload conflict.
Verifies the governed DXF translator produces valid output.
"""

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.cam.translators.dxf.body_outline_translator import (
    BodyOutlineDxfTranslator,
    create_r12_translator,
    create_r2000_translator,
    DXF_R12_TRANSLATOR_ID,
    DXF_R2000_TRANSLATOR_ID,
)
from app.cam.translators.base import TranslatorErrorCode
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


def make_dreadnought_export_object() -> BodyExportObject:
    """Create a realistic dreadnought body export object."""
    points = [
        [-200.0, 0.0],
        [-200.0, 150.0],
        [-180.0, 250.0],
        [-115.0, 350.0],
        [-115.0, 400.0],
        [-130.0, 450.0],
        [-140.0, 500.0],
        [0.0, 510.0],
        [140.0, 500.0],
        [130.0, 450.0],
        [115.0, 400.0],
        [115.0, 350.0],
        [180.0, 250.0],
        [200.0, 150.0],
        [200.0, 0.0],
        [-200.0, 0.0],
    ]

    entities = [
        GeometryEntity(
            type="closed_contour",
            id="body_outer",
            role="outer",
            winding="ccw",
            points=points,
        ),
    ]

    return BodyExportObject(
        schema_version="1.0.0",
        export_id="EXP-BODY-20260513-dread001",
        export_type="geometry",
        metadata=ExportMetadata(
            export_id="EXP-BODY-20260513-dread001",
            schema_version="1.0.0",
            created_at=datetime.now(timezone.utc).isoformat(),
            source=ExportSource(
                preview_id="boe_test",
                preview_hash="dread_hash_001",
            ),
        ),
        geometry=ExportGeometry(
            coordinate_system=CoordinateSystem(),
            bounds=Bounds(
                x_min=-200.0, x_max=200.0,
                y_min=0.0, y_max=510.0,
            ),
            entities=entities,
        ),
        validation=ExportValidation(
            gate_status="green",
            preview_gate="green",
            export_gate="green",
            checks_performed=[
                ValidationCheck(check="has_points", result="passed"),
                ValidationCheck(check="contour_closed", result="passed"),
            ],
            source_preview_hash="dread_hash_001",
        ),
        intent=ExportIntent(),
        extensions=ExportExtensions(
            ibg_morphology=IBGMorphologyExtension(
                session_id="ibg-dread-001",
                confidence=0.95,
                dimensions={
                    "lower_bout_width_mm": 400.0,
                    "upper_bout_width_mm": 280.0,
                    "waist_width_mm": 230.0,
                    "body_length_mm": 510.0,
                },
                instrument_spec="dreadnought",
            )
        ),
    )


def make_red_gate_export_object() -> BodyExportObject:
    """Create export object with red gate for rejection test."""
    export_obj = make_dreadnought_export_object()
    export_obj.validation.gate_status = "red"
    export_obj.validation.preview_gate = "red"
    export_obj.validation.export_gate = "red"
    export_obj.validation.issues = ["Test failure condition"]
    return export_obj


def verify_r12_translation():
    """Verify R12 translator produces valid output."""
    print("\n=== R12 Translator Verification ===")

    translator = create_r12_translator()
    print(f"Translator ID: {translator.translator_id}")
    print(f"Version: {translator.translator_version}")
    print(f"DXF Version: {translator.dxf_version}")

    export_obj = make_dreadnought_export_object()
    print(f"\nExport Object: {export_obj.export_id}")
    print(f"Gate Status: {export_obj.validation.gate_status}")

    print("\nCan translate check...")
    can_translate = translator.can_translate(export_obj)
    print(f"can_translate: {can_translate}")
    assert can_translate, "R12 translator should accept geometry export"

    print("\nTranslating...")
    result = translator.translate(export_obj)

    print(f"\nResult:")
    print(f"  success: {result.success}")
    print(f"  output_format: {result.output_format}")
    print(f"  has_output: {result.has_output}")
    print(f"  errors: {len(result.errors)}")
    print(f"  warnings: {len(result.warnings)}")

    assert result.success, f"Translation should succeed: {result.errors}"
    assert result.has_output, "Should produce output bytes"
    assert result.output_format == "dxf_r12", "Should be R12 format"

    print(f"\nStatistics:")
    for key, value in result.statistics.items():
        print(f"  {key}: {value}")

    print(f"\nProvenance:")
    print(f"  export_id: {result.provenance.export_id}")
    print(f"  translator_id: {result.provenance.translator_id}")
    print(f"  ibg_session_id: {result.provenance.ibg_session_id}")
    print(f"  instrument_spec: {result.provenance.instrument_spec}")

    assert result.provenance.ibg_session_id == "ibg-dread-001"
    assert result.provenance.instrument_spec == "dreadnought"

    output_str = result.output_bytes.decode("utf-8")
    print(f"\nDXF Output (first 500 chars):")
    print(output_str[:500])

    assert "SECTION" in output_str, "DXF should contain SECTION"
    assert "ENTITIES" in output_str, "DXF should contain ENTITIES"
    assert "EOF" in output_str, "DXF should contain EOF"
    assert "BODY_OUTLINE" in output_str, "DXF should contain BODY_OUTLINE layer"

    print("\nPASSED: R12 Translation: VERIFIED")
    return True


def verify_r2000_translation():
    """Verify R2000 translator produces valid output."""
    print("\n=== R2000 Translator Verification ===")

    translator = create_r2000_translator()
    print(f"Translator ID: {translator.translator_id}")
    print(f"DXF Version: {translator.dxf_version}")

    export_obj = make_dreadnought_export_object()

    result = translator.translate(export_obj)

    assert result.success, f"Translation should succeed: {result.errors}"
    assert result.has_output, "Should produce output bytes"
    assert result.output_format == "dxf_r2000", "Should be R2000 format"

    print(f"  success: {result.success}")
    print(f"  output_format: {result.output_format}")
    print(f"  output_size: {result.statistics.get('output_size_bytes', 0)} bytes")

    print("\nPASSED: R2000 Translation: VERIFIED")
    return True


def verify_red_gate_rejection():
    """Verify red gate blocks translation."""
    print("\n=== Red Gate Rejection Verification ===")

    translator = create_r12_translator()
    export_obj = make_red_gate_export_object()

    print(f"Export Object gate: {export_obj.validation.gate_status}")

    result = translator.translate(export_obj)

    print(f"  success: {result.success}")
    print(f"  has_output: {result.has_output}")
    print(f"  errors: {len(result.errors)}")

    assert not result.success, "Red gate should block translation"
    assert not result.has_output, "Should not produce output"
    assert len(result.errors) == 1, "Should have exactly one error"
    assert result.errors[0].code == TranslatorErrorCode.GATE_RED

    print(f"  error_code: {result.errors[0].code}")
    print(f"  error_message: {result.errors[0].message}")

    print("\nPASSED: Red Gate Rejection: VERIFIED")
    return True


def verify_dxf_file_output():
    """Verify DXF can be written to file."""
    print("\n=== DXF File Output Verification ===")

    translator = create_r12_translator()
    export_obj = make_dreadnought_export_object()
    result = translator.translate(export_obj)

    with tempfile.NamedTemporaryFile(
        suffix="_dread_r12.dxf",
        delete=False,
        mode="wb",
    ) as f:
        f.write(result.output_bytes)
        output_path = f.name

    file_size = Path(output_path).stat().st_size
    print(f"  Output file: {output_path}")
    print(f"  File size: {file_size} bytes")

    assert file_size > 0, "File should not be empty"

    with open(output_path, "r") as f:
        content = f.read()

    assert "BODY_OUTLINE" in content
    assert "PROVENANCE" in content
    assert "Export ID:" in content

    print("\nPASSED: DXF File Output: VERIFIED")
    return output_path


def verify_capability_registry():
    """Verify translators are in capability registry."""
    print("\n=== Capability Registry Verification ===")

    from app.cam.translator_capability_registry import (
        get_translator_capability,
        list_governed_translators,
    )

    r12_cap = get_translator_capability(DXF_R12_TRANSLATOR_ID)
    r2000_cap = get_translator_capability(DXF_R2000_TRANSLATOR_ID)

    assert r12_cap is not None, "R12 should be in registry"
    assert r2000_cap is not None, "R2000 should be in registry"

    print(f"R12 Capability:")
    print(f"  execution_state: {r12_cap.execution_state}")
    print(f"  execution_supported: {r12_cap.execution_supported}")
    print(f"  maturity: {r12_cap.maturity}")

    assert r12_cap.execution_state == "governed_execution"
    assert r12_cap.execution_supported is True
    assert r12_cap.maturity == "governed"

    print(f"\nR2000 Capability:")
    print(f"  execution_state: {r2000_cap.execution_state}")
    print(f"  execution_supported: {r2000_cap.execution_supported}")
    print(f"  maturity: {r2000_cap.maturity}")

    assert r2000_cap.execution_state == "governed_execution"
    assert r2000_cap.execution_supported is True
    assert r2000_cap.maturity == "governed"

    governed = list_governed_translators()
    governed_ids = [t.translator_id for t in governed]
    assert DXF_R12_TRANSLATOR_ID in governed_ids
    assert DXF_R2000_TRANSLATOR_ID in governed_ids

    print(f"\nGoverned translators: {governed_ids}")

    print("\nPASSED: Capability Registry: VERIFIED")
    return True


def main():
    """Run all translator verifications."""
    print("=" * 60)
    print("MRP-3A: Standalone Translator Verification")
    print("=" * 60)

    results = {}

    try:
        results["r12_translation"] = verify_r12_translation()
    except Exception as e:
        print(f"\nFAILED: R12 Translation FAILED: {e}")
        results["r12_translation"] = False

    try:
        results["r2000_translation"] = verify_r2000_translation()
    except Exception as e:
        print(f"\nFAILED: R2000 Translation FAILED: {e}")
        results["r2000_translation"] = False

    try:
        results["red_gate_rejection"] = verify_red_gate_rejection()
    except Exception as e:
        print(f"\nFAILED: Red Gate Rejection FAILED: {e}")
        results["red_gate_rejection"] = False

    try:
        output_path = verify_dxf_file_output()
        results["dxf_file_output"] = True
    except Exception as e:
        print(f"\nFAILED: DXF File Output FAILED: {e}")
        results["dxf_file_output"] = False

    try:
        results["capability_registry"] = verify_capability_registry()
    except Exception as e:
        print(f"\nFAILED: Capability Registry FAILED: {e}")
        results["capability_registry"] = False

    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    all_passed = True
    for test, passed in results.items():
        status = "VERIFIED" if passed else "FAILED"
        print(f"  {test}: {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\nPASSED: MRP-3A TRANSLATOR LAYER: VERIFIED")
        print("\nThe translator era has begun. Export Objects now have a")
        print("governed downstream path to DXF output.")
        return 0
    else:
        print("\nFAILED: MRP-3A VERIFICATION: INCOMPLETE")
        return 1


if __name__ == "__main__":
    sys.exit(main())
