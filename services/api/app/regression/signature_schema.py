"""
Regression Signature Schema
===========================

Base schema for regression signatures. Defines the structure for
capturing and comparing protected system outputs.

MRP-1B: Regression & Behavioral Observability Infrastructure
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ComparisonResult(Enum):
    """Result of comparing two signatures."""
    MATCH = "match"
    DRIFT = "drift"
    REGRESSION = "regression"
    BASELINE_MISSING = "baseline_missing"


@dataclass
class RegressionSignature:
    """
    Base class for regression signatures.

    A signature captures the observable output characteristics of a
    protected system run, enabling comparison against baselines.
    """
    # Identity (defaults allow subclass extension)
    artifact_id: str = ""
    system_id: str = ""

    # Versioning
    signature_version: str = "1.0.0"
    captured_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Source context
    input_hash: Optional[str] = None
    input_description: Optional[str] = None

    # Output characteristics (subclasses extend)
    dimensions: Dict[str, float] = field(default_factory=dict)
    counts: Dict[str, int] = field(default_factory=dict)
    flags: Dict[str, bool] = field(default_factory=dict)

    # Metadata
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "system_id": self.system_id,
            "artifact_id": self.artifact_id,
            "signature_version": self.signature_version,
            "captured_at": self.captured_at,
            "input_hash": self.input_hash,
            "input_description": self.input_description,
            "dimensions": self.dimensions,
            "counts": self.counts,
            "flags": self.flags,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RegressionSignature:
        """Deserialize from dictionary."""
        return cls(
            system_id=data["system_id"],
            artifact_id=data["artifact_id"],
            signature_version=data.get("signature_version", "1.0.0"),
            captured_at=data.get("captured_at", ""),
            input_hash=data.get("input_hash"),
            input_description=data.get("input_description"),
            dimensions=data.get("dimensions", {}),
            counts=data.get("counts", {}),
            flags=data.get("flags", {}),
            notes=data.get("notes"),
        )


@dataclass
class SignatureComparison:
    """
    Result of comparing two regression signatures.
    """
    result: ComparisonResult
    baseline_id: str
    current_id: str

    # Dimensional drift
    dimension_deltas: Dict[str, float] = field(default_factory=dict)
    dimension_drift_pct: Dict[str, float] = field(default_factory=dict)

    # Count changes
    count_deltas: Dict[str, int] = field(default_factory=dict)

    # Flag changes
    flag_changes: Dict[str, tuple] = field(default_factory=dict)  # (old, new)

    # Invariant violations
    invariant_violations: List[str] = field(default_factory=list)

    # Summary
    is_acceptable: bool = True
    blocking_issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "result": self.result.value,
            "baseline_id": self.baseline_id,
            "current_id": self.current_id,
            "dimension_deltas": self.dimension_deltas,
            "dimension_drift_pct": self.dimension_drift_pct,
            "count_deltas": self.count_deltas,
            "flag_changes": {k: list(v) for k, v in self.flag_changes.items()},
            "invariant_violations": self.invariant_violations,
            "is_acceptable": self.is_acceptable,
            "blocking_issues": self.blocking_issues,
            "warnings": self.warnings,
        }
