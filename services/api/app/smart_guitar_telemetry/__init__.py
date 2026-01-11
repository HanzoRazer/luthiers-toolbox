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
from .store import (
    TelemetryStore,
    StoredTelemetry,
    store_telemetry,
    get_telemetry,
    list_telemetry,
    count_telemetry,
    get_instrument_summary,
)
from .api import router as telemetry_router

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
    # Storage
    "TelemetryStore",
    "StoredTelemetry",
    "store_telemetry",
    "get_telemetry",
    "list_telemetry",
    "count_telemetry",
    "get_instrument_summary",
    # API
    "telemetry_router",
]
