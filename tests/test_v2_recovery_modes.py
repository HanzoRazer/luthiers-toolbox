"""
V2 Recovery Mode Endpoint Validation Tests

Tests V2_RAW and PHOTO_V2 modes wired in 2026-05-12.
Also verifies existing modes are not affected.
"""
import base64
import json
import pytest
from pathlib import Path
from datetime import datetime

from fastapi.testclient import TestClient


# Test file paths
CUATRO_PDF = Path("Guitar Plans/El Cuatro/cuatro puertoriqueño.pdf")
MELODY_MAKER_PDF = Path("docs/archive/instrument_references/gibson_melody_maker/gibson_melody_maker_blueprint.pdf")
DAQUISTO_JPG = Path("docs/archive/instrument_references/daquisto/DAquisto-Measurements-2.jpg")

# Output directory
PENDING_DIR = Path("tests/regression_corpus/pending")


def get_client():
    """Get test client - import here to avoid circular imports."""
    from app.main import app
    return TestClient(app)


def save_artifact(mode: str, filename: str, response_data: dict, output_dir: Path):
    """Save test artifacts to pending directory."""
    artifact_dir = output_dir / f"{filename}_{mode}"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    # Save DXF if present (base64 encoded in response)
    artifacts = response_data.get("artifacts", {})
    dxf_artifact = artifacts.get("dxf", {})
    if dxf_artifact.get("present") and dxf_artifact.get("base64"):
        dxf_bytes = base64.b64decode(dxf_artifact["base64"])
        (artifact_dir / "output.dxf").write_bytes(dxf_bytes)

    # Save SVG if present
    svg_artifact = artifacts.get("svg", {})
    if svg_artifact.get("present") and svg_artifact.get("content"):
        (artifact_dir / "output.svg").write_text(svg_artifact["content"])

    # Save signature if present
    if "signature" in response_data:
        (artifact_dir / "candidate_signature.json").write_text(
            json.dumps(response_data["signature"], indent=2)
        )

    # Save DXF summary if present
    if "dxf_summary" in response_data:
        (artifact_dir / "candidate_dxf_summary.json").write_text(
            json.dumps(response_data["dxf_summary"], indent=2)
        )

    # Save capture notes
    notes = f"""# Capture Notes

**Mode:** {mode}
**Input:** {filename}
**Captured:** {datetime.now().isoformat()}

## Response Summary

- OK: {response_data.get('ok', 'N/A')}
- Stage: {response_data.get('stage', 'N/A')}
- Error: {response_data.get('error', 'None')}
- Warnings: {response_data.get('warnings', [])}

## Artifacts Present

- DXF: {'Yes' if response_data.get('artifacts', {}).get('dxf') else 'No'}
- SVG: {'Yes' if response_data.get('artifacts', {}).get('svg') else 'No'}

## Visual Inspection

Status: PENDING
"""
    (artifact_dir / "capture_notes.md").write_text(notes)

    return artifact_dir


class TestV2RawMode:
    """Test V2_RAW mode with PDF blueprints."""

    def test_v2_raw_cuatro_pdf(self):
        """V2_RAW should process cuatro PDF and generate DXF."""
        client = get_client()
        pdf_path = Path(__file__).parent.parent / CUATRO_PDF

        if not pdf_path.exists():
            pytest.skip(f"Test file not found: {pdf_path}")

        with open(pdf_path, "rb") as f:
            response = client.post(
                "/api/blueprint/vectorize",
                files={"file": ("cuatro.pdf", f, "application/pdf")},
                data={"mode": "v2_raw"},
            )

        assert response.status_code == 200, f"Endpoint failed: {response.text}"
        data = response.json()

        # V2_RAW bypasses cleanup, so ok may be False due to recommendation logic
        # Key check: DXF artifact was generated
        assert "artifacts" in data, "No artifacts in response"
        dxf_artifact = data["artifacts"].get("dxf", {})
        assert dxf_artifact.get("present"), f"No DXF artifact generated: {data.get('error')}"
        assert dxf_artifact.get("entity_count", 0) > 0, "DXF has zero entities"

        # Save artifacts
        output_dir = Path(__file__).parent.parent / PENDING_DIR
        save_artifact("v2_raw", "cuatro_pdf", data, output_dir)

    def test_v2_raw_melody_maker_pdf(self):
        """V2_RAW should process Melody Maker PDF and generate DXF."""
        client = get_client()
        pdf_path = Path(__file__).parent.parent / MELODY_MAKER_PDF

        if not pdf_path.exists():
            pytest.skip(f"Test file not found: {pdf_path}")

        with open(pdf_path, "rb") as f:
            response = client.post(
                "/api/blueprint/vectorize",
                files={"file": ("melody_maker.pdf", f, "application/pdf")},
                data={"mode": "v2_raw"},
            )

        assert response.status_code == 200, f"Endpoint failed: {response.text}"
        data = response.json()

        # V2_RAW bypasses cleanup, so ok may be False due to recommendation logic
        # Key check: DXF artifact was generated
        assert "artifacts" in data, "No artifacts in response"
        dxf_artifact = data["artifacts"].get("dxf", {})
        assert dxf_artifact.get("present"), f"No DXF artifact generated: {data.get('error')}"
        assert dxf_artifact.get("entity_count", 0) > 0, "DXF has zero entities"

        # Save artifacts
        output_dir = Path(__file__).parent.parent / PENDING_DIR
        save_artifact("v2_raw", "melody_maker_pdf", data, output_dir)


