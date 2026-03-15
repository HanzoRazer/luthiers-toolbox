"""
AI-CAM Data Models (Wave 11)

Shared data structures for CAM advisor, G-code explainer, and optimizer.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class CAMAdvisory:
    """A single advisory message from the CAM advisor."""
    message: str
    severity: str  # "info", "warning", "error"
    context: Optional[Dict[str, Any]] = None

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CAMAnalysisResult:
    """Complete result from CAM operation analysis."""
    advisories: List[CAMAdvisory] = field(default_factory=list)
    recommended_changes: Dict[str, Any] = field(default_factory=dict)
    physics_results: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "advisories": [a.as_dict() for a in self.advisories],
            "recommended_changes": self.recommended_changes,
            "physics_results": self.physics_results,
        }


@dataclass
class GCodeExplanation:
    """Explanation for a single G-code line."""
    line_number: int
    raw: str
    explanation: str
    risk: Optional[str] = None  # "low", "medium", "high"

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GCodeExplainerResult:
    """Complete result from G-code explanation."""
    explanations: List[GCodeExplanation] = field(default_factory=list)
    overall_risk: str = "low"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "explanations": [e.as_dict() for e in self.explanations],
            "overall_risk": self.overall_risk,
        }
