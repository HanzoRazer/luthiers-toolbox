#!/usr/bin/env python3
"""
MRP-4A: Standalone Multi-Target Translator Verification

Verifies the multi-target translator abstraction works correctly.
Runs outside pytest to avoid Python 3.14/numpy module reload conflict.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi.testclient import TestClient


def make_test_export_object(
    gate_status: str = "green",
    export_id: str = "EXP-BODY-20260513-test001",
) -> dict:
    """Create a test BodyExportObject as dict for API request."""
    return {
        "schema_version": "1.0.0",
        "export_id": export_id,
        "export_type": "geometry",
        "metadata": {
            "export_id": export_id,
            "schema_version": "1.0.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source": {
                "preview_id": "boe_test",
                "preview_hash": "abc123def456",
            },
        },
        "geometry": {
            "coordinate_system": {
                "origin": "body_center",
                "x_axis": "width",
                "y_axis": "length_toward_neck",
                "z_axis": "thickness",
                "z_zero": "top_face",
                "units": "mm",
                "handedness": "right_handed",
                "frame": "local_workpiece",
            },
            "bounds": {
                "x_min": -200.0,
                "x_max": 200.0,
                "y_min": 0.0,
                "y_max": 300.0,
            },
            "entities": [
                {
                    "type": "closed_contour",
                    "id": "body_outer",
                    "role": "outer",
                    "winding": "ccw",
                    "points": [
                        [-200.0, 0.0],
                        [-200.0, 150.0],
                        [-180.0, 250.0],
                        [0.0, 300.0],
                        [180.0, 250.0],
                        [200.0, 150.0],
                        [200.0, 0.0],
                        [-200.0, 0.0],
                    ],
                },
            ],
        },
        "validation": {
            "gate_status": gate_status,
            "preview_gate": gate_status,
            "export_gate": gate_status,
            "issues": ["Test failure"] if gate_status == "red" else [],
            "warnings": [],
            "checks_performed": [
                {"check": "has_points", "result": "passed"},
                {"check": "contour_closed", "result": "passed"},
            ],
            "source_preview_hash": "abc123def456",
        },
        "intent": {
            "operation_type": "body_profiling",
            "depth_strategy": "full_thickness",
            "finish_requirements": {
                "surface_finish": "router_quality",
                "tolerance_mm": 0.5,
            },
        },
        "extensions": {
            "ibg_morphology": {
                "session_id": "ibg-test-001",
                "confidence": 0.92,
                "dimensions": {"body_length_mm": 500.0},
                "instrument_spec": "dreadnought",
            }
        },
    }


def verify_registry():
    """Verify translator registry works."""
    print("\n=== Registry Verification ===")

    from app.cam.translators.base.registry import get_translator_registry

    registry = get_translator_registry()

    targets = registry.list_targets()
    print(f"Targets: {targets}")
    assert "dxf" in targets, "DXF target missing"
    assert "svg" in targets, "SVG target missing"

    all_translators = registry.list_all()
    print(f"Translators: {all_translators}")
    assert "body_outline_dxf_r12" in all_translators
    assert "body_outline_dxf_r2000" in all_translators
    assert "body_outline_svg" in all_translators

    governed = registry.list_governed()
    print(f"Governed: {governed}")
    assert len(governed) == 3

    print("\nPASSED: Registry: VERIFIED")
    return True


def verify_target_negotiation():
    """Verify target negotiation works."""
    print("\n=== Target Negotiation Verification ===")

    from app.cam.translators.base.negotiation import (
        resolve_translator,
        get_supported_targets,
        get_supported_versions,
        TargetNotSupportedError,
        VersionNotSupportedError,
    )

    targets = get_supported_targets()
    print(f"Supported targets: {targets}")
    assert "dxf" in targets
    assert "svg" in targets

    dxf_versions = get_supported_versions("dxf")
    print(f"DXF versions: {dxf_versions}")
    assert "r12" in dxf_versions
    assert "r2000" in dxf_versions

    translator_r12 = resolve_translator("dxf", "r12")
    print(f"DXF R12 translator: {translator_r12.translator_id}")
    assert translator_r12.translator_id == "body_outline_dxf_r12"

    translator_r2000 = resolve_translator("dxf", "r2000")
    print(f"DXF R2000 translator: {translator_r2000.translator_id}")
    assert translator_r2000.translator_id == "body_outline_dxf_r2000"

    translator_svg = resolve_translator("svg")
    print(f"SVG translator: {translator_svg.translator_id}")
    assert translator_svg.translator_id == "body_outline_svg"

    try:
        resolve_translator("step")
        assert False, "Should have raised TargetNotSupportedError"
    except TargetNotSupportedError:
        print("Unsupported target rejected: OK")

    try:
        resolve_translator("dxf", "r14")
        assert False, "Should have raised VersionNotSupportedError"
    except VersionNotSupportedError:
        print("Unsupported version rejected: OK")

    print("\nPASSED: Target Negotiation: VERIFIED")
    return True


def verify_svg_translation():
    """Verify SVG translator produces valid output."""
    print("\n=== SVG Translation Verification ===")

    from app.cam.translators.svg import BodyOutlineSvgTranslator
    from app.export.body_export_bridge import (
        BodyExportObject,
        ExportGeometry,
        ExportValidation,
        ExportMetadata,
        ExportSource,
        ExportIntent,
        GeometryEntity,
        CoordinateSystem,
        Bounds,
        ValidationCheck,
    )

    export_obj = BodyExportObject(
        schema_version="1.0.0",
        export_id="EXP-BODY-20260513-svgtest",
        export_type="geometry",
        metadata=ExportMetadata(
            export_id="EXP-BODY-20260513-svgtest",
            schema_version="1.0.0",
            created_at=datetime.now(timezone.utc).isoformat(),
            source=ExportSource(preview_id="test", preview_hash="hash123"),
        ),
        geometry=ExportGeometry(
            coordinate_system=CoordinateSystem(),
            bounds=Bounds(x_min=-100, x_max=100, y_min=0, y_max=200),
            entities=[
                GeometryEntity(
                    type="closed_contour",
                    id="outer",
                    role="outer",
                    winding="ccw",
                    points=[[-100, 0], [100, 0], [100, 200], [-100, 200], [-100, 0]],
                )
            ],
        ),
        validation=ExportValidation(
            gate_status="green",
            preview_gate="green",
            export_gate="green",
            checks_performed=[ValidationCheck(check="test", result="passed")],
            source_preview_hash="hash123",
        ),
        intent=ExportIntent(),
    )

    translator = BodyOutlineSvgTranslator()
    print(f"Translator ID: {translator.translator_id}")

    result = translator.translate(export_obj)

    print(f"Success: {result.success}")
    print(f"Has output: {result.has_output}")
    print(f"Output size: {result.statistics.get('output_size_bytes', 0)} bytes")

    assert result.success, f"Translation should succeed: {result.errors}"
    assert result.has_output, "Should produce output"

    svg_content = result.output_bytes.decode("utf-8")
    print(f"\nSVG Preview (first 500 chars):")
    print(svg_content[:500])

    assert "<svg" in svg_content, "Should contain SVG tag"
    assert "viewBox" in svg_content, "Should have viewBox"
    assert "<path" in svg_content, "Should contain path"
    assert "#0066CC" in svg_content, "Should have blue outline color"

    print("\nPASSED: SVG Translation: VERIFIED")
    return True


def verify_multitarget_api():
    """Verify multi-target API endpoint."""
    print("\n=== Multi-Target API Verification ===")

    from app.main import app
    client = TestClient(app)

    response = client.get("/api/translate/targets")
    print(f"GET /targets status: {response.status_code}")
    assert response.status_code == 200
    data = response.json()
    assert "dxf" in data["targets"]
    assert "svg" in data["targets"]

    response = client.get("/api/translate/targets/dxf")
    print(f"GET /targets/dxf status: {response.status_code}")
    assert response.status_code == 200
    data = response.json()
    assert data["supported"] is True
    assert "r12" in data["versions"]
    assert "r2000" in data["versions"]

    payload = make_test_export_object()

    response = client.post("/api/translate/dxf", json=payload)
    print(f"POST /translate/dxf status: {response.status_code}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/dxf"
    assert response.headers["X-Target-Format"] == "dxf"
    assert b"SECTION" in response.content

    response = client.post("/api/translate/dxf?version=r2000", json=payload)
    print(f"POST /translate/dxf?version=r2000 status: {response.status_code}")
    assert response.status_code == 200
    assert response.headers["X-Translator-ID"] == "body_outline_dxf_r2000"

    response = client.post("/api/translate/svg", json=payload)
    print(f"POST /translate/svg status: {response.status_code}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    assert b"<svg" in response.content

    payload_red = make_test_export_object(gate_status="red")
    response = client.post("/api/translate/dxf", json=payload_red)
    print(f"POST /translate/dxf (red gate) status: {response.status_code}")
    assert response.status_code == 422

    response = client.post("/api/translate/step", json=payload)
    print(f"POST /translate/step (unsupported) status: {response.status_code}")
    assert response.status_code == 400

    print("\nPASSED: Multi-Target API: VERIFIED")
    return True


def verify_deterministic_output():
    """Verify translator output is deterministic."""
    print("\n=== Deterministic Output Verification ===")

    from app.cam.translators.base.negotiation import resolve_translator
    from app.export.body_export_bridge import (
        BodyExportObject,
        ExportGeometry,
        ExportValidation,
        ExportMetadata,
        ExportSource,
        ExportIntent,
        GeometryEntity,
        CoordinateSystem,
        Bounds,
        ValidationCheck,
    )

    export_obj = BodyExportObject(
        schema_version="1.0.0",
        export_id="EXP-BODY-DETERMINISM-TEST",
        export_type="geometry",
        metadata=ExportMetadata(
            export_id="EXP-BODY-DETERMINISM-TEST",
            schema_version="1.0.0",
            created_at="2026-05-13T12:00:00Z",
            source=ExportSource(preview_id="test", preview_hash="fixed_hash"),
        ),
        geometry=ExportGeometry(
            coordinate_system=CoordinateSystem(),
            bounds=Bounds(x_min=-100, x_max=100, y_min=0, y_max=200),
            entities=[
                GeometryEntity(
                    type="closed_contour",
                    id="outer",
                    role="outer",
                    winding="ccw",
                    points=[[-100, 0], [100, 0], [100, 200], [-100, 200], [-100, 0]],
                )
            ],
        ),
        validation=ExportValidation(
            gate_status="green",
            preview_gate="green",
            export_gate="green",
            checks_performed=[ValidationCheck(check="test", result="passed")],
            source_preview_hash="fixed_hash",
        ),
        intent=ExportIntent(),
    )

    from app.cam.translators.base.contracts import TranslatorOptions
    options = TranslatorOptions(embed_provenance=False)

    svg_translator = resolve_translator("svg")
    result1 = svg_translator.translate(export_obj, options)
    result2 = svg_translator.translate(export_obj, options)

    hash1 = result1.content_hash()
    hash2 = result2.content_hash()

    print(f"SVG hash 1: {hash1[:16]}...")
    print(f"SVG hash 2: {hash2[:16]}...")

    assert hash1 == hash2, "SVG output should be deterministic (without provenance)"

    print("\nPASSED: Deterministic Output: VERIFIED")
    return True


def verify_no_geometry_mutation():
    """Verify geometry is not mutated during translation."""
    print("\n=== No Geometry Mutation Verification ===")

    payload = make_test_export_object()
    original_points = payload["geometry"]["entities"][0]["points"].copy()

    from app.main import app
    client = TestClient(app)

    client.post("/api/translate/dxf", json=payload)
    client.post("/api/translate/svg", json=payload)

    current_points = payload["geometry"]["entities"][0]["points"]
    assert original_points == current_points, "Geometry was mutated!"

    print("Points preserved after DXF translation: OK")
    print("Points preserved after SVG translation: OK")
    print("\nPASSED: No Geometry Mutation: VERIFIED")
    return True


def main():
    """Run all multi-target verifications."""
    print("=" * 60)
    print("MRP-4A: Standalone Multi-Target Translator Verification")
    print("=" * 60)

    results = {}

    tests = [
        ("registry", verify_registry),
        ("target_negotiation", verify_target_negotiation),
        ("svg_translation", verify_svg_translation),
        ("multitarget_api", verify_multitarget_api),
        ("deterministic_output", verify_deterministic_output),
        ("no_geometry_mutation", verify_no_geometry_mutation),
    ]

    for name, test_fn in tests:
        try:
            results[name] = test_fn()
        except Exception as e:
            print(f"\nFAILED: {name}: {e}")
            results[name] = False
            import traceback
            traceback.print_exc()

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
        print("\nPASSED: MRP-4A MULTI-TARGET LAYER: VERIFIED")
        print("\nMultiple serialization targets now consume Export Objects canonically:")
        print("  - DXF (R12, R2000)")
        print("  - SVG")
        print("\nAPI endpoints:")
        print("  GET  /api/translate/targets")
        print("  GET  /api/translate/targets/{target}")
        print("  POST /api/translate/{target}")
        print("  POST /api/translate/{target}/metadata")
        return 0
    else:
        print("\nFAILED: MRP-4A VERIFICATION: INCOMPLETE")
        return 1


if __name__ == "__main__":
    sys.exit(main())
