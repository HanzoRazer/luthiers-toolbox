# services/api/app/schemas/cam_fret_slots_export.py

from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


Units = Literal["mm", "inch"]


class FretSlotMultiPostExportRequest(BaseModel):
    """
    Request model for multi-post fret-slot export.

    Steps the backend will perform:
      - Compute fret slots for a given instrument model
      - Generate DXF/SVG
      - Generate one G-code file per post-processor
      - Bundle all artifacts into a single ZIP.
    """

    model_id: str = Field(
        ...,
        description="Instrument model identifier (e.g., 'benedetto_17').",
    )
    mode: Literal["straight", "fan_fret"] = Field(
        "straight",
        description="Fret layout mode; fan-fret uses instrument's fan_fret spec.",
    )
    scale_id: Optional[str] = Field(
        None,
        description="Optional scale preset ID, if your model supports more than one.",
    )

    fret_count: int = Field(
        22,
        ge=1,
        le=36,
        description="Number of frets to generate.",
    )

    slot_depth_mm: float = Field(
        2.0,
        gt=0,
        description="Slot cutting depth (mm).",
    )
    slot_width_mm: float = Field(
        0.6,
        gt=0,
        description="Slot width (mm).",
    )

    # Post-processor IDs, e.g. ["grbl", "mach4", "linuxcnc"]
    post_ids: List[str] = Field(
        ...,
        min_items=1,
        description="List of post-processors to generate G-code for.",
    )

    target_units: Units = Field(
        "mm",
        description="Output units for DXF/G-code.",
    )

    filename_prefix: Optional[str] = Field(
        None,
        description="Optional base prefix for files inside the ZIP.",
    )
