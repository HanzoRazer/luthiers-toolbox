"""Storage seam for LTB evidence records.

Implementations persist records. They do not score them and they do not
decide whether a proposal may be reviewed.
"""
from __future__ import annotations

from typing import Protocol

from app.physical_engineering.evidence_artifact_v1 import LtbStoredEvidenceArtifactV1


class EvidenceRepository(Protocol):
    def save(self, record: LtbStoredEvidenceArtifactV1) -> None:
        """Store one record. Identical bytes may replay. Different bytes may not."""

    def get(self, evidence_id: str) -> LtbStoredEvidenceArtifactV1:
        """Return the record with this id."""

    def list_for_subject(
        self, subject_id: str, subject_revision: str
    ) -> tuple[LtbStoredEvidenceArtifactV1, ...]:
        """Return matching records in evidence-id order."""
