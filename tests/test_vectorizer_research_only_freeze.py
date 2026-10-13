"""Integrity checks for VECTORIZER-HARVEST-FREEZE-001.

These tests protect the governance boundary only. They do not exercise or repair
vectorizer algorithms.
"""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_relocated_tier_a_files_are_absent_from_runtime_spine():
    absent = [
        ROOT / "services/photo-vectorizer/cognitive_extractor.py",
        ROOT / "services/photo-vectorizer/cognitive_extraction_engine.py",
        ROOT / "services/photo-vectorizer/extract_body_grid.py",
        ROOT / "services/photo-vectorizer/extract_body_grid_v2.py",
        ROOT / "services/photo-vectorizer/extract_body_grid_v3.py",
        ROOT / "services/photo-vectorizer/extract_body_grid_v4.py",
        ROOT / "services/photo-vectorizer/extract_body_grid_v5.py",
        ROOT / "services/blueprint-import/vectorizer_phase2.py",
    ]
    assert all(not p.exists() for p in absent)


def test_existing_semantic_import_gate_stays_green():
    script = ROOT / "scripts/governance/check_semantic_sandbox_imports.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_lifecycle_records_retain_research_only():
    text = (ROOT / "docs/governance/VECTORIZER_COMPONENT_LIFECYCLE.md").read_text(encoding="utf-8")
    assert "RETAIN_RESEARCH_ONLY" in text
    assert "zero production authority" in text


def test_enhanced_is_not_documented_as_production_qualified():
    text = (ROOT / "docs/governance/VECTORIZER_CANONICAL_PATHS.md").read_text(encoding="utf-8")
    row = next(line for line in text.splitlines() if line.startswith("| `enhanced` |"))
    assert "API_EXPOSED_EXPERIMENTAL" in row
    assert "| PRODUCTION |" not in row


def test_migration_plan_no_longer_claims_tier_a_is_unexecuted_proposal():
    text = (ROOT / "docs/governance/VECTORIZER_SANDBOX_MIGRATION_PLAN.md").read_text(encoding="utf-8")
    assert "**Status:** TIER A EXECUTED" in text


def test_closeout_preserves_current_runtime():
    text = (
        ROOT
        / "docs/investigations/vectorizer-recovery-retirement_2026-10/HARVEST_AND_FREEZE.md"
    ).read_text(encoding="utf-8")
    assert "RETAIN_RESEARCH_ONLY" in text
    assert "current canonical production vectorizer remains in service unchanged" in text
    assert "does **not** authorize deletion" in text
