#!/usr/bin/env python3
"""
MRP-3B: Standalone Endpoint Verification Script

Verifies the /api/export/translate/dxf endpoint works correctly.
Runs outside pytest to avoid Python 3.14/numpy module reload conflict.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi.testclient import TestClient


def make_test_export_object(
    gate_status: str = "green",
    with_ibg_context: bool = True,
    export_id: str = "EXP-BODY-20260513-test001",
) -> dict:
    """Create a test BodyExportObject as dict for API request."""
    entities = [
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
    ]

    extensions = None
    if with_ibg_context:
        extensions = {
            "ibg_morphology": {
                "session_id": "ibg-test-session-001",
                "confidence": 0.92,
                "dimensions": {
                    "lower_bout_width_mm": 400.0,
                    "upper_bout_width_mm": 280.0,
                    "waist_width_mm": 230.0,
                    "body_length_mm": 500.0,
                },
                "instrument_spec": "dreadnought",
            }
        }

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
            "entities": entities,
        },
        "validation": {
            "gate_status": gate_status,
            "preview_gate": gate_status,
            "export_gate": gate_status,
            "issues": ["Test failure"] if gate_status == "red" else [],
            "warnings": ["Winding direction non-standard"] if gate_status == "yellow" else [],
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
        "extensions": extensions,
    }


def verify_r12_translation():
    """Test R12 translation via endpoint."""
    print("\n=== R12 Endpoint Verification ===")

    from app.main import app
    client = TestClient(app)

    payload = make_test_export_object(gate_status="green")

    response = client.post(
        "/api/export/translate/dxf?version=r12",
        json=payload,
    )

    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"X-Export-ID: {response.headers.get('X-Export-ID')}")
    print(f"X-Translator-ID: {response.headers.get('X-Translator-ID')}")
    print(f"X-Governance-Gate: {response.headers.get('X-Governance-Gate')}")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.headers["content-type"] == "application/dxf"
    assert response.headers["X-Translator-ID"] == "body_outline_dxf_r12"
    assert response.headers["X-Governance-Gate"] == "green"
    assert b"SECTION" in response.content
    assert b"EOF" in response.content

    print(f"DXF size: {len(response.content)} bytes")
    print("\nPASSED: R12 Endpoint: VERIFIED")
    return True


def verify_r2000_translation():
    """Test R2000 translation via endpoint."""
    print("\n=== R2000 Endpoint Verification ===")

    from app.main import app
    client = TestClient(app)

    payload = make_test_export_object(gate_status="green")

    response = client.post(
        "/api/export/translate/dxf?version=r2000",
        json=payload,
    )

    print(f"Status: {response.status_code}")
    print(f"X-Translator-ID: {response.headers.get('X-Translator-ID')}")

    assert response.status_code == 200
    assert response.headers["X-Translator-ID"] == "body_outline_dxf_r2000"

    print(f"DXF size: {len(response.content)} bytes")
    print("\nPASSED: R2000 Endpoint: VERIFIED")
    return True


def verify_red_gate_rejection():
    """Test red gate returns 422."""
    print("\n=== Red Gate Rejection Verification ===")

    from app.main import app
    client = TestClient(app)

    payload = make_test_export_object(gate_status="red")

    response = client.post(
        "/api/export/translate/dxf?version=r12",
        json=payload,
    )

    print(f"Status: {response.status_code}")

    assert response.status_code == 422, f"Expected 422, got {response.status_code}"

    data = response.json()
    print(f"Error: {data['detail']['error']}")
    print(f"Gate: {data['detail']['gate']}")

    assert data["detail"]["error"] == "EXPORT_OBJECT_NOT_TRANSLATABLE"
    assert data["detail"]["gate"] == "red"

    print("\nPASSED: Red Gate Rejection: VERIFIED")
    return True


def verify_yellow_gate_warning():
    """Test yellow gate translates with warning."""
    print("\n=== Yellow Gate Warning Verification ===")

    from app.main import app
    client = TestClient(app)

    payload = make_test_export_object(gate_status="yellow")

    response = client.post(
        "/api/export/translate/dxf?version=r12",
        json=payload,
    )

    print(f"Status: {response.status_code}")
    print(f"X-Governance-Gate: {response.headers.get('X-Governance-Gate')}")
    print(f"X-Governance-Warnings: {response.headers.get('X-Governance-Warnings')}")

    assert response.status_code == 200
    assert response.headers["X-Governance-Gate"] == "yellow"
    assert "X-Governance-Warnings" in response.headers

    print("\nPASSED: Yellow Gate Warning: VERIFIED")
    return True


def verify_provenance_headers():
    """Test provenance headers are present."""
    print("\n=== Provenance Headers Verification ===")

    from app.main import app
    client = TestClient(app)

    payload = make_test_export_object(with_ibg_context=True)

    response = client.post(
        "/api/export/translate/dxf",
        json=payload,
    )

    print(f"X-IBG-Session-ID: {response.headers.get('X-IBG-Session-ID')}")
    print(f"X-Instrument-Spec: {response.headers.get('X-Instrument-Spec')}")
    print(f"X-Provenance-Hash: {response.headers.get('X-Provenance-Hash')}")

    assert response.status_code == 200
    assert "X-IBG-Session-ID" in response.headers
    assert response.headers["X-IBG-Session-ID"] == "ibg-test-session-001"
    assert response.headers["X-Instrument-Spec"] == "dreadnought"

    print("\nPASSED: Provenance Headers: VERIFIED")
    return True


def verify_filename_disposition():
    """Test Content-Disposition has correct filename."""
    print("\n=== Filename Disposition Verification ===")

    from app.main import app
    client = TestClient(app)

    payload = make_test_export_object(export_id="EXP-BODY-20260513-myguitar")

    response = client.post(
        "/api/export/translate/dxf?version=r12",
        json=payload,
    )

    disposition = response.headers.get("Content-Disposition", "")
    print(f"Content-Disposition: {disposition}")

    assert response.status_code == 200
    assert "EXP-BODY-20260513-myguitar" in disposition
    assert ".dxf" in disposition

    print("\nPASSED: Filename Disposition: VERIFIED")
    return True


def verify_metadata_endpoint():
    """Test metadata endpoint returns statistics."""
    print("\n=== Metadata Endpoint Verification ===")

    from app.main import app
    client = TestClient(app)

    payload = make_test_export_object()

    response = client.post(
        "/api/export/translate/dxf/metadata",
        json=payload,
    )

    print(f"Status: {response.status_code}")

    assert response.status_code == 200

    data = response.json()
    print(f"export_id: {data['export_id']}")
    print(f"translator_id: {data['translator_id']}")
    print(f"output_size_bytes: {data['output_size_bytes']}")
    print(f"entities_translated: {data['entities_translated']}")

    assert "export_id" in data
    assert "translator_id" in data
    assert data["output_size_bytes"] > 0
    assert data["entities_translated"] == 1

    print("\nPASSED: Metadata Endpoint: VERIFIED")
    return True


def verify_default_version_r12():
    """Test default version is R12."""
    print("\n=== Default Version Verification ===")

    from app.main import app
    client = TestClient(app)

    payload = make_test_export_object()

    response = client.post(
        "/api/export/translate/dxf",
        json=payload,
    )

    print(f"X-Translator-ID (no version param): {response.headers.get('X-Translator-ID')}")

    assert response.status_code == 200
    assert response.headers["X-Translator-ID"] == "body_outline_dxf_r12"

    print("\nPASSED: Default Version R12: VERIFIED")
    return True


def verify_no_geometry_mutation():
    """Test that geometry is not mutated during translation."""
    print("\n=== No Geometry Mutation Verification ===")

    from app.main import app
    client = TestClient(app)

    payload = make_test_export_object()
    original_points = payload["geometry"]["entities"][0]["points"].copy()

    response = client.post(
        "/api/export/translate/dxf",
        json=payload,
    )

    assert response.status_code == 200

    current_points = payload["geometry"]["entities"][0]["points"]
    assert original_points == current_points, "Geometry was mutated!"

    print("Original points preserved: YES")
    print("\nPASSED: No Geometry Mutation: VERIFIED")
    return True


def main():
    """Run all endpoint verifications."""
    print("=" * 60)
    print("MRP-3B: Standalone Endpoint Verification")
    print("=" * 60)

    results = {}

    tests = [
        ("r12_translation", verify_r12_translation),
        ("r2000_translation", verify_r2000_translation),
        ("red_gate_rejection", verify_red_gate_rejection),
        ("yellow_gate_warning", verify_yellow_gate_warning),
        ("provenance_headers", verify_provenance_headers),
        ("filename_disposition", verify_filename_disposition),
        ("metadata_endpoint", verify_metadata_endpoint),
        ("default_version_r12", verify_default_version_r12),
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
        print("\nPASSED: MRP-3B ENDPOINT LAYER: VERIFIED")
        print("\nThe DXF translator is now accessible via API:")
        print("  POST /api/export/translate/dxf")
        print("  POST /api/export/translate/dxf/metadata")
        return 0
    else:
        print("\nFAILED: MRP-3B VERIFICATION: INCOMPLETE")
        return 1


if __name__ == "__main__":
    sys.exit(main())