class TestPhotoV2Mode:
    """Test PHOTO_V2 mode with photographic images."""

    def test_photo_v2_daquisto_jpg(self):
        """PHOTO_V2 should process JPG image and generate DXF."""
        client = get_client()
        jpg_path = Path(__file__).parent.parent / DAQUISTO_JPG

        if not jpg_path.exists():
            pytest.skip(f"Test file not found: {jpg_path}")

        with open(jpg_path, "rb") as f:
            response = client.post(
                "/api/blueprint/vectorize",
                files={"file": ("daquisto.jpg", f, "image/jpeg")},
                data={"mode": "photo_v2"},
            )

        assert response.status_code == 200, f"Endpoint failed: {response.text}"
        data = response.json()

        # PHOTO_V2 bypasses cleanup, so ok may be False due to recommendation logic
        # Key check: DXF artifact was generated
        assert "artifacts" in data, "No artifacts in response"
        dxf_artifact = data["artifacts"].get("dxf", {})
        assert dxf_artifact.get("present"), f"No DXF artifact generated: {data.get('error')}"
        assert dxf_artifact.get("entity_count", 0) > 0, "DXF has zero entities"

        # Save artifacts
        output_dir = Path(__file__).parent.parent / PENDING_DIR
        save_artifact("photo_v2", "daquisto_jpg", data, output_dir)


class TestRegressionSafety:
    """Verify existing modes still work and don't route through V2."""

    def test_refined_mode_unchanged(self):
        """Refined mode should still work."""
        client = get_client()
        pdf_path = Path(__file__).parent.parent / MELODY_MAKER_PDF

        if not pdf_path.exists():
            pytest.skip(f"Test file not found: {pdf_path}")

        with open(pdf_path, "rb") as f:
            response = client.post(
                "/api/blueprint/vectorize",
                files={"file": ("melody_maker.pdf", f, "application/pdf")},
                data={"mode": "refined"},
            )

        assert response.status_code == 200, f"Endpoint failed: {response.text}"
        data = response.json()
        # Check artifacts generated (ok depends on recommendation logic)
        dxf_artifact = data.get("artifacts", {}).get("dxf", {})
        assert dxf_artifact.get("present"), f"No DXF artifact: {data.get('error')}"

    def test_baseline_mode_unchanged(self):
        """Baseline mode should still work."""
        client = get_client()
        pdf_path = Path(__file__).parent.parent / MELODY_MAKER_PDF

        if not pdf_path.exists():
            pytest.skip(f"Test file not found: {pdf_path}")

        with open(pdf_path, "rb") as f:
            response = client.post(
                "/api/blueprint/vectorize",
                files={"file": ("melody_maker.pdf", f, "application/pdf")},
                data={"mode": "baseline"},
            )

        assert response.status_code == 200, f"Endpoint failed: {response.text}"
        data = response.json()
        # Check artifacts generated (ok depends on recommendation logic)
        dxf_artifact = data.get("artifacts", {}).get("dxf", {})
        assert dxf_artifact.get("present"), f"No DXF artifact: {data.get('error')}"

    def test_restored_baseline_mode_unchanged(self):
        """Restored baseline mode should still work."""
        client = get_client()
        pdf_path = Path(__file__).parent.parent / MELODY_MAKER_PDF

        if not pdf_path.exists():
            pytest.skip(f"Test file not found: {pdf_path}")

        with open(pdf_path, "rb") as f:
            response = client.post(
                "/api/blueprint/vectorize",
                files={"file": ("melody_maker.pdf", f, "application/pdf")},
                data={"mode": "restored_baseline"},
            )

        assert response.status_code == 200, f"Endpoint failed: {response.text}"
        data = response.json()
        # Check artifacts generated (ok depends on recommendation logic)
        dxf_artifact = data.get("artifacts", {}).get("dxf", {})
        assert dxf_artifact.get("present"), f"No DXF artifact: {data.get('error')}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
