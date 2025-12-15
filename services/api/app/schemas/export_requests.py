from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, Field


class ManufacturingPlanExportRequest(BaseModel):
    pattern_id: str
    guitars: int = Field(1, ge=1)
    tile_length_mm: float = Field(8.0, gt=0)
    scrap_factor: float = Field(0.12, ge=0)
    record_joblog: bool = False


class SawBatchGcodeExportRequest(BaseModel):
    batch_op: Dict[str, Any] = Field(
        ..., description="SawSliceBatchOpCircle dict or DXF batch op payload"
    )
