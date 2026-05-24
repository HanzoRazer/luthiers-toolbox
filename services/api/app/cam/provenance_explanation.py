"""
Provenance Explanation

CAM Dev Order 8C: Model for provenance explanation artifacts.

Provides:
  - ProvenanceExplanationArtifact model
  - Explanation validation
  - Summary helpers

Core principle:
  Provenance explanations make manufacturing decisions human-comprehensible.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ProvenanceExplanationArtifact(BaseModel):
    """
    Provenance explanation artifact.

    Provides human-readable explanation for a manufacturing artifact.
    """

    explanation_id: str = Field(
        default_factory=lambda: f"pea-{uuid4().hex[:12]}",
        description="Unique explanation identifier"
    )

    artifact_id: str = Field(
        ...,
        description="ID of the artifact being explained"
    )

    explanation_text: str = Field(
        ...,
        min_length=1,
        description="Human-readable explanation"
    )

    provenance_chain: List[str] = Field(
        default_factory=list,
        description="Chain of provenance references"
    )

    source_layer: Optional[str] = Field(
        default=None,
        description="Source layer that produced this artifact"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    deterministic_explanation_hash: str = Field(
        default="",
        description="Deterministic hash of explanation state"
    )

    def compute_hash(self) -> str:
        """Compute deterministic hash of explanation state."""
        hash_input = {
            "artifact_id": self.artifact_id,
            "explanation_text": self.explanation_text,
            "provenance_chain": self.provenance_chain,
            "source_layer": self.source_layer,
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def create_provenance_explanation(
    artifact_id: str,
    explanation_text: str,
    provenance_chain: Optional[List[str]] = None,
    source_layer: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> ProvenanceExplanationArtifact:
    """Create a provenance explanation artifact."""
    explanation = ProvenanceExplanationArtifact(
        artifact_id=artifact_id,
        explanation_text=explanation_text,
        provenance_chain=provenance_chain or [],
        source_layer=source_layer,
        metadata=metadata or {},
    )
    explanation.deterministic_explanation_hash = explanation.compute_hash()
    return explanation


def validate_provenance_explanation(
    explanation: ProvenanceExplanationArtifact,
) -> tuple[bool, List[str]]:
    """Validate a provenance explanation artifact."""
    issues: List[str] = []

    if not explanation.artifact_id:
        issues.append("Missing artifact_id")

    if not explanation.explanation_text:
        issues.append("Missing explanation_text")

    return len(issues) == 0, issues


def get_explanation_summary(explanation: ProvenanceExplanationArtifact) -> Dict[str, Any]:
    """Get explanation summary for API response."""
    return {
        "explanation_id": explanation.explanation_id,
        "artifact_id": explanation.artifact_id,
        "explanation_text": explanation.explanation_text[:100] + "..." if len(explanation.explanation_text) > 100 else explanation.explanation_text,
        "provenance_chain_length": len(explanation.provenance_chain),
        "source_layer": explanation.source_layer,
        "created_at": explanation.created_at.isoformat(),
    }
