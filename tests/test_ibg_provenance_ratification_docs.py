"""
Tests for IBG Provenance Ratification documentation (MRP-6C).

Validates governance documentation state without testing runtime behavior.
All 5 IBG DXF paths must remain BLOCKED_PROVENANCE until R1 ratification completes.
"""

import re
from pathlib import Path

import pytest


GOVERNANCE_DIR = Path(__file__).parent.parent / "docs" / "governance"

REQUIRED_DOCS = [
    "IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md",
    "IBG_PROVENANCE_RATIFICATION_PACKET.md",
    "IBG_PROVENANCE_ATTACHMENT_FIELD_MATRIX.md",
    "IBG_DXF_LIFECYCLE_MAPPING_ADDENDUM.md",
    "IBG_PROVENANCE_GOVERNANCE_ENTRY.md",
]

BLOCKED_PATHS = [
    ("body_contour_solver.py", 777),
    ("body_contour_solver.py", 808),
    ("arc_reconstructor.py", 1116),
    ("arc_reconstructor.py", 1279),
    ("arc_reconstructor.py", 1303),
]

REQUIRED_ATTACHMENT_FIELDS = {
    "provenance_record_id",
    "source_artifact_id",
    "ibg_run_id",
    "candidate_id",
    "epistemic_status",
    "authority_state",
    "confidence_type",
    "topology_integrity_score",
    "reconstruction_method",
    "operator_review_status",
    "export_intent",
    "lifecycle_target",
    "created_at",
    "schema_version",
}


class TestIBGProvenanceDocumentation:
    """Validate IBG provenance ratification documentation exists and is consistent."""

    @pytest.mark.parametrize("doc_name", REQUIRED_DOCS)
    def test_required_docs_exist(self, doc_name: str) -> None:
        """All R1 ratification prep documents must exist."""
        doc_path = GOVERNANCE_DIR / doc_name
        assert doc_path.exists(), f"Missing required doc: {doc_name}"

    def test_timeline_marks_r0_complete(self) -> None:
        """Timeline must mark R0 as complete."""
        timeline = GOVERNANCE_DIR / "IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md"
        content = timeline.read_text(encoding="utf-8")
        assert "R0 — Documentation convergence (COMPLETE" in content or \
               "Phase R0 — Documentation convergence (COMPLETE" in content, \
               "R0 must be marked COMPLETE in timeline"

    def test_timeline_lists_all_blocked_paths(self) -> None:
        """Timeline must list all 5 blocked paths."""
        timeline = GOVERNANCE_DIR / "IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md"
        content = timeline.read_text(encoding="utf-8")
        for filename, line in BLOCKED_PATHS:
            assert filename in content, f"Missing blocked path: {filename}"

    def test_field_matrix_lists_required_fields(self) -> None:
        """Field matrix must document all required attachment fields."""
        matrix = GOVERNANCE_DIR / "IBG_PROVENANCE_ATTACHMENT_FIELD_MATRIX.md"
        content = matrix.read_text(encoding="utf-8")
        for field in REQUIRED_ATTACHMENT_FIELDS:
            assert field in content, f"Missing required field in matrix: {field}"

    def test_governance_entry_status_is_blocker(self) -> None:
        """Governance entry must show ACTIVE_BLOCKER status."""
        entry = GOVERNANCE_DIR / "IBG_PROVENANCE_GOVERNANCE_ENTRY.md"
        content = entry.read_text(encoding="utf-8")
        assert "ACTIVE_BLOCKER" in content, "Governance entry must be ACTIVE_BLOCKER"
        assert "RATIFICATION_PENDING" in content, "Must show RATIFICATION_PENDING"

    def test_no_lifecycle_governed_claims(self) -> None:
        """No document may claim IBG paths are LIFECYCLE_GOVERNED."""
        for doc_name in REQUIRED_DOCS:
            doc_path = GOVERNANCE_DIR / doc_name
            content = doc_path.read_text(encoding="utf-8")
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                if "body_contour_solver" in line or "arc_reconstructor" in line:
                    assert "LIFECYCLE_GOVERNED" not in line, \
                        f"{doc_name}:{i} — IBG path cannot be LIFECYCLE_GOVERNED before R2"

    def test_blocked_provenance_preserved(self) -> None:
        """All IBG paths must remain BLOCKED_PROVENANCE classification."""
        timeline = GOVERNANCE_DIR / "IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md"
        content = timeline.read_text(encoding="utf-8")
        assert "BLOCKED_PROVENANCE" in content
        assert content.count("BLOCKED") >= 5, "Must show blocked status for all 5 paths"

    def test_ratification_packet_has_schema(self) -> None:
        """Ratification packet must define IBGProvenanceAttachment schema."""
        packet = GOVERNANCE_DIR / "IBG_PROVENANCE_RATIFICATION_PACKET.md"
        content = packet.read_text(encoding="utf-8")
        assert "IBGProvenanceAttachment" in content, "Must define attachment schema"
        assert "dataclass" in content or "@dataclass" in content, \
            "Schema should show dataclass definition"

    def test_lifecycle_addendum_forbids_direct_jump(self) -> None:
        """Lifecycle addendum must forbid direct BLOCKED_PROVENANCE → LIFECYCLE_GOVERNED."""
        addendum = GOVERNANCE_DIR / "IBG_DXF_LIFECYCLE_MAPPING_ADDENDUM.md"
        content = addendum.read_text(encoding="utf-8")
        assert "FORBIDDEN" in content, "Must explicitly forbid direct promotion"
        assert "Rule 1" in content or "No Direct Jump" in content, \
            "Must state no-direct-jump rule"


class TestIBGProvenanceDocumentCrossReferences:
    """Validate cross-references between IBG provenance documents."""

    def test_timeline_references_all_docs(self) -> None:
        """Timeline must reference all related governance documents."""
        timeline = GOVERNANCE_DIR / "IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md"
        content = timeline.read_text(encoding="utf-8")
        expected_refs = [
            "EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX",
            "CANONICAL_PROVENANCE_MODEL",
            "IBG_CONSTITUTIONAL_RUNTIME_FOUNDATION",
        ]
        for ref in expected_refs:
            assert ref in content, f"Timeline missing reference to {ref}"

    def test_governance_entry_links_to_packet(self) -> None:
        """Governance entry must link to ratification packet."""
        entry = GOVERNANCE_DIR / "IBG_PROVENANCE_GOVERNANCE_ENTRY.md"
        content = entry.read_text(encoding="utf-8")
        assert "IBG_PROVENANCE_RATIFICATION_PACKET" in content

    def test_field_matrix_maps_to_dxf_lifecycle_context(self) -> None:
        """Field matrix must show mapping to DxfLifecycleContext."""
        matrix = GOVERNANCE_DIR / "IBG_PROVENANCE_ATTACHMENT_FIELD_MATRIX.md"
        content = matrix.read_text(encoding="utf-8")
        assert "DxfLifecycleContext" in content, "Must map to DxfLifecycleContext"
