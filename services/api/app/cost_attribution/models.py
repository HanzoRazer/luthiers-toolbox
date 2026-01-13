from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional, Dict, Any

CostDimension = Literal[
    "compute_cost_hours",
    "energy_amp_hours",
    "thermal_stress_c",
    "wear_cycles",
]


@dataclass(frozen=True)
class CostFact:
    """
    Internal cost fact derived from telemetry.
    Immutable record of a single cost dimension measurement.
    """
    manufacturing_batch_id: str
    instrument_id: str
    cost_dimension: CostDimension
    value: float
    unit: str
    aggregation: str
    source_metric_key: str
    emitted_at_utc: datetime
    telemetry_category: str
    telemetry_schema_version: str = "v1"
    meta: Optional[Dict[str, Any]] = None
