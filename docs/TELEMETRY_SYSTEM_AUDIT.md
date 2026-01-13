# Telemetry System Audit: luthiers-toolbox

> **Version**: 1.0.0
> **Created**: 2026-01-12
> **Scope**: Smart Guitar → ToolBox Telemetry Ingestion v1
> **Status**: Active

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Module Structure](#3-module-structure)
4. [Schema Definition](#4-schema-definition)
5. [API Endpoints](#5-api-endpoints)
6. [Validation Engine](#6-validation-engine)
7. [Storage System](#7-storage-system)
8. [Boundary Enforcement](#8-boundary-enforcement)
9. [Test Coverage](#9-test-coverage)
10. [Configuration](#10-configuration)

---

## 1. Executive Summary

### Purpose

The telemetry system in `luthiers-toolbox` receives hardware/manufacturing telemetry from Smart Guitar devices. It enforces a strict **manufacturing-only boundary** that:

- **ALLOWS**: Utilization, hardware performance, environment, lifecycle data
- **BLOCKS**: Player identity, pedagogy, teaching content, musical recordings

### Key Statistics

| Metric | Value |
|--------|-------|
| API Endpoints | 8 |
| Pydantic Models | 6 |
| Forbidden Fields | 22 |
| Allowed Categories | 4 |
| Allowed Units | 14 |
| Test Cases | 50+ |

### Data Flow

```
┌─────────────────┐     POST /api/telemetry/ingest     ┌──────────────────────┐
│  Smart Guitar   │ ─────────────────────────────────► │   luthiers-toolbox   │
│  (Device)       │                                    │                      │
└─────────────────┘                                    │  ┌────────────────┐  │
                                                       │  │   Validator    │  │
     Payload:                                          │  │  (Gate Check)  │  │
     - instrument_id                                   │  └───────┬────────┘  │
     - manufacturing_batch_id                          │          │           │
     - telemetry_category                              │          ▼           │
     - metrics (hardware only)                         │  ┌────────────────┐  │
                                                       │  │     Store      │  │
     BLOCKED:                                          │  │ (Date-Partitioned)│
     - player_id ❌                                    │  └────────────────┘  │
     - lesson_id ❌                                    │                      │
     - accuracy ❌                                     └──────────────────────┘
     - midi/audio ❌
```

---

## 2. Architecture Overview

### 2.1 Component Diagram

```
services/api/app/smart_guitar_telemetry/
├── __init__.py          # Public API exports
├── schemas.py           # Pydantic models (mirrors JSON Schema)
├── validator.py         # Gate enforcement logic
├── store.py             # Date-partitioned storage
└── api.py               # FastAPI router (8 endpoints)

contracts/
├── smart_guitar_toolbox_telemetry_v1.schema.json    # JSON Schema (source of truth)
├── smart_guitar_toolbox_telemetry_v1.schema.sha256  # Checksum
└── fixtures/
    ├── telemetry_valid_hardware_performance.json    # Valid example
    ├── telemetry_invalid_pedagogy_leak.json         # MUST be rejected
    └── telemetry_invalid_metric_key_smuggle.json    # MUST be rejected

services/api/tests/
├── test_smart_guitar_telemetry_gate.py    # Boundary enforcement tests
├── test_smart_guitar_telemetry_api.py     # API integration tests
└── test_smart_guitar_telemetry_store.py   # Storage tests
```

### 2.2 Router Registration

**Location**: `services/api/app/main.py:1135-1138`

```python
from .smart_guitar_telemetry import telemetry_router as sg_telemetry_router
app.include_router(sg_telemetry_router, prefix="/api/telemetry", tags=["Smart Guitar", "Telemetry"])
```

---

## 3. Module Structure

### 3.1 Public Exports (`__init__.py`)

```python
# Schemas
TelemetryPayload        # Main payload model
MetricValue             # Individual metric measurement
TelemetryCategory       # Enum: utilization, hardware_performance, environment, lifecycle
MetricUnit              # Enum: 14 allowed units
AggregationType         # Enum: sum, avg, max, min, bucket

# Validation
validate_telemetry()           # Dict → TelemetryValidationResult
validate_telemetry_json()      # JSON string → TelemetryValidationResult
TelemetryValidationResult      # Dataclass with valid, errors, warnings, payload
FORBIDDEN_FIELDS               # frozenset of 22 blocked field names

# Storage
TelemetryStore                 # Date-partitioned store class
StoredTelemetry                # Stored record wrapper
store_telemetry()              # Store a validated payload
get_telemetry()                # Retrieve by ID
list_telemetry()               # List with filters
count_telemetry()              # Count with filters
get_instrument_summary()       # Instrument statistics

# API
telemetry_router               # FastAPI router
```

---

## 4. Schema Definition

### 4.1 Required Fields (7)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `schema_id` | string | `const: "smart_guitar_toolbox_telemetry"` | Fixed identifier |
| `schema_version` | string | `const: "v1"` | Fixed version |
| `emitted_at_utc` | datetime | ISO 8601 format | When payload was emitted |
| `instrument_id` | string | 6-128 chars, pattern: `^[A-Za-z0-9][A-Za-z0-9._:-]{4,126}[A-Za-z0-9]$` | Physical unit ID (non-player) |
| `manufacturing_batch_id` | string | 4-128 chars | ToolBox batch/build ID |
| `telemetry_category` | enum | `utilization`, `hardware_performance`, `environment`, `lifecycle` | Manufacturing category |
| `metrics` | object | min 1 property, keys: `^[a-z][a-z0-9_]{1,63}$` | Metric measurements |

### 4.2 Optional Fields (3)

| Field | Type | Description |
|-------|------|-------------|
| `design_revision_id` | string | Design revision (manufacturing correlation) |
| `hardware_sku` | string | Hardware SKU (manufacturing correlation) |
| `component_lot_id` | string | Component lot ID (manufacturing correlation) |

### 4.3 Metric Value Structure

```python
class MetricValue(BaseModel):
    value: float          # Required, range: ±1.0e308
    unit: MetricUnit      # Required, 14 allowed values
    aggregation: AggregationType  # Required: sum, avg, max, min, bucket
    bucket_label: Optional[str]   # Required only if aggregation=bucket
```

### 4.4 Allowed Units (14)

```python
class MetricUnit(str, Enum):
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
```

### 4.5 Telemetry Categories (4)

| Category | Purpose | Example Metrics |
|----------|---------|-----------------|
| `utilization` | Usage patterns | `power_on_hours`, `session_count` |
| `hardware_performance` | Hardware health | `battery_voltage`, `cpu_temp`, `adc_noise_db` |
| `environment` | Operating conditions | `temp_c`, `humidity_bucket` |
| `lifecycle` | Wear and maintenance | `fret_wear_events`, `string_break_count` |

---

## 5. API Endpoints

### 5.1 Endpoint Summary

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/telemetry/ingest` | Ingest telemetry payload |
| `POST` | `/api/telemetry/validate` | Dry-run validation |
| `GET` | `/api/telemetry/contract` | Get contract info |
| `GET` | `/api/telemetry/health` | Health check |
| `GET` | `/api/telemetry/records/{id}` | Get record by ID |
| `GET` | `/api/telemetry/records` | List records with filters |
| `GET` | `/api/telemetry/instruments/{id}/summary` | Instrument summary |
| `GET` | `/api/telemetry/stats` | Overall statistics |

### 5.2 Ingest Endpoint Details

**`POST /api/telemetry/ingest`**

```python
# Request: Dict[str, Any] (raw JSON payload)
# Response 200: TelemetryIngestResponse
{
    "accepted": true,
    "telemetry_id": "telem_20260112235500_000001",
    "instrument_id": "sg-0001-alpha",
    "category": "hardware_performance",
    "metric_count": 5,
    "received_at_utc": "2026-01-12T23:55:00Z",
    "warnings": []
}

# Response 422: TelemetryRejectResponse (forbidden fields detected)
{
    "accepted": false,
    "errors": ["Forbidden field 'player_id' at 'player_id': Player/pedagogy data must not cross the boundary"],
    "contract_version": "v1",
    "forbidden_fields_detected": ["player_id"]
}
```

### 5.3 Contract Info Endpoint

**`GET /api/telemetry/contract`**

```json
{
    "contract_name": "Smart Guitar -> ToolBox Telemetry Contract",
    "contract_version": "v1",
    "allowed_categories": ["utilization", "hardware_performance", "environment", "lifecycle"],
    "forbidden_fields": ["account_id", "accuracy", "audio", "coach_feedback", "curriculum_id", ...],
    "schema_url": "/contracts/smart_guitar_toolbox_telemetry_v1.schema.json"
}
```

---

## 6. Validation Engine

### 6.1 Validation Steps

**Location**: `services/api/app/smart_guitar_telemetry/validator.py`

```python
def validate_telemetry(payload_dict: Dict[str, Any]) -> TelemetryValidationResult:
    # 1) Check for forbidden fields FIRST (hard block)
    forbidden_errors = _check_forbidden_fields(payload_dict)

    # 2) Parse with Pydantic (validates schema)
    payload = TelemetryPayload.model_validate(payload_dict)

    # 3) Validate telemetry category
    # 4) Validate metrics have at least one entry
    # 5) Hard-block forbidden terms in metric keys (prevents smuggling)
    # 6) Warning for suspiciously teaching-like metric names
```

### 6.2 Forbidden Fields (22)

**Location**: `validator.py:25-50`

```python
FORBIDDEN_FIELDS: Set[str] = frozenset({
    # Player identity
    "player_id", "account_id", "user_id", "email", "username",

    # Pedagogy / Teaching
    "lesson_id", "curriculum_id", "practice_session_id",
    "skill_level", "accuracy", "timing",

    # Musical content
    "midi", "audio", "recording_url",

    # Coaching
    "coach_feedback", "prompt_trace", "lesson_progress",
    "score", "grade", "evaluation",
})
```

### 6.3 Recursive Field Checking

The validator recursively checks nested objects for forbidden fields:

```python
def _check_forbidden_fields(data: Dict[str, Any], path: str = "") -> List[str]:
    for key, value in data.items():
        if key.lower() in FORBIDDEN_FIELDS:
            errors.append(f"Forbidden field '{key}' at '{path}'...")

        # Recurse into nested objects
        if isinstance(value, dict):
            errors.extend(_check_forbidden_fields(value, current_path))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    errors.extend(_check_forbidden_fields(item, f"{current_path}[{i}]"))
```

### 6.4 Metric Key Smuggling Detection

Prevents hiding forbidden terms in metric keys like `player_id_hash`:

```python
# Splits metric key into segments and checks for forbidden term matches
for metric_key in payload.metrics.keys():
    segments = metric_key_lower.split("_")
    for forbidden in FORBIDDEN_FIELDS:
        forbidden_parts = forbidden.split("_")
        # Check if forbidden_parts match as complete segments
        if segments[i:i + len(forbidden_parts)] == forbidden_parts:
            result.add_error(f"Forbidden metric key '{metric_key}'...")
```

### 6.5 Suspicious Pattern Warnings

Soft warnings for potentially problematic metric names (not hard-blocked):

```python
suspicious_patterns = ["practice", "skill", "progress", "performance_score"]
for metric_name in payload.metrics.keys():
    for pattern in suspicious_patterns:
        if pattern in metric_name.lower():
            result.add_warning(f"Suspicious metric name '{metric_name}'...")
```

---

## 7. Storage System

### 7.1 Storage Structure

**Location**: `services/api/app/smart_guitar_telemetry/store.py`

```
{SMART_GUITAR_TELEMETRY_DIR}/
├── 2026-01-10/
│   ├── telem_20260110170600_000001.json
│   └── telem_20260110180000_000002.json
├── 2026-01-11/
│   └── telem_20260111090000_000003.json
└── _index.json
```

### 7.2 Telemetry ID Format

```python
def generate_telemetry_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"telem_{ts}_{counter:06d}"

# Example: telem_20260112235500_000001
```

### 7.3 StoredTelemetry Record

```python
class StoredTelemetry:
    telemetry_id: str              # Unique ID
    payload: TelemetryPayload      # Validated payload
    received_at_utc: datetime      # Server receive timestamp
    partition: str                 # Date partition (YYYY-MM-DD)
    warnings: List[str]            # Any validation warnings
```

### 7.4 Index Metadata

The `_index.json` file stores lightweight metadata for efficient queries:

```python
{
    "telem_20260110170600_000001": {
        "telemetry_id": "telem_20260110170600_000001",
        "received_at_utc": "2026-01-10T17:06:00Z",
        "partition": "2026-01-10",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "hardware_performance",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "metric_count": 5,
        "metric_names": ["uptime_hours", "boot_count", "adc_noise_db", ...],
        "design_revision_id": null,
        "hardware_sku": null,
        "has_warnings": false
    }
}
```

### 7.5 Query Filters

```python
def list_telemetry(
    limit: int = 50,
    offset: int = 0,
    instrument_id: Optional[str] = None,
    manufacturing_batch_id: Optional[str] = None,
    category: Optional[TelemetryCategory] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> List[StoredTelemetry]
```

---

## 8. Boundary Enforcement

### 8.1 Test Fixtures

**Valid Fixture** (`telemetry_valid_hardware_performance.json`):

```json
{
  "schema_id": "smart_guitar_toolbox_telemetry",
  "schema_version": "v1",
  "emitted_at_utc": "2026-01-10T17:06:00Z",
  "instrument_id": "sg-0001-alpha",
  "manufacturing_batch_id": "tb-batch-2026-01-10-01",
  "telemetry_category": "hardware_performance",
  "metrics": {
    "uptime_hours": { "value": 12.5, "unit": "hours", "aggregation": "sum" },
    "boot_count": { "value": 4, "unit": "count", "aggregation": "sum" },
    "adc_noise_db": { "value": -72.4, "unit": "db", "aggregation": "avg" },
    "battery_voltage_v": { "value": 3.92, "unit": "volts", "aggregation": "avg" },
    "temp_c": { "value": 31.2, "unit": "celsius", "aggregation": "max" }
  }
}
```

**Invalid Fixture - Pedagogy Leak** (`telemetry_invalid_pedagogy_leak.json`):

```json
{
  "$comment": "INVALID - This payload must be REJECTED",
  "schema_id": "smart_guitar_toolbox_telemetry",
  "schema_version": "v1",
  "telemetry_category": "practice_usage",    // ❌ Invalid category
  "player_id": "user-12345",                 // ❌ Forbidden field
  "lesson_id": "lesson_fretting_101",        // ❌ Forbidden field
  "accuracy": 0.82,                          // ❌ Forbidden field
  "metrics": {
    "practice_minutes_total": { ... },
    "timing_accuracy_pct": { ... }           // ❌ Contains "timing"
  }
}
```

**Invalid Fixture - Metric Key Smuggling** (`telemetry_invalid_metric_key_smuggle.json`):

```json
{
  "schema_id": "smart_guitar_toolbox_telemetry",
  "telemetry_category": "utilization",
  "metrics": {
    "player_id_hash": { ... },       // ❌ Contains "player_id"
    "lesson_progress_pct": { ... },  // ❌ Contains "lesson"
    "accuracy_score_avg": { ... }    // ❌ Contains "accuracy"
  }
}
```

### 8.2 Error Messages

| Violation | Error Message |
|-----------|---------------|
| Forbidden field | `"Forbidden field 'player_id' at 'player_id': Player/pedagogy data must not cross the boundary"` |
| Metric key smuggling | `"Forbidden metric key 'player_id_hash': contains blocked term 'player_id' (pedagogy data boundary violation)"` |
| Invalid category | `"Input should be 'utilization', 'hardware_performance', 'environment' or 'lifecycle'"` |
| Invalid unit | `"Input should be 'count', 'hours', 'seconds', ..."` |
| Missing bucket_label | `"bucket_label is required when aggregation is 'bucket'"` |

---

## 9. Test Coverage

### 9.1 Test File: `test_smart_guitar_telemetry_gate.py`

**Location**: `services/api/tests/test_smart_guitar_telemetry_gate.py`

| Test Category | Count | Purpose |
|---------------|-------|---------|
| Valid Payload Tests | 5 | Verify all categories work |
| Forbidden Field Tests | 8 | Block player/pedagogy fields |
| Invalid Category Tests | 2 | Reject non-manufacturing categories |
| Schema Validation Tests | 10 | Enforce schema constraints |
| Fixture File Tests | 3 | Validate test fixtures |
| Metric Key Smuggling | 9 | Block forbidden terms in keys |
| JSON String Tests | 2 | Test JSON parsing |
| Warning Tests | 1 | Test suspicious pattern warnings |

### 9.2 Parametrized Tests

```python
@pytest.mark.parametrize("field_name", list(FORBIDDEN_FIELDS)[:10])
def test_forbidden_fields_rejected(field_name):
    """All forbidden fields are rejected at top level."""

@pytest.mark.parametrize("forbidden_term", [
    "player_id", "user_id", "account_id", "lesson_id", "accuracy", "timing",
    "midi", "audio", "score", "grade", "evaluation", "coach_feedback",
])
def test_forbidden_terms_blocked_in_metric_keys(forbidden_term):
    """All forbidden terms are blocked when used in metric keys."""
```

### 9.3 Running Tests

```bash
cd services/api
pytest tests/test_smart_guitar_telemetry_gate.py -v
pytest tests/test_smart_guitar_telemetry_api.py -v
pytest tests/test_smart_guitar_telemetry_store.py -v
```

---

## 10. Configuration

### 10.1 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SMART_GUITAR_TELEMETRY_DIR` | `services/api/data/telemetry/smart_guitar` | Storage directory |

### 10.2 Router Tags

The router is registered with tags for OpenAPI documentation:

```python
app.include_router(
    sg_telemetry_router,
    prefix="/api/telemetry",
    tags=["Smart Guitar", "Telemetry"]
)
```

### 10.3 Logging

```python
import logging
_log = logging.getLogger(__name__)

# On rejection:
_log.warning("Telemetry rejected: instrument=%s errors=%s", ...)

# On acceptance:
_log.info("Telemetry accepted: id=%s instrument=%s category=%s metrics=%d", ...)
```

---

## Appendix A: Quick Reference

### Valid Payload Template

```json
{
  "schema_id": "smart_guitar_toolbox_telemetry",
  "schema_version": "v1",
  "emitted_at_utc": "2026-01-12T23:55:00Z",
  "instrument_id": "SG-UNIT-001234",
  "manufacturing_batch_id": "TB-BATCH-2026-Q1",
  "telemetry_category": "hardware_performance",
  "metrics": {
    "metric_name": {
      "value": 123.45,
      "unit": "celsius",
      "aggregation": "avg"
    }
  }
}
```

### Forbidden Fields Quick List

```
player_id, account_id, user_id, email, username,
lesson_id, curriculum_id, practice_session_id,
skill_level, accuracy, timing,
midi, audio, recording_url,
coach_feedback, prompt_trace, lesson_progress,
score, grade, evaluation
```

### Allowed Categories

```
utilization, hardware_performance, environment, lifecycle
```

### Allowed Units

```
count, hours, seconds, milliseconds, ratio, percent,
celsius, fahrenheit, volts, amps, ohms, db, hz, bytes
```

---

## Document History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2026-01-12 | 1.0.0 | Development Team | Initial creation |

---

*This document should be updated whenever the telemetry system is modified.*
