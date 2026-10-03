"""VECTORIZER-CI-BOUNDARY-001 — evidence integrity.

Checks the committed evidence bundle against the repository it describes. It does
not run the vectorizer and does not read the Melody Maker PDF; the measurements
themselves are recorded in TEST_RUNTIME_CENSUS.json.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
BUNDLE = REPO_ROOT / "docs" / "investigations" / "vectorizer-ci-boundary_2026-10-03"
CENSUS = BUNDLE / "TEST_RUNTIME_CENSUS.json"
MANIFEST = REPO_ROOT / ".cbsp21" / "patches" / "vectorizer-ci-boundary-001.json"
CORE_CI = REPO_ROOT / ".github" / "workflows" / "core_ci.yml"
DEDICATED = REPO_ROOT / ".github" / "workflows" / "vectorizer-regression.yml"
MAKEFILE = REPO_ROOT / "Makefile"
TESTS_DIR = REPO_ROOT / "services" / "api" / "tests"
REGRESSION_MODULE = TESTS_DIR / "test_text_masking_regression.py"
GENERATOR = REPO_ROOT / "scripts" / "investigations" / "generate_vectorizer_ci_boundary.py"

MARKER = "vectorizer_regression"
LARGE_COUNT = 266_359
ELLIPSE_COUNT = 1_116
CUATRO_SHA256 = "41e62ec08c1c748681f43d05c1abab305978b5cce6ef1278a6ddc36be639613a"
CUATRO_LINES = 128_997
BUNDLE_FILES = (
    "README.md",
    "TEST_RUNTIME_CENSUS.md",
    "TEST_RUNTIME_CENSUS.json",
    "CUATRO_PROVENANCE.md",
    "CI_REACHABILITY.md",
    "SANDBOX_BOUNDARY.md",
    "ADJUDICATION.md",
)
# Production surfaces this increment must not touch.
FORBIDDEN_PREFIXES = (
    "services/photo-vectorizer/",
    "services/api/app/",
)


def _census() -> dict:
    return json.loads(CENSUS.read_text(encoding="utf-8"))


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _regression_test_ids() -> list[str]:
    tree = ast.parse(REGRESSION_MODULE.read_text(encoding="utf-8"))
    ids = []
    for cls in tree.body:
        if isinstance(cls, ast.ClassDef):
            ids += [f"{cls.name}::{fn.name}" for fn in cls.body
                    if isinstance(fn, ast.FunctionDef) and fn.name.startswith("test_")]
    return ids


def test_bundle_is_complete():
    missing = [name for name in BUNDLE_FILES if not (BUNDLE / name).exists()]
    assert missing == []


def test_census_markdown_is_rendered_from_its_json():
    result = subprocess.run([sys.executable, str(GENERATOR), "--check"],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_every_measured_test_has_a_disposition():
    tests = _census()["tests"]
    assert tests
    assert all(t["disposition"].strip() for t in tests)
    assert len({t["id"] for t in tests}) == len(tests)


def test_the_large_count_producer_is_named_and_is_not_the_ellipse():
    census = _census()
    obs = census["large_count_observation"]
    assert obs["value"] == LARGE_COUNT
    by_test = {t["test_id"]: t for t in census["tests"]}
    assert obs["producer_tests"]
    for test_id in obs["producer_tests"]:
        assert by_test[test_id]["entity_count"]["ci"] == LARGE_COUNT
        assert by_test[test_id]["source_fixture"].endswith("gibson_melody_maker_blueprint.pdf")
    ellipse = [t for t in census["tests"] if t["test_id"].endswith("test_convert_marks_result_degraded_when_ocr_fails")]
    assert len(ellipse) == 1
    assert ellipse[0]["entity_count"]["ci"] == ELLIPSE_COUNT
    assert ellipse[0]["test_id"] not in obs["producer_tests"]


def test_ellipse_contract_keeps_its_emission_and_gains_only_a_ceiling():
    source = (TESTS_DIR / "test_text_masking.py").read_text(encoding="utf-8")
    body = source.split("def test_convert_marks_result_degraded_when_ocr_fails", 1)[1].split("\n    def ", 1)[0]
    assert "convert_enhanced(" in body
    assert "max_entities" not in body  # no converter cap, so no CAP_EXCEEDED
    assert "ConversionStatus.DEGRADED" in body and "out.exists()" in body
    ceiling = int(re.search(r"result\.line_count <= ([\d_]+)", body).group(1).replace("_", ""))
    assert ceiling >= 2 * ELLIPSE_COUNT


def test_both_cuatro_paths_are_recorded_present_identical_and_unresolved():
    cuatro = _census()["cuatro"]
    assert len(cuatro["paths"]) == 2
    assert cuatro["manufacturing_authority"] == "none"
    for entry in cuatro["paths"]:
        path = REPO_ROOT / entry["path"]
        data = path.read_bytes()  # absent file fails here: nothing may be deleted or moved
        assert hashlib.sha256(data).hexdigest() == entry["sha256"] == CUATRO_SHA256
        assert len(data) == entry["bytes"]
        assert len(re.findall(rb"(?m)^\s*0\r?\n\s*LINE\r?\n", data)) == entry["line_count"] == CUATRO_LINES
        assert entry["role"] == "ROLE_UNRESOLVED"
        assert entry["candidate_roles"] == ["benchmark witness", "plan-package artifact"]
    assert cuatro["paths"][0]["path"] != cuatro["paths"][1]["path"]


def test_default_ci_excludes_only_the_vectorizer_regression_marker():
    expression = _census()["default_ci"]["expression_after"]
    assert expression == f"not {MARKER}"
    assert f'python -m pytest -q -m "{expression}"' in CORE_CI.read_text(encoding="utf-8")
    makefile = MAKEFILE.read_text(encoding="utf-8")
    assert f"API_TEST_MARKERS ?= {expression}" in makefile
    assert '-m "$(API_TEST_MARKERS)"' in makefile


def test_the_marker_is_applied_in_exactly_one_module():
    users = []
    for path in TESTS_DIR.rglob("*.py"):
        if path.resolve() == Path(__file__).resolve():
            continue
        if re.search(rf"pytest\.mark\.{MARKER}\b", path.read_text(encoding="utf-8", errors="replace")):
            users.append(path.relative_to(TESTS_DIR).as_posix())
    assert users == ["test_text_masking_regression.py"]
    assert f"pytestmark = pytest.mark.{MARKER}" in REGRESSION_MODULE.read_text(encoding="utf-8")


def test_excluded_and_dedicated_sets_are_the_same_complete_set():
    default_ci = _census()["default_ci"]
    module_ids = sorted(f"tests/test_text_masking_regression.py::{i}" for i in _regression_test_ids())
    assert sorted(default_ci["excluded"]) == module_ids
    assert sorted(default_ci["dedicated"]) == module_ids


def test_dedicated_workflow_is_bounded_manual_and_path_triggered():
    text = DEDICATED.read_text(encoding="utf-8")
    assert f"-m {MARKER}" in text
    assert re.search(r"timeout-minutes:\s*\d+", text)
    assert "workflow_dispatch:" in text and "paths:" in text
    assert "schedule:" not in text


def test_no_production_vectorizer_or_authority_file_changed():
    declared = sorted(_census()["changed_files"])
    manifest_paths = sorted(f["path"] for f in _manifest()["files"])
    assert declared == manifest_paths
    assert not [p for p in declared if p.startswith(FORBIDDEN_PREFIXES)]
    assert not [p for p in declared if p.endswith(".dxf")]


def test_records_are_cited_and_one_next_adjudication_is_named():
    readme = (BUNDLE / "README.md").read_text(encoding="utf-8")
    boundary = (BUNDLE / "SANDBOX_BOUNDARY.md").read_text(encoding="utf-8")
    assert "VEC-ROOT-001" in readme and "c8ad3ae4" in readme
    assert "VECTORIZER_COMPONENT_LIFECYCLE.md" in boundary
    assert "body_lexicon.md" in boundary
    for term in ("ARCHIVAL_TRACE", "DESIGN_CANDIDATE"):
        assert term in boundary  # recorded as not introduced
    nxt = _census()["next_adjudication"]
    assert isinstance(nxt, str) and nxt.strip()
    assert nxt in (BUNDLE / "ADJUDICATION.md").read_text(encoding="utf-8")
