"""
Smart Guitar -> ToolBox Telemetry Ingestion v1

This module validates and processes telemetry payloads from Smart Guitar.
Enforces the manufacturing-only boundary:
- NO player/pedagogy data
- NO teaching content
- Only instrument utilization, hardware performance, environment, lifecycle
"""

from .schemas import (
    TelemetryPayload,
    MetricValue,
    TelemetryCategory,
    MetricUnit,
    AggregationType,
)
from .validator import (
    validate_telemetry,
    validate_telemetry_json,
    TelemetryValidationResult,
    FORBIDDEN_FIELDS,
)

__all__ = [
    # Schemas
    "TelemetryPayload",
    "MetricValue",
    "TelemetryCategory",
    "MetricUnit",
    "AggregationType",
    # Validation
    "validate_telemetry",
    "validate_telemetry_json",
    "TelemetryValidationResult",
    "FORBIDDEN_FIELDS",
]
