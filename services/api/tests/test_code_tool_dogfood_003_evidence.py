"""CODE-TOOL-DOGFOOD-003 — evidence integrity.

Checks the committed bundle against the source blobs it pins. It does not run
code-audit and does not rerun the Melody Maker conversion.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
BUNDLE = REPO_ROOT / "docs" / "investigations" / "code-tool-dogfood_2026-10-05"
RUNS = BUNDLE / "DETECTOR_RUNS.json"
REQUIRED = (
    "README.md",
    "BASELINE.md",
    "F2_HOLLOW_GUARANTEE.md",
    "F3_FAILURE_MIMICS_SUCCESS.md",
    "DETECTOR_RUNS.json",
    "DETECTOR_RUNS.md",
    "ADJUDICATION.md",
)
PERMITTED = {
    "REACH_GAP",
    "SIGNATURE_GAP",
    "CONFIGURATION_GAP",
    "DETECTED_UNDISPOSITIONED",
    "TOOL_UNAVAILABLE",
}
FORBIDDEN_PREFIXES = (
    "services/photo-vectorizer/",
    "services/api/app/",
    "services/blueprint-import/",
)
ALLOWED_CHANGED = {
    "docs/investigations/code-tool-dogfood_2026-10-05/README.md",
    "docs/investigations/code-tool-dogfood_2026-10-05/BASELINE.md",
    "docs/investigations/code-tool-dogfood_2026-10-05/F2_HOLLOW_GUARANTEE.md",
    "docs/investigations/code-tool-dogfood_2026-10-05/F3_FAILURE_MIMICS_SUCCESS.md",
    "docs/investigations/code-tool-dogfood_2026-10-05/DETECTOR_RUNS.json",
    "docs/investigations/code-tool-dogfood_2026-10-05/DETECTOR_RUNS.md",
    "docs/investigations/code-tool-dogfood_2026-10-05/ADJUDICATION.md",
    "services/api/tests/test_code_tool_dogfood_003_evidence.py",
    ".cbsp21/patches/code-tool-dogfood-003.json",
}
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SECRET = re.compile(r"(ghp_|ghs_|github_pat_|/home/|/Users/|BEGIN [A-Z ]*PRIVATE KEY)")


def _runs() -> dict:
    return json.loads(RUNS.read_text(encoding="utf-8"))


def _bundle_text() -> str:
    return "\n".join((BUNDLE / name).read_text(encoding="utf-8") for name in REQUIRED)


def test_ctd_required_files_exist():
    missing = [name for name in REQUIRED if not (BUNDLE / name).exists()]
    assert missing == []


def test_ctd_each_fixture_classified_once():
    classifications = _runs()["classifications"]
    assert list(classifications) == ["F-2", "F-3"]
    assert set(classifications.values()) <= PERMITTED
    matrix = (BUNDLE / "DETECTOR_RUNS.md").read_text(encoding="utf-8")
    assert len(re.findall(r"^\| F-2 \|", matrix, flags=re.M)) == 1
    assert len(re.findall(r"^\| F-3 \|", matrix, flags=re.M)) == 1


def test_ctd_commands_have_exit_codes_and_digests():
    runs = _runs()["runs"]
    assert runs
    for run in runs:
        assert isinstance(run["argv"], list) and run["argv"]
        assert isinstance(run["exit_code"], int)
        assert SHA256.match(run["stdout_sha256"])
        assert SHA256.match(run["stderr_sha256"])


def test_ctd_source_blobs_match_baseline():
    for pin in _runs()["source_blobs"]:
        path = REPO_ROOT / pin["path"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == pin["content_sha256"]
        blob = subprocess.run(
            ["git", "hash-object", pin["path"]],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        assert blob == pin["git_blob_sha"]


def test_ctd_defects_not_repaired_and_no_secrets():
    data = _runs()
    assert data["defects_repaired"] is False
    text = _bundle_text()
    assert "Neither F-2 nor F-3 was repaired." in text
    assert "repaired F-2" not in text
    assert "repaired F-3" not in text
    assert SECRET.search(text) is None
    assert SECRET.search(json.dumps(data)) is None


def test_ctd_declared_surface_excludes_production_sources():
    manifest = json.loads(
        (REPO_ROOT / ".cbsp21" / "patches" / "code-tool-dogfood-003.json").read_text(
            encoding="utf-8"
        )
    )
    declared = set(manifest["scope"]["files_expected_to_change"])
    assert declared == ALLOWED_CHANGED
    for path in declared:
        assert not path.startswith(FORBIDDEN_PREFIXES)
        assert path != "services/api/tests/test_text_masking_regression.py"


def test_ctd_full_repository_recorded_and_selection_not_invented():
    data = _runs()
    roles = {run["role"] for run in data["runs"]}
    assert "normal_and_full_repository" in roles
    assert "direct_f2" in roles
    assert "direct_f3_ocr" in roles
    assert data["changed_file_selection"]["supported_by_default_cli"] is False
    assert data["changed_file_selection"]["command_run"] is None
    assert data["scan_topology"]["full_repository_mode"].startswith("same command")
