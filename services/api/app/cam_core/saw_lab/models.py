"""Saw Lab data contracts.

This module re-exports models from the cnc_production experimental module
and provides local aliases for backward compatibility.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import real models from experimental (now production-ready)
from app._experimental.cnc_production.joblog.models import (
    SawRunMeta,
    SawRunRecord,
    TelemetrySample,
    SawTelemetryRecord,
    OpType,
    RiskGrade,
)

from app._experimental.cnc_production.learn.models import (
    TelemetryIngestConfig,
    LaneMetrics,
    LaneAdjustment,
    TelemetryIngestRequest,
    TelemetryIngestResponse,
)


# Legacy dataclasses for backward compatibility
@dataclass
class SawLabCut:
    """A single cut operation within a run."""
    id: str
    name: str
    program_id: str
    status: str = "pending"
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SawLabRun:
    """Legacy run container - use SawRunRecord for new code."""
    id: str
    created_at: datetime
    cuts: List[SawLabCut] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_saw_run_record(cls, record: SawRunRecord) -> "SawLabRun":
        """Convert SawRunRecord to legacy SawLabRun."""
        return cls(
            id=record.run_id,
            created_at=record.created_at,
            cuts=[],
            metadata={
                "op_type": record.meta.op_type if record.meta else None,
                "blade_id": record.meta.blade_id if record.meta else None,
                "status": record.status,
            }
        )


# Re-export all for convenience
__all__ = [
    # Legacy
    "SawLabCut",
    "SawLabRun",
    # Production models
    "SawRunMeta",
    "SawRunRecord",
    "TelemetrySample",
    "SawTelemetryRecord",
    "OpType",
    "RiskGrade",
    # Learning models
    "TelemetryIngestConfig",
    "LaneMetrics",
    "LaneAdjustment",
    "TelemetryIngestRequest",
    "TelemetryIngestResponse",
]
