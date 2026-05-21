"""
Structural validation for Research Wave Index 1A documentation.

No production code changes are tested here.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
RESEARCH_DIR = REPO_ROOT / "docs" / "research"

CORE_1A_SPINE_DOCS = [
    "RESEARCH_WAVE_INDEX.md",
    "IBG_RUNTIME_POSITION.md",
    "IBG_LINEAGE_MAP.md",
    "TOPOLOGY_IDEA_REGISTRY.md",
    "SEMANTIC_DISCOVERY_MATRIX.md",
    "RESEARCH_PLATFORM_SPINE.md",
]

CORE_1B_SPINE_DOCS = [
    "SEMANTIC_INTERPRETATION_TRACE.md",
    "PRIMITIVE_FLOW_ANALYSIS.md",
    "MORPHOLOGY_INTERPRETATION_BOUNDARY.md",
    "TOPOLOGY_CONTINUITY_FAILURES.md",
    "SEMANTIC_OBSERVABILITY_MAP.md",
    "WAVE_1B_RESEARCH_QUESTIONS.md",
]

REQUIRED_DOCS = [
    "README.md",
    "RESEARCH_PLATFORM_1A_ALIGNMENT.md",
    *CORE_1A_SPINE_DOCS,
    *CORE_1B_SPINE_DOCS,
]

SUPPORTING_DOCS = [
    "CAD_KERNEL_BOUNDARY_ANALYSIS.md",
    "gibson_l37_1941_significance.md",
]

REQUIRED_MATRIX_SEEDS = [
    "primitive starvation",
    "slab_body collapse",
    "confidence ≠ authority",
    "visibility ≠ legitimacy",
    "semantic influence ≠ semantic authority",
    "sandbox discovers / runtime ratifies",
]

WAVE_HEADINGS = [
    "Wave 0 — Pre-Constitutional Boundaries",
    "Wave A — Reconstruction Intelligence",
    "Wave B — Evaluation Science",
    "Wave C — Semantic Cognition",
    "Wave D — Constitutional Runtime",
    "Wave E — Workflow / IBG Intake",
]


@pytest.fixture
def readme_text() -> str:
    return (RESEARCH_DIR / "README.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("filename", REQUIRED_DOCS)
def test_research_doc_exists(filename: str) -> None:
    path = RESEARCH_DIR / filename
    assert path.is_file(), f"Missing {path}"


def test_readme_links_to_all_research_docs(readme_text: str) -> None:
    for name in REQUIRED_DOCS:
        if name == "README.md":
            continue
        assert name in readme_text, f"README.md must link to or mention {name}"
    for name in SUPPORTING_DOCS:
        assert name in readme_text, f"README.md must list supporting doc {name}"
    assert "Core Wave 1A Spine" in readme_text
    assert "Core Wave 1B Spine" in readme_text
    assert "Supporting Research Notes" in readme_text
    assert "Constitutional Alignment" in readme_text


def test_ibg_runtime_position_is_non_overlapping_bridge_doc() -> None:
    text = (RESEARCH_DIR / "IBG_RUNTIME_POSITION.md").read_text(encoding="utf-8")
    assert "governed semantic runtime bridge" in text
    assert "not a semantic research sandbox" in text.lower()
    assert "IBG_LINEAGE_MAP.md" in text
    assert "ibg_workflow_pipeline" not in text  # lineage detail stays in lineage map


def test_semantic_matrix_includes_required_seed_discoveries() -> None:
    text = (RESEARCH_DIR / "SEMANTIC_DISCOVERY_MATRIX.md").read_text(encoding="utf-8")
    for seed in REQUIRED_MATRIX_SEEDS:
        assert seed in text, f"SEMANTIC_DISCOVERY_MATRIX missing seed: {seed}"


def test_research_wave_index_contains_all_waves() -> None:
    text = (RESEARCH_DIR / "RESEARCH_WAVE_INDEX.md").read_text(encoding="utf-8")
    for heading in WAVE_HEADINGS:
        assert heading in text, f"RESEARCH_WAVE_INDEX missing {heading}"
    assert "Wave 1B — Semantic Interpretation Trace" in text


def test_wave_1b_trace_doc_exists_and_links_spine() -> None:
    text = (RESEARCH_DIR / "SEMANTIC_INTERPRETATION_TRACE.md").read_text(encoding="utf-8")
    assert "recover_topology" in text
    assert "IBGWorkflowPipeline" in text
    assert "BodyEvidenceCandidate" in text
    assert "emit_review_package" in text


def test_wave_1b_questions_documents_pending_prerequisites() -> None:
    text = (RESEARCH_DIR / "WAVE_1B_RESEARCH_QUESTIONS.md").read_text(encoding="utf-8")
    assert "PENDING / external verification" in text
    assert "PR-1" in text


def test_topology_failures_use_fixture_metadata_fields() -> None:
    text = (RESEARCH_DIR / "TOPOLOGY_CONTINUITY_FAILURES.md").read_text(encoding="utf-8")
    for field in ("fixture_status", "artifact_path", "verification_state"):
        assert field in text, f"TOPOLOGY_CONTINUITY_FAILURES missing {field}"


def test_morphology_boundary_preserves_three_layers() -> None:
    text = (RESEARCH_DIR / "MORPHOLOGY_INTERPRETATION_BOUNDARY.md").read_text(encoding="utf-8")
    assert "Morphology Harvest" in text
    assert "MorphologyDescriptor" in text
    assert "Workflow Pipeline 1A" in text
    assert "non-authoritative" in text
    assert "research-only" in text


def test_observability_map_has_visibility_columns() -> None:
    text = (RESEARCH_DIR / "SEMANTIC_OBSERVABILITY_MAP.md").read_text(encoding="utf-8")
    assert "Current Visibility" in text
    assert "Blind Spot" in text
    assert "Desired Instrumentation" in text


def test_alignment_doc_ratifies_authority_split() -> None:
    text = (RESEARCH_DIR / "RESEARCH_PLATFORM_1A_ALIGNMENT.md").read_text(encoding="utf-8")
    assert "research remembers" in text
    assert "governance ratifies" in text
    assert "docs/governance/" in text


def test_ibg_canonical_objective_ratified() -> None:
    text = (RESEARCH_DIR / "IBG_LINEAGE_MAP.md").read_text(encoding="utf-8")
    assert "provenance-bearing" in text
    assert "human-reviewable body evidence" in text


def test_semantic_matrix_uses_formal_risk_scale() -> None:
    text = (RESEARCH_DIR / "SEMANTIC_DISCOVERY_MATRIX.md").read_text(encoding="utf-8")
    assert "Risk (H/M/L)" in text or "Risk |" in text
    assert "**High**" in text
    assert "**Medium**" in text
    assert "**Low**" in text


def test_ibg_lineage_references_workflow_1a_and_intake_gate() -> None:
    text = (RESEARCH_DIR / "IBG_LINEAGE_MAP.md").read_text(encoding="utf-8")
    assert "Workflow Pipeline 1A" in text or "1A-WORKFLOW" in text
    assert "ibg_workflow_pipeline" in text
    assert "IBGIntakeGate" in text
    assert "BodyEvidenceCandidate" in text
    assert "BodyEvidence" in text


def test_topology_registry_at_least_ten_seed_ideas() -> None:
    text = (RESEARCH_DIR / "TOPOLOGY_IDEA_REGISTRY.md").read_text(encoding="utf-8")
    numbered = re.findall(r"^###\s+\d+\.\s+", text, re.MULTILINE)
    assert len(numbered) >= 10, f"Expected >= 10 topology entries, found {len(numbered)}"


def test_semantic_matrix_includes_sandbox_runtime_separation() -> None:
    text = (RESEARCH_DIR / "SEMANTIC_DISCOVERY_MATRIX.md").read_text(encoding="utf-8")
    assert "Sandbox / runtime separation" in text or "sandbox / runtime" in text.lower()
    assert "vectorizer-sandbox" in text
    assert "luthiers-toolbox" in text
    assert "sandbox discovers" in text.lower() or "runtime ratifies" in text.lower()


def test_platform_spine_defines_layers() -> None:
    text = (RESEARCH_DIR / "RESEARCH_PLATFORM_SPINE.md").read_text(encoding="utf-8")
    for layer in ("Archaeology", "Evaluation", "Reconstruction", "Cognition", "Incubation", "Graduation"):
        assert layer in text, f"RESEARCH_PLATFORM_SPINE missing layer {layer}"


def test_readme_states_no_operational_authority(readme_text: str) -> None:
    assert "not" in readme_text.lower() and "operational authority" in readme_text.lower()


def test_research_index_builder_is_deterministic(tmp_path: Path) -> None:
    import importlib.util
    import json

    script = REPO_ROOT / "scripts" / "research" / "build_research_index.py"
    spec = importlib.util.spec_from_file_location("build_research_index", script)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    out = tmp_path / "research_index.json"
    mod.OUTPUT_PATH = out
    assert mod.main() == 0
    first = out.read_text(encoding="utf-8")
    assert mod.main() == 0
    second = out.read_text(encoding="utf-8")
    assert first == second
    data = json.loads(first)
    assert "generated_at" not in data
    assert data["schema_version"] == 1
    assert data["document_count"] >= len(REQUIRED_DOCS)

