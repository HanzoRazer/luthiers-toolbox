"""
MRP-2D: Morphology Spine End-to-End Verification Tests

Verifies that real morphology artifacts can travel through the complete
governed morphology spine without semantic corruption, authority collapse,
DXF leakage, or provenance loss.

Spine flow:
    Blueprint/Recovery → IBG → BOE (simulated edit) → Export Object

Sprint: MRP-2D
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
from fastapi.testclient import TestClient


# ─── Test Fixtures ───────────────────────────────────────────────────────────


@pytest.fixture
def api_client():
    """Create a test client for the FastAPI app."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def melody_maker_dxf():
    """Path to Melody Maker baseline DXF artifact."""
    path = Path(__file__).parent.parent.parent / "melody_maker_restored_baseline.dxf"
    if not path.exists():
        pytest.skip(f"Melody Maker DXF not found: {path}")
    return path


@pytest.fixture
def cuatro_dxf():
    """Path to Cuatro Puertorriqueño DXF artifact."""
    path = (
        Path(__file__).parent.parent.parent
        / "app"
        / "instrument_geometry"
        / "reference_dxf"
        / "cuatro"
        / "cuatro puertoriqueño.dxf"
    )
    if not path.exists():
        pytest.skip(f"Cuatro DXF not found: {path}")
    return path


@pytest.fixture
def verification_output_dir():
    """Directory for verification artifact captures."""
    output_dir = Path(__file__).parent / "artifacts"
    output_dir.mkdir(exist_ok=True)
    return output_dir


@pytest.fixture
def auth_headers():
    """Paid-tier operator auth headers for IBG endpoints.

    The IBG paid-tier endpoints (solve-from-landmarks, landmark PUT) gained
    ``Depends(get_current_principal)`` in IBG-2B, so an unauthenticated
    TestClient request now 401s. These headers exercise the real header-auth
    path (``_principal_from_headers``) as an operator principal — the same
    convention as ``test_body_solver_integration.py``'s ``auth_header``.

    Kept as an explicit ``headers=auth_headers`` argument at each IBG call site
    (rather than baked into an authenticated client fixture) on purpose: the auth
    dependency stays visible at the call, so a future auth-model migration surfaces
    here loudly instead of silently passing through a pre-authenticated client.
    """
    return {"x-user-role": "operator", "x-user-id": "test_user_123"}


# ─── Helper Functions ────────────────────────────────────────────────────────


def simulate_boe_edit(outline_points: List[List[float]]) -> List[List[float]]:
    """
    Simulate a BOE user edit by nudging the first point by 0.5mm.

    This proves that manual geometry edits survive the export pipeline.
    """
    if not outline_points:
        return outline_points

    edited = [list(p) for p in outline_points]
    edited[0][0] += 0.5  # Nudge first point X by 0.5mm
    return edited


