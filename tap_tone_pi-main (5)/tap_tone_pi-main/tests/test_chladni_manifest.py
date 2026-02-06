from __future__ import annotations
"""
Validates that the Chladni demo produces a run-level manifest with the
expected entries (WAV, peaks, images, chladni_run.json) and that the
recorded sha256 values match recomputed hashes. Also asserts idempotency:
re-running the indexer does not duplicate manifest entries.
"""
import json
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUN_DIR = REPO / "out" / "DEMO" / "chladni"
MANIFEST = RUN_DIR / "manifest.json"

def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def _run_cmd(args):
    subprocess.check_call(args, cwd=REPO)

def _clean_run_dir():
    """Remove existing demo artifacts to ensure clean state."""
    if RUN_DIR.exists():
        shutil.rmtree(RUN_DIR)

def _ensure_demo_artifacts():
    # Clean before running to ensure deterministic state
    _clean_run_dir()
    # The make_demo.py script runs the full flow:
    # WAV → peaks_from_wav → index_patterns (which appends to manifest)
    _run_cmd([sys.executable, "examples/chladni/make_demo.py"])

def test_chladni_manifest_hashes_and_idempotency():
    _ensure_demo_artifacts()

    # Must exist after index_patterns integration
    assert MANIFEST.exists(), "manifest.json was not created"

    doc = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert doc.get("schema_id") == "measurement_manifest"
    assert doc.get("schema_version") == "1.0"
    artifacts = doc.get("artifacts") or []
    assert isinstance(artifacts, list)

    # Expected relative paths in the demo
    expected = {
        "capture.wav": "chladni_wav",
        "peaks.json": "chladni_peaks",
        "F0148.png": "chladni_image",
        "F0226.png": "chladni_image",
        "chladni_run.json": "chladni_run",
    }

    # Map manifest entries by filename
    by_name = {}
    for a in artifacts:
        p = a.get("path")
        if not isinstance(p, str):
            continue
        name = Path(p).name
        by_name[name] = a

    # Check presence, type, and sha256 correctness
    for fname, atype in expected.items():
        assert fname in by_name, f"missing manifest entry for {fname}"
        entry = by_name[fname]
        assert entry.get("artifact_type") == atype, f"wrong type for {fname}"
        abs_path = RUN_DIR / fname
        assert abs_path.exists(), f"file not found on disk: {abs_path}"
        want_sha = _sha256_file(abs_path)
        have_sha = entry.get("sha256")
        assert have_sha == want_sha, f"sha256 mismatch for {fname}"

    # Idempotency: re-run demo; manifest should not duplicate entries
    before_count = len(artifacts)
    _run_cmd([sys.executable, "examples/chladni/make_demo.py"])
    doc2 = json.loads(MANIFEST.read_text(encoding="utf-8"))
    after_count = len(doc2.get("artifacts") or [])
    assert after_count == before_count, "manifest append is not idempotent; artifact duplication detected"
