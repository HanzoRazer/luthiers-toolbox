"""
Phase 2 schema validation tests.

Validates that phase2_slice.py output matches contracts/*.schema.json.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Attempt jsonschema import; skip tests if not available
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    jsonschema = None  # type: ignore


REPO_ROOT = Path(__file__).parent.parent
CONTRACTS_DIR = REPO_ROOT / "contracts"
EXAMPLES_DIR = REPO_ROOT / "examples"
SCRIPTS_DIR = REPO_ROOT / "scripts"


def load_schema(name: str) -> dict:
    """Load a JSON schema from contracts/."""
    path = CONTRACTS_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


def validate_json(data: dict, schema: dict) -> None:
    """Validate JSON data against schema using jsonschema."""
    if not HAS_JSONSCHEMA:
        pytest.skip("jsonschema not installed")
    jsonschema.validate(instance=data, schema=schema)


@pytest.fixture(scope="module")
def synthetic_session_dir(tmp_path_factory) -> Path:
    """
    Run phase2_slice.py with --synthetic and return the session directory.

    This is a module-scoped fixture so we only run the pipeline once.
    """
    import os

    out_root = tmp_path_factory.mktemp("phase2_runs")
    grid_path = EXAMPLES_DIR / "phase2_grid_mm.json"

    if not grid_path.exists():
        pytest.skip(f"Grid file not found: {grid_path}")

    # Set PYTHONPATH to include repo root for 'modes' module
    env = os.environ.copy()
    existing_path = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(REPO_ROOT) + (os.pathsep + existing_path if existing_path else "")

    # Run phase2_slice.py run --synthetic
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS_DIR / "phase2_slice.py"),
            "run",
            "--grid", str(grid_path),
            "--out", str(out_root),
            "--synthetic",
            "--top-n", "5",
            "--ods-target-hz", "185",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        env=env,
    )

    if result.returncode != 0:
        pytest.fail(f"phase2_slice.py failed:\n{result.stderr}\n{result.stdout}")

    # Find the session directory (session_*)
    sessions = list(out_root.glob("session_*"))
    if not sessions:
        pytest.fail(f"No session directory created in {out_root}")

    return sessions[0]


class TestPhase2WolfCandidatesSchema:
    """Validate wolf_candidates.json against phase2_wolf_candidates.schema.json."""

    def test_wolf_candidates_exists(self, synthetic_session_dir: Path):
        path = synthetic_session_dir / "derived" / "wolf_candidates.json"
        assert path.exists(), f"wolf_candidates.json not found at {path}"

    @pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
    def test_wolf_candidates_schema_valid(self, synthetic_session_dir: Path):
        path = synthetic_session_dir / "derived" / "wolf_candidates.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        schema = load_schema("phase2_wolf_candidates.schema.json")
        validate_json(data, schema)

    def test_wolf_candidates_has_required_fields(self, synthetic_session_dir: Path):
        path = synthetic_session_dir / "derived" / "wolf_candidates.json"
        data = json.loads(path.read_text(encoding="utf-8"))

        assert data.get("schema_version") == "phase2_wolf_candidates_v2"
        assert "wsi_threshold" in data
        assert "coherence_threshold" in data
        assert "candidates" in data
        assert "provenance" in data

        # Validate provenance structure
        prov = data["provenance"]
        assert "algo_id" in prov
        assert "algo_version" in prov
        assert "numpy_version" in prov
        assert "computed_at_utc" in prov

    def test_wolf_candidates_has_top_points_per_candidate(self, synthetic_session_dir: Path):
        path = synthetic_session_dir / "derived" / "wolf_candidates.json"
        data = json.loads(path.read_text(encoding="utf-8"))

        candidates = data.get("candidates", [])
        assert len(candidates) > 0, "Expected at least one candidate"

        for i, cand in enumerate(candidates):
            assert "freq_hz" in cand, f"Candidate {i} missing freq_hz"
            assert "wsi" in cand, f"Candidate {i} missing wsi"
            assert "admissible" in cand, f"Candidate {i} missing admissible"
            assert "coh_mean" in cand, f"Candidate {i} missing coh_mean"
            assert "top_points" in cand, f"Candidate {i} missing top_points"

            top_points = cand["top_points"]
            assert len(top_points) >= 1, f"Candidate {i} has no top_points"

            for j, tp in enumerate(top_points):
                assert "point_id" in tp, f"Candidate {i} top_point {j} missing point_id"
                assert "x_mm" in tp, f"Candidate {i} top_point {j} missing x_mm"
                assert "y_mm" in tp, f"Candidate {i} top_point {j} missing y_mm"
                assert "score" in tp, f"Candidate {i} top_point {j} missing score"


class TestPhase2ODSSnapshotSchema:
    """Validate ods_snapshot.json against phase2_ods_snapshot.schema.json."""

    def test_ods_snapshot_exists(self, synthetic_session_dir: Path):
        path = synthetic_session_dir / "derived" / "ods_snapshot.json"
        assert path.exists(), f"ods_snapshot.json not found at {path}"

    @pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
    def test_ods_snapshot_schema_valid(self, synthetic_session_dir: Path):
        path = synthetic_session_dir / "derived" / "ods_snapshot.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        schema = load_schema("phase2_ods_snapshot.schema.json")
        validate_json(data, schema)

    def test_ods_snapshot_has_required_fields(self, synthetic_session_dir: Path):
        path = synthetic_session_dir / "derived" / "ods_snapshot.json"
        data = json.loads(path.read_text(encoding="utf-8"))

        assert data.get("schema_version") == "phase2_ods_snapshot_v2"
        assert "capdir" in data
        assert "freqs_hz" in data
        assert "points" in data
        assert "provenance" in data

        # Validate freqs_hz is array
        freqs = data["freqs_hz"]
        assert isinstance(freqs, list), "freqs_hz should be an array"
        assert len(freqs) >= 1, "freqs_hz should have at least one element"

        # Validate provenance structure
        prov = data["provenance"]
        assert "algo_id" in prov
        assert "algo_version" in prov
        assert "numpy_version" in prov
        assert "scipy_version" in prov
        assert "computed_at_utc" in prov

    def test_ods_snapshot_points_have_arrays(self, synthetic_session_dir: Path):
        path = synthetic_session_dir / "derived" / "ods_snapshot.json"
        data = json.loads(path.read_text(encoding="utf-8"))

        points = data.get("points", [])
        assert len(points) > 0, "Expected at least one point"

        for i, pt in enumerate(points):
            assert "point_id" in pt, f"Point {i} missing point_id"
            assert "x_mm" in pt, f"Point {i} missing x_mm"
            assert "y_mm" in pt, f"Point {i} missing y_mm"
            assert "H_mag" in pt, f"Point {i} missing H_mag"
            assert "H_phase_deg" in pt, f"Point {i} missing H_phase_deg"
            assert "coherence" in pt, f"Point {i} missing coherence"

            # Validate arrays
            assert isinstance(pt["H_mag"], list), f"Point {i} H_mag should be array"
            assert isinstance(pt["H_phase_deg"], list), f"Point {i} H_phase_deg should be array"
            assert isinstance(pt["coherence"], list), f"Point {i} coherence should be array"

            # Array lengths should match freqs_hz length
            n_freqs = len(data["freqs_hz"])
            assert len(pt["H_mag"]) == n_freqs, f"Point {i} H_mag length mismatch"
            assert len(pt["H_phase_deg"]) == n_freqs, f"Point {i} H_phase_deg length mismatch"
            assert len(pt["coherence"]) == n_freqs, f"Point {i} coherence length mismatch"


class TestPhase2NoExtraFields:
    """Ensure no extra fields that violate additionalProperties: false."""

    def test_wolf_candidates_no_extra_root_fields(self, synthetic_session_dir: Path):
        path = synthetic_session_dir / "derived" / "wolf_candidates.json"
        data = json.loads(path.read_text(encoding="utf-8"))

        allowed_root = {"schema_version", "wsi_threshold", "coherence_threshold", "candidates", "provenance"}
        actual_root = set(data.keys())
        extra = actual_root - allowed_root
        assert not extra, f"Extra root fields in wolf_candidates.json: {extra}"

    def test_ods_snapshot_no_extra_root_fields(self, synthetic_session_dir: Path):
        path = synthetic_session_dir / "derived" / "ods_snapshot.json"
        data = json.loads(path.read_text(encoding="utf-8"))

        allowed_root = {"schema_version", "capdir", "freqs_hz", "points", "provenance"}
        actual_root = set(data.keys())
        extra = actual_root - allowed_root
        assert not extra, f"Extra root fields in ods_snapshot.json: {extra}"
