"""
Pydantic schemas for Smart Guitar -> ToolBox Telemetry v1

These schemas mirror the JSON Schema at:
contracts/smart_guitar_toolbox_telemetry_v1.schema.json
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class TelemetryCategory(str, Enum):
    """Allowed telemetry categories (manufacturing-only)."""
    UTILIZATION = "utilization"
    HARDWARE_PERFORMANCE = "hardware_performance"
    ENVIRONMENT = "environment"
    LIFECYCLE = "lifecycle"


class MetricUnit(str, Enum):
    """Allowed metric units."""
    COUNT = "count"
    HOURS = "hours"
    SECONDS = "seconds"
    MILLISECONDS = "milliseconds"
    RATIO = "ratio"
    PERCENT = "percent"
    CELSIUS = "celsius"
    FAHRENHEIT = "fahrenheit"
    VOLTS = "volts"
    AMPS = "amps"
    OHMS = "ohms"
    DB = "db"
    HZ = "hz"
    BYTES = "bytes"


class AggregationType(str, Enum):
    """How metrics are aggregated upstream."""
    SUM = "sum"
    AVG = "avg"
    MAX = "max"
    MIN = "min"
    BUCKET = "bucket"


class MetricValue(BaseModel):
    """A single metric measurement with aggregation metadata."""
    value: float = Field(
        ...,
        description="Numeric metric value. Must be aggregatable.",
        ge=-1.0e308,
        le=1.0e308,
    )
    unit: MetricUnit = Field(..., description="Unit label for the metric.")
    aggregation: AggregationType = Field(
        ...,
        description="How this metric is aggregated upstream.",
    )
    bucket_label: Optional[str] = Field(
        None,
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9 _./:-]{0,62}[A-Za-z0-9]$",
        description="Only for aggregation=bucket. Human-readable bucket name.",
    )

    @model_validator(mode="after")
    def validate_bucket_label(self) -> "MetricValue":
        """Enforce bucket_label required for bucket aggregation, forbidden otherwise."""
        if self.aggregation == AggregationType.BUCKET:
            if not self.bucket_label:
                raise ValueError("bucket_label is required when aggregation is 'bucket'")
        else:
            if self.bucket_label is not None:
                raise ValueError("bucket_label is only allowed when aggregation is 'bucket'")
        return self

    model_config = {"extra": "forbid"}


class TelemetryPayload(BaseModel):
    """
    Smart Guitar -> ToolBox telemetry payload.

    This is the ONLY allowed data exchange from Smart Guitar to ToolBox.
    Purpose: Manufacturing intelligence and lifecycle optimization.
    """
    schema_id: str = Field(
        ...,
        pattern=r"^smart_guitar_toolbox_telemetry$",
        description="Must be 'smart_guitar_toolbox_telemetry'",
    )
    schema_version: str = Field(
        ...,
        pattern=r"^v1$",
        description="Must be 'v1'",
    )
    emitted_at_utc: datetime = Field(
        ...,
        description="UTC timestamp when payload was emitted.",
    )
    instrument_id: str = Field(
        ...,
        min_length=6,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{4,126}[A-Za-z0-9]$",
        description="Smart Guitar physical unit identifier (non-player).",
    )
    manufacturing_batch_id: str = Field(
        ...,
        min_length=4,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,126}[A-Za-z0-9]$",
        description="ToolBox manufacturing batch/build identifier.",
    )
    telemetry_category: TelemetryCategory = Field(
        ...,
        description="High-level category for manufacturing intelligence.",
    )
    metrics: Dict[str, MetricValue] = Field(
        ...,
        min_length=1,
        description="Map of metric_name -> metric data. Values must be numeric + aggregatable.",
    )

    # Optional manufacturing correlation fields
    design_revision_id: Optional[str] = Field(
        None,
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,126}[A-Za-z0-9]$",
        description="Optional design revision identifier (manufacturing correlation only).",
    )
    hardware_sku: Optional[str] = Field(
        None,
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,126}[A-Za-z0-9]$",
        description="Optional hardware SKU (manufacturing correlation only).",
    )
    component_lot_id: Optional[str] = Field(
        None,
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,126}[A-Za-z0-9]$",
        description="Optional component lot identifier (manufacturing correlation only).",
    )

    @field_validator("metrics")
    @classmethod
    def validate_metric_names(cls, v: Dict[str, MetricValue]) -> Dict[str, MetricValue]:
        """Validate metric names match the allowed pattern."""
        import re
        pattern = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
        for name in v.keys():
            if not pattern.match(name):
                raise ValueError(
                    f"Invalid metric name '{name}': must match pattern ^[a-z][a-z0-9_]{{1,63}}$"
                )
        return v

    model_config = {"extra": "forbid"}