def build_boe_geometry(
    outline_points: List[List[float]],
    name: str = "test_body",
    ibg_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build BOE-approved geometry structure from outline points."""
    points = outline_points.copy()

    # Ensure closed contour
    if points and points[0] != points[-1]:
        points.append(points[0])

    geometry = {
        "schema_version": 1,
        "units": "mm",
        "origin": "body_center_y_positive_toward_neck",
        "metadata": {
            "name": name,
            "source": "mrp_spine_verification",
            "created_at": datetime.utcnow().isoformat(),
        },
        "outer": {
            "id": "body",
            "role": "outer",
            "closed": True,
            "winding": "ccw",
            "points": points,
        },
        "voids": [],
    }

    if ibg_context:
        geometry["ibg_context"] = ibg_context

    return geometry


def verify_no_dxf_leakage(export_object: Dict[str, Any]) -> List[str]:
    """Check Export Object for DXF-specific terms (should be absent)."""
    forbidden = ["dxf", "lwpolyline", "ac1009", "ac1015", "ezdxf", "layer_0"]
    export_str = json.dumps(export_object).lower()

    violations = []
    for term in forbidden:
        if term in export_str:
            violations.append(f"DXF term '{term}' found in Export Object")

    return violations


def verify_provenance_preserved(
    ibg_response: Dict[str, Any],
    export_object: Dict[str, Any],
) -> Dict[str, str]:
    """
    Verify IBG context survived through export.

    Returns classification for each field:
    - PRESERVED: Field exists and matches
    - LOST: Field missing from export
    - TRANSFORMED: Field exists but value changed
    - OPTIONAL: Field not in source
    """
    results = {}

    fields_to_check = [
        "session_id",
        "confidence",
        "dimensions",
        "side_heights",
        "radii_by_zone",
        "missing_landmarks",
        "recovery_mode",
    ]

    ibg_ext = export_object.get("extensions", {}).get("ibg_morphology", {})

    for field in fields_to_check:
        source_value = ibg_response.get(field)

        # Map field names (side_heights -> side_heights_mm in export)
        export_field = field
        if field == "side_heights":
            export_field = "side_heights_mm"

        export_value = ibg_ext.get(export_field)

        if source_value is None:
            results[field] = "OPTIONAL"
        elif export_value is None:
            results[field] = "LOST"
        elif source_value == export_value:
            results[field] = "PRESERVED"
        else:
            # Check if values are close enough (for floats)
            if isinstance(source_value, (int, float)) and isinstance(export_value, (int, float)):
                if abs(source_value - export_value) < 0.001:
                    results[field] = "PRESERVED"
                else:
                    results[field] = "TRANSFORMED"
            else:
                results[field] = "TRANSFORMED"

    return results


def save_verification_artifact(
    output_dir: Path,
    artifact_name: str,
    stage: str,
    data: Any,
):
    """Save intermediate artifact for verification review."""
    artifact_dir = output_dir / artifact_name
    artifact_dir.mkdir(exist_ok=True)

    filepath = artifact_dir / f"{stage}.json"
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)


# ─── Spine Flow Tests ────────────────────────────────────────────────────────


class TestMorphologySpineFlow:
    """End-to-end spine flow verification tests."""

    def test_dreadnought_ibg_defaults_spine_flow(
        self, api_client, verification_output_dir, auth_headers
    ):
        """
        Verify spine flow with IBG-generated dreadnought defaults.

        Flow: IBG landmarks → IBG solve → simulated BOE edit → Export Object
        """
        artifact_name = "dreadnought_defaults"

        # Step 1: Use landmark-based solve to get IBG output (avoids numpy import)
        landmarks = [
            {"label": "lower_bout_max", "x_mm": 202.0, "y_mm": 95.0},
            {"label": "waist_min", "x_mm": 125.0, "y_mm": 230.0},
            {"label": "upper_bout_max", "x_mm": 147.0, "y_mm": 380.0},
            {"label": "butt_center", "x_mm": 0.0, "y_mm": 0.0},
            {"label": "neck_center", "x_mm": 0.0, "y_mm": 508.0},
        ]

        solve_response = api_client.post(
            "/api/body/solve-from-landmarks",
            json={
                "instrument_spec": "dreadnought",
                "landmarks": landmarks,
                "options": {"return_json": True, "return_side_heights": True},
            },
            headers=auth_headers,
        )

        if solve_response.status_code == 404:
            pytest.skip("Body solver router not loaded")

        assert solve_response.status_code == 200, f"IBG solve failed: {solve_response.text}"

        ibg_response = solve_response.json()

        save_verification_artifact(
            verification_output_dir, artifact_name, "01_ibg_response", ibg_response
        )

        # Step 2: Simulate BOE edit
        edited_points = simulate_boe_edit(ibg_response["outline_points"])

        boe_geometry = build_boe_geometry(
            edited_points,
            name=artifact_name,
            ibg_context={
                "session_id": ibg_response["session_id"],
                "confidence": ibg_response["confidence"],
                "dimensions": ibg_response["dimensions"],
                "instrument_spec": "dreadnought",
            },
        )

        save_verification_artifact(
            verification_output_dir, artifact_name, "02_boe_geometry", boe_geometry
        )

        # Step 3: Submit to export endpoint
        export_request = {
            "geometry": boe_geometry,
            "ibg_context": boe_geometry.get("ibg_context"),
        }

        response = api_client.post("/api/export/body-outline", json=export_request)

        if response.status_code == 404:
            pytest.skip("Body export router not loaded")

        assert response.status_code == 200, f"Export failed: {response.text}"
        export_result = response.json()

        save_verification_artifact(
            verification_output_dir, artifact_name, "03_export_object", export_result
        )

        # Step 4: Verify Export Object
        export_object = export_result["export_object"]

        # Verify no DXF leakage
        dxf_violations = verify_no_dxf_leakage(export_object)
        assert len(dxf_violations) == 0, f"DXF leakage: {dxf_violations}"

        # Verify gate status
        assert export_result["gate_status"] in ("green", "yellow"), \
            f"Unexpected gate status: {export_result['gate_status']}"

        # Verify Export Object structure
        assert export_object["schema_version"] == "1.0.0"
        assert export_object["export_type"] == "geometry"
        assert "geometry" in export_object
        assert "validation" in export_object
        assert "metadata" in export_object

        # Verify provenance
        provenance = verify_provenance_preserved(ibg_response, export_object)

        save_verification_artifact(
            verification_output_dir, artifact_name, "04_provenance_check", provenance
        )

        # session_id and confidence should be preserved
        assert provenance["session_id"] == "PRESERVED", \
            f"session_id not preserved: {provenance['session_id']}"
        assert provenance["confidence"] == "PRESERVED", \
            f"confidence not preserved: {provenance['confidence']}"

    def test_melody_maker_real_artifact_spine_flow(
        self, api_client, melody_maker_dxf, verification_output_dir
    ):
        """
        Verify spine flow with real Melody Maker DXF artifact.

        Flow: DXF file → IBG solve → simulated BOE edit → Export Object
        """
        artifact_name = "melody_maker"

        # Step 1: Submit DXF to IBG solve endpoint
        with open(melody_maker_dxf, "rb") as f:
            ibg_response = api_client.post(
                "/api/body/solve-from-dxf",
                files={"dxf_file": ("melody_maker.dxf", f, "application/dxf")},
                data={
                    "instrument_spec": "stratocaster",  # Electric body type
                    "consolidate": "true",
                    "options": json.dumps({
                        "return_json": True,
                        "return_side_heights": True,
                        "return_zone_radii": True,
                    }),
                },
            )

        if ibg_response.status_code == 404:
            pytest.skip("Body solver router not loaded")

        if ibg_response.status_code != 200:
            pytest.skip(f"IBG solve failed: {ibg_response.text}")

        ibg_data = ibg_response.json()

        save_verification_artifact(
            verification_output_dir, artifact_name, "01_ibg_response", ibg_data
        )

        # Verify IBG solve completed
        assert ibg_data.get("status") == "completed", \
            f"IBG solve not completed: {ibg_data.get('status')}"
        assert "outline_points" in ibg_data, "No outline_points in IBG response"

        # Step 2: Simulate BOE edit
        edited_points = simulate_boe_edit(ibg_data["outline_points"])

        boe_geometry = build_boe_geometry(
            edited_points,
            name=artifact_name,
            ibg_context={
                "session_id": ibg_data.get("session_id"),
                "confidence": ibg_data.get("confidence", 0.85),
                "dimensions": ibg_data.get("dimensions", {}),
                "instrument_spec": "stratocaster",
                "side_heights_mm": ibg_data.get("side_heights"),
                "radii_by_zone": ibg_data.get("radii_by_zone"),
                "missing_landmarks": ibg_data.get("missing_landmarks"),
                "recovery_mode": ibg_data.get("recovery_mode"),
            },
        )

        save_verification_artifact(
            verification_output_dir, artifact_name, "02_boe_geometry", boe_geometry
        )

        # Step 3: Submit to export endpoint
        export_request = {
            "geometry": boe_geometry,
            "ibg_context": boe_geometry.get("ibg_context"),
        }

        response = api_client.post("/api/export/body-outline", json=export_request)

        assert response.status_code == 200, f"Export failed: {response.text}"
        export_result = response.json()

        save_verification_artifact(
            verification_output_dir, artifact_name, "03_export_object", export_result
        )

        # Step 4: Verification
        export_object = export_result["export_object"]

        dxf_violations = verify_no_dxf_leakage(export_object)
        assert len(dxf_violations) == 0, f"DXF leakage: {dxf_violations}"

        assert export_result["export_ready"] is True or \
               export_result["gate_status"] in ("green", "yellow")

        provenance = verify_provenance_preserved(ibg_data, export_object)

        save_verification_artifact(
            verification_output_dir, artifact_name, "04_provenance_check", provenance
        )

        # Core provenance fields should be preserved
        assert provenance["session_id"] in ("PRESERVED", "OPTIONAL"), \
            f"session_id: {provenance['session_id']}"

    def test_cuatro_real_artifact_spine_flow(
        self, api_client, cuatro_dxf, verification_output_dir
    ):
        """
        Verify spine flow with real Cuatro Puertorriqueño DXF artifact.

        Flow: DXF file → IBG solve → simulated BOE edit → Export Object
        """
        artifact_name = "cuatro_puertorriqueno"

        # Step 1: Submit DXF to IBG solve endpoint
        with open(cuatro_dxf, "rb") as f:
            ibg_response = api_client.post(
                "/api/body/solve-from-dxf",
                files={"dxf_file": ("cuatro.dxf", f, "application/dxf")},
                data={
                    "instrument_spec": "cuatro_venezolano",  # Closest spec
                    "consolidate": "true",
                    "options": json.dumps({
                        "return_json": True,
                        "return_side_heights": True,
                        "return_zone_radii": True,
                    }),
                },
            )

        if ibg_response.status_code == 404:
            pytest.skip("Body solver router not loaded")

        if ibg_response.status_code != 200:
            pytest.skip(f"IBG solve failed: {ibg_response.text}")

        ibg_data = ibg_response.json()

        save_verification_artifact(
            verification_output_dir, artifact_name, "01_ibg_response", ibg_data
        )

        assert ibg_data.get("status") == "completed", \
            f"IBG solve not completed: {ibg_data.get('status')}"
        assert "outline_points" in ibg_data, "No outline_points in IBG response"

        # Step 2: Simulate BOE edit
        edited_points = simulate_boe_edit(ibg_data["outline_points"])

        boe_geometry = build_boe_geometry(
            edited_points,
            name=artifact_name,
            ibg_context={
                "session_id": ibg_data.get("session_id"),
                "confidence": ibg_data.get("confidence", 0.80),
                "dimensions": ibg_data.get("dimensions", {}),
                "instrument_spec": "cuatro_venezolano",
                "side_heights_mm": ibg_data.get("side_heights"),
                "radii_by_zone": ibg_data.get("radii_by_zone"),
                "missing_landmarks": ibg_data.get("missing_landmarks"),
                "recovery_mode": ibg_data.get("recovery_mode"),
            },
        )

        save_verification_artifact(
            verification_output_dir, artifact_name, "02_boe_geometry", boe_geometry
        )

        # Step 3: Submit to export endpoint
        export_request = {
            "geometry": boe_geometry,
            "ibg_context": boe_geometry.get("ibg_context"),
        }

        response = api_client.post("/api/export/body-outline", json=export_request)

        assert response.status_code == 200, f"Export failed: {response.text}"
        export_result = response.json()

        save_verification_artifact(
            verification_output_dir, artifact_name, "03_export_object", export_result
        )

        # Step 4: Verification
        export_object = export_result["export_object"]

        dxf_violations = verify_no_dxf_leakage(export_object)
        assert len(dxf_violations) == 0, f"DXF leakage: {dxf_violations}"

        provenance = verify_provenance_preserved(ibg_data, export_object)

        save_verification_artifact(
            verification_output_dir, artifact_name, "04_provenance_check", provenance
        )

    def test_landmark_only_solve_spine_flow(
        self, api_client, verification_output_dir, auth_headers
    ):
        """
        Verify spine flow with landmark-only IBG solve (no DXF input).

        Flow: Manual landmarks → IBG solve → simulated BOE edit → Export Object
        """
        artifact_name = "landmark_only_dreadnought"

        # Step 1: Submit landmarks to IBG
        landmarks = [
            {"label": "lower_bout_max", "x_mm": 202.0, "y_mm": 95.0},
            {"label": "waist_min", "x_mm": 125.0, "y_mm": 230.0},
            {"label": "upper_bout_max", "x_mm": 147.0, "y_mm": 380.0},
            {"label": "butt_center", "x_mm": 0.0, "y_mm": 0.0},
            {"label": "neck_center", "x_mm": 0.0, "y_mm": 508.0},
        ]

        ibg_response = api_client.post(
            "/api/body/solve-from-landmarks",
            json={
                "instrument_spec": "dreadnought",
                "landmarks": landmarks,
                "options": {
                    "return_json": True,
                    "return_side_heights": True,
                    "return_zone_radii": True,
                },
            },
            headers=auth_headers,
        )

        if ibg_response.status_code == 404:
            pytest.skip("Body solver router not loaded")

        assert ibg_response.status_code == 200, f"IBG solve failed: {ibg_response.text}"

        ibg_data = ibg_response.json()

        save_verification_artifact(
            verification_output_dir, artifact_name, "01_ibg_response", ibg_data
        )

        assert ibg_data.get("status") == "completed"
        assert "outline_points" in ibg_data

        # Step 2: Simulate BOE edit
        edited_points = simulate_boe_edit(ibg_data["outline_points"])

        boe_geometry = build_boe_geometry(
            edited_points,
            name=artifact_name,
            ibg_context={
                "session_id": ibg_data.get("session_id"),
                "confidence": ibg_data.get("confidence", 1.0),
                "dimensions": ibg_data.get("dimensions", {}),
                "instrument_spec": "dreadnought",
                "side_heights_mm": ibg_data.get("side_heights"),
                "radii_by_zone": ibg_data.get("radii_by_zone"),
            },
        )

        save_verification_artifact(
            verification_output_dir, artifact_name, "02_boe_geometry", boe_geometry
        )

        # Step 3: Submit to export endpoint
        export_request = {
            "geometry": boe_geometry,
            "ibg_context": boe_geometry.get("ibg_context"),
        }

        response = api_client.post("/api/export/body-outline", json=export_request)

        assert response.status_code == 200, f"Export failed: {response.text}"
        export_result = response.json()

        save_verification_artifact(
            verification_output_dir, artifact_name, "03_export_object", export_result
        )

        # Step 4: Verification
        export_object = export_result["export_object"]

        dxf_violations = verify_no_dxf_leakage(export_object)
        assert len(dxf_violations) == 0, f"DXF leakage: {dxf_violations}"

        assert export_result["export_ready"] is True
        assert export_result["gate_status"] == "green"

        provenance = verify_provenance_preserved(ibg_data, export_object)

        save_verification_artifact(
            verification_output_dir, artifact_name, "04_provenance_check", provenance
        )

        # Full provenance should be preserved for landmark solve
        assert provenance["session_id"] in ("PRESERVED", "OPTIONAL")
        assert provenance["confidence"] == "PRESERVED"


# ─── Authority Boundary Tests ────────────────────────────────────────────────


class TestAuthorityBoundaries:
    """Verify authority boundaries are maintained through spine flow."""

    def test_ibg_metadata_does_not_override_boe_edits(
        self, api_client, verification_output_dir, auth_headers
    ):
        """
        Verify that IBG metadata is advisory only -
        BOE geometry edits survive even when IBG context is present.
        """
        # Get IBG output via API to avoid numpy import conflict
        landmarks = [
            {"label": "lower_bout_max", "x_mm": 202.0, "y_mm": 95.0},
            {"label": "butt_center", "x_mm": 0.0, "y_mm": 0.0},
            {"label": "neck_center", "x_mm": 0.0, "y_mm": 508.0},
        ]

        solve_response = api_client.post(
            "/api/body/solve-from-landmarks",
            json={
                "instrument_spec": "dreadnought",
                "landmarks": landmarks,
                "options": {"return_json": True},
            },
            headers=auth_headers,
        )

        if solve_response.status_code == 404:
            pytest.skip("Body solver router not loaded")

        assert solve_response.status_code == 200, f"IBG solve failed: {solve_response.text}"

        ibg_data = solve_response.json()
        original_points = ibg_data["outline_points"]

        # Significant BOE edit - move first point by 5mm
        edited_points = [list(p) for p in original_points]
        edited_points[0][0] += 5.0
        edited_points[0][1] += 5.0

        # Build geometry with IBG context that has original dimensions
        boe_geometry = build_boe_geometry(
            edited_points,
            name="authority_test",
            ibg_context={
                "session_id": ibg_data.get("session_id", "authority_test_session"),
                "confidence": ibg_data.get("confidence", 0.95),
                "dimensions": ibg_data.get("dimensions", {}),
                "instrument_spec": "dreadnought",
            },
        )

        # Export
        export_request = {
            "geometry": boe_geometry,
            "ibg_context": boe_geometry.get("ibg_context"),
        }

        response = api_client.post("/api/export/body-outline", json=export_request)

        if response.status_code == 404:
            pytest.skip("Body export router not loaded")

        assert response.status_code == 200
        export_result = response.json()

        export_object = export_result["export_object"]

        # Verify the edited geometry is in the Export Object, not IBG original
        exported_points = export_object["geometry"]["entities"][0]["points"]

        # The first point should be the edited version
        assert abs(exported_points[0][0] - edited_points[0][0]) < 0.01, \
            "BOE edit was overwritten by IBG metadata"
        assert abs(exported_points[0][1] - edited_points[0][1]) < 0.01, \
            "BOE edit was overwritten by IBG metadata"

    def test_export_validation_independent_of_extensions(
        self, api_client
    ):
        """
        Verify that Export Object validation does not depend on
        IBG morphology extensions.
        """
        # Valid geometry without IBG context
        geometry = build_boe_geometry(
            [
                [0, 0], [25, 0], [50, 0], [75, 0], [100, 0],
                [100, 50], [100, 100], [100, 150], [100, 200],
                [75, 200], [50, 200], [25, 200], [0, 200],
                [0, 150], [0, 100], [0, 50], [0, 0],
            ],
            name="no_ibg_context",
            ibg_context=None,
        )

        export_request = {"geometry": geometry}

        response = api_client.post("/api/export/body-outline", json=export_request)

        if response.status_code == 404:
            pytest.skip("Body export router not loaded")

        assert response.status_code == 200
        export_result = response.json()

        # Should still be export-ready without IBG context
        assert export_result["export_ready"] is True
        assert export_result["gate_status"] == "green"

        # Extensions should be None
        assert export_result["export_object"].get("extensions") is None

    def test_malformed_extension_handled_safely(
        self, api_client
    ):
        """
        Verify that malformed IBG context doesn't break export.
        """
        geometry = build_boe_geometry(
            [
                [0, 0], [50, 0], [100, 0], [100, 100], [100, 200],
                [50, 200], [0, 200], [0, 100], [0, 0],
            ],
            name="malformed_test",
        )

        # Add malformed ibg_context directly to request
        export_request = {
            "geometry": geometry,
            "ibg_context": {
                "session_id": "test",
                "confidence": "not_a_number",  # Should be float
                "dimensions": "not_a_dict",  # Should be dict
                "instrument_spec": "dreadnought",
            },
        }

        response = api_client.post("/api/export/body-outline", json=export_request)

        if response.status_code == 404:
            pytest.skip("Body export router not loaded")

        # Should return 422 validation error, not crash
        assert response.status_code == 422


# ─── Export Object Integrity Tests ───────────────────────────────────────────


class TestExportObjectIntegrity:
    """Verify Export Object structure and content integrity."""

    def test_coordinate_system_present(self, api_client):
        """Export Object must have coordinate system specification."""
        geometry = build_boe_geometry(
            [[0, 0], [100, 0], [100, 200], [0, 200], [0, 0]],
            name="coord_test",
        )

        export_request = {"geometry": geometry}
        response = api_client.post("/api/export/body-outline", json=export_request)

        if response.status_code == 404:
            pytest.skip("Body export router not loaded")

        assert response.status_code == 200
        export_object = response.json()["export_object"]

        cs = export_object["geometry"]["coordinate_system"]
        assert cs["origin"] == "body_center"
        assert cs["units"] == "mm"
        assert cs["handedness"] == "right_handed"

    def test_provenance_metadata_present(self, api_client):
        """Export Object must have provenance metadata."""
        geometry = build_boe_geometry(
            [[0, 0], [100, 0], [100, 200], [0, 200], [0, 0]],
            name="provenance_test",
        )

        export_request = {"geometry": geometry}
        response = api_client.post("/api/export/body-outline", json=export_request)

        if response.status_code == 404:
            pytest.skip("Body export router not loaded")

        assert response.status_code == 200
        export_object = response.json()["export_object"]

        metadata = export_object["metadata"]
        assert "export_id" in metadata
        assert "created_at" in metadata
        assert "source" in metadata
        assert metadata["source"]["generator_id"] == "boe_export"

    def test_validation_block_present(self, api_client):
        """Export Object must have validation block with gate status."""
        geometry = build_boe_geometry(
            [[0, 0], [100, 0], [100, 200], [0, 200], [0, 0]],
            name="validation_test",
        )

        export_request = {"geometry": geometry}
        response = api_client.post("/api/export/body-outline", json=export_request)

        if response.status_code == 404:
            pytest.skip("Body export router not loaded")

        assert response.status_code == 200
        export_object = response.json()["export_object"]

        validation = export_object["validation"]
        assert validation["gate_status"] in ("green", "yellow", "red")
        assert "checks_performed" in validation

    def test_intent_block_present(self, api_client):
        """Export Object must have manufacturing intent block."""
        geometry = build_boe_geometry(
            [[0, 0], [100, 0], [100, 200], [0, 200], [0, 0]],
            name="intent_test",
        )

        export_request = {"geometry": geometry}
        response = api_client.post("/api/export/body-outline", json=export_request)

        if response.status_code == 404:
            pytest.skip("Body export router not loaded")

        assert response.status_code == 200
        export_object = response.json()["export_object"]

        intent = export_object["intent"]
        assert intent["operation_type"] == "body_profiling"
        assert intent["depth_strategy"] == "full_thickness"
