"""
IBG export provenance bridge (DO 80 Phase D).

Maps constitutional intake objects to save-boundary ProvenanceAttachmentDraft.
Default status remains BLOCKED until R1 ratification marks attachments RATIFIED.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from app.governance.provenance_attachment import (
    ProvenanceAttachmentDraft,
    create_ibg_provenance_draft,
)

if TYPE_CHECKING:
    from app.instrument_geometry.body.ibg.body_evidence_candidate import (
        BodyEvidenceCandidate,
    )


def _derivation_chain_from_candidate(candidate: "BodyEvidenceCandidate") -> List[str]:
    if candidate.provenance and candidate.provenance.derivation_chain:
        return list(candidate.provenance.derivation_chain)
    if candidate.provenance and candidate.provenance.derived_from:
        return [candidate.provenance.derived_from]
    return [candidate.candidate_id]


def _source_artifact_from_candidate(candidate: "BodyEvidenceCandidate") -> str:
    if candidate.provenance and candidate.provenance.source_artifact:
        return candidate.provenance.source_artifact
    return candidate.candidate_id


def _transformation_method_from_candidate(candidate: "BodyEvidenceCandidate") -> str:
    if candidate.provenance and candidate.provenance.transformation_history:
        last = candidate.provenance.transformation_history[-1]
        return last.stage.value if hasattr(last.stage, "value") else str(last.stage)
    return "body_evidence_candidate_export"


def attachment_from_body_evidence_candidate(
    candidate: "BodyEvidenceCandidate",
    *,
    export_intent: str,
    ibg_run_id: Optional[str] = None,
) -> ProvenanceAttachmentDraft:
    """
    Build a provenance attachment draft for an IBG DXF save boundary.

    Remains non-exportable (BLOCKED) until governance ratification (R1) and
    explicit RATIFIED status assignment (Phase E).
    """
    run_id = ibg_run_id or candidate.metadata.get("ibg_run_id") or candidate.candidate_id
    source = _source_artifact_from_candidate(candidate)

    draft = create_ibg_provenance_draft(
        attachment_id=f"ibg-export:{run_id}:{export_intent}",
        source_artifact_id=source,
        derivation_chain=_derivation_chain_from_candidate(candidate),
        transformation_stage=export_intent,
        transformation_method=_transformation_method_from_candidate(candidate),
    )
    draft.metadata["candidate_id"] = candidate.candidate_id
    draft.metadata["export_intent"] = export_intent
    draft.metadata["ibg_run_id"] = run_id
    draft.metadata["epistemic_status"] = candidate.confidence.confidence_type.value
    draft.metadata["authority_state"] = candidate.authority.current_state.value
    if candidate.provenance:
        draft.metadata["topology_integrity_score"] = (
            candidate.provenance.topology_integrity_score
        )
    return draft
