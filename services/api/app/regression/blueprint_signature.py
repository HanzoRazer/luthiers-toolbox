"""
Blueprint Reader Output Signature
=================================

Signature model specific to Blueprint Reader MVP outputs.
Captures dimensional, structural, and quality characteristics.

MRP-1B: Regression & Behavioral Observability Infrastructure
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .signature_schema import RegressionSignature


@dataclass
class BlueprintOutputSignature(RegressionSignature):
    """
    Signature for Blueprint Reader vectorization output.

    Captures the observable characteristics of a vectorization run
    that should remain stable across code changes.
    """

    # Blueprint-specific dimensions
    body_width_mm: float = 0.0
    body_height_mm: float = 0.0

    # DXF artifact characteristics
    dxf_entity_count: int = 0
    dxf_closed_contours: int = 0
    dxf_layers: List[str] = field(default_factory=list)

    # SVG artifact characteristics
    svg_path_count: int = 0
    svg_present: bool = False

    # Selection characteristics
    candidate_count: int = 0
    selected_index: int = -1
    selection_score: float = 0.0
    winner_margin: float = 0.0

    # Recommendation
    recommendation_action: str = ""
    recommendation_confidence: float = 0.0

    # Processing metadata
    mode: str = ""
    spec_name: Optional[str] = None

    def __post_init__(self):
        """Populate base class fields from blueprint-specific fields."""
        self.system_id = "BLUEPRINT_READER_MVP"

        # Populate dimensions dict
        self.dimensions = {
            "body_width_mm": self.body_width_mm,
            "body_height_mm": self.body_height_mm,
            "selection_score": self.selection_score,
            "winner_margin": self.winner_margin,
            "recommendation_confidence": self.recommendation_confidence,
        }

        # Populate counts dict
        self.counts = {
            "dxf_entity_count": self.dxf_entity_count,
            "dxf_closed_contours": self.dxf_closed_contours,
            "dxf_layer_count": len(self.dxf_layers),
            "svg_path_count": self.svg_path_count,
            "candidate_count": self.candidate_count,
            "selected_index": self.selected_index,
        }

        # Populate flags dict
        self.flags = {
            "svg_present": self.svg_present,
            "has_closed_contours": self.dxf_closed_contours > 0,
            "has_selection": self.selected_index >= 0,
            "is_accepted": self.recommendation_action == "accept",
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary with blueprint-specific fields."""
        base = super().to_dict()
        base.update({
            "body_width_mm": self.body_width_mm,
            "body_height_mm": self.body_height_mm,
            "dxf_entity_count": self.dxf_entity_count,
            "dxf_closed_contours": self.dxf_closed_contours,
            "dxf_layers": self.dxf_layers,
            "svg_path_count": self.svg_path_count,
            "svg_present": self.svg_present,
            "candidate_count": self.candidate_count,
            "selected_index": self.selected_index,
            "selection_score": self.selection_score,
            "winner_margin": self.winner_margin,
            "recommendation_action": self.recommendation_action,
            "recommendation_confidence": self.recommendation_confidence,
            "mode": self.mode,
            "spec_name": self.spec_name,
        })
        return base

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BlueprintOutputSignature:
        """Deserialize from dictionary."""
        return cls(
            artifact_id=data["artifact_id"],
            signature_version=data.get("signature_version", "1.0.0"),
            captured_at=data.get("captured_at", ""),
            input_hash=data.get("input_hash"),
            input_description=data.get("input_description"),
            notes=data.get("notes"),
            body_width_mm=data.get("body_width_mm", 0.0),
            body_height_mm=data.get("body_height_mm", 0.0),
            dxf_entity_count=data.get("dxf_entity_count", 0),
            dxf_closed_contours=data.get("dxf_closed_contours", 0),
            dxf_layers=data.get("dxf_layers", []),
            svg_path_count=data.get("svg_path_count", 0),
            svg_present=data.get("svg_present", False),
            candidate_count=data.get("candidate_count", 0),
            selected_index=data.get("selected_index", -1),
            selection_score=data.get("selection_score", 0.0),
            winner_margin=data.get("winner_margin", 0.0),
            recommendation_action=data.get("recommendation_action", ""),
            recommendation_confidence=data.get("recommendation_confidence", 0.0),
            mode=data.get("mode", ""),
            spec_name=data.get("spec_name"),
        )


def extract_blueprint_signature(
    result_dict: Dict[str, Any],
    artifact_id: str,
    input_bytes: Optional[bytes] = None,
    input_description: Optional[str] = None,
) -> BlueprintOutputSignature:
    """
    Extract a signature from a Blueprint Reader result dictionary.

    Args:
        result_dict: The response dict from BlueprintResult.to_response_dict()
        artifact_id: Identifier for this artifact (e.g., "dreadnought_test_001")
        input_bytes: Optional input file bytes for hashing
        input_description: Optional description of input

    Returns:
        BlueprintOutputSignature capturing the result characteristics
    """
    # Extract nested values safely
    dimensions = result_dict.get("dimensions", {})
    artifacts = result_dict.get("artifacts", {})
    dxf = artifacts.get("dxf", {})
    svg = artifacts.get("svg", {})
    selection = result_dict.get("selection", {})
    recommendation = result_dict.get("recommendation", {})

    # Compute input hash if bytes provided
    input_hash = None
    if input_bytes:
        input_hash = hashlib.sha256(input_bytes).hexdigest()[:16]

    return BlueprintOutputSignature(
        artifact_id=artifact_id,
        input_hash=input_hash,
        input_description=input_description,
        body_width_mm=dimensions.get("width_mm", 0.0),
        body_height_mm=dimensions.get("height_mm", 0.0),
        dxf_entity_count=dxf.get("entity_count", 0),
        dxf_closed_contours=dxf.get("closed_contours", 0),
        dxf_layers=[],  # Would need DXF parsing to extract
        svg_path_count=svg.get("path_count", 0),
        svg_present=svg.get("present", False),
        candidate_count=selection.get("candidate_count", 0),
        selected_index=selection.get("selected_index", -1),
        selection_score=selection.get("selection_score", 0.0),
        winner_margin=selection.get("winner_margin", 0.0),
        recommendation_action=recommendation.get("action", ""),
        recommendation_confidence=recommendation.get("confidence", 0.0),
        mode=result_dict.get("mode", ""),
        spec_name=result_dict.get("spec_name"),
    )
