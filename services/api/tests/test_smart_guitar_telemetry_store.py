"""
Unit tests for Smart Guitar Telemetry Store.

Tests the date-partitioned, append-only storage:
- Store and retrieve telemetry records
- List and filter records
- Count records
- Instrument summaries
- Index operations
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from app.smart_guitar_telemetry.schemas import (
    TelemetryPayload,
    TelemetryCategory,
    MetricValue,
    MetricUnit,
    AggregationType,
)
from app.smart_guitar_telemetry.store import (
    TelemetryStore,
    StoredTelemetry,
    generate_telemetry_id,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_store_dir():
    """Create a temporary directory for store testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def store(temp_store_dir):
    """Create a TelemetryStore with temporary directory."""
    return TelemetryStore(root_dir=temp_store_dir)


@pytest.fixture
def sample_payload() -> TelemetryPayload:
    """Create a sample valid telemetry payload."""
    return TelemetryPayload(
        schema_id="smart_guitar_toolbox_telemetry",
        schema_version="v1",
        emitted_at_utc=datetime(2026, 1, 10, 17, 0, 0, tzinfo=timezone.utc),
        instrument_id="sg-test-0001",
        manufacturing_batch_id="tb-batch-test-01",
        telemetry_category=TelemetryCategory.HARDWARE_PERFORMANCE,
        metrics={
            "uptime_hours": MetricValue(
                value=12.5,
                unit=MetricUnit.HOURS,
                aggregation=AggregationType.SUM,
            ),
            "boot_count": MetricValue(
                value=4,
                unit=MetricUnit.COUNT,
                aggregation=AggregationType.SUM,
            ),
        },
    )


def make_payload(
    instrument_id: str,
    batch_id: str,
    category: TelemetryCategory,
    **kwargs,
) -> TelemetryPayload:
    """Helper to create test payloads with specified attributes."""
    return TelemetryPayload(
        schema_id="smart_guitar_toolbox_telemetry",
        schema_version="v1",
        emitted_at_utc=kwargs.get("emitted_at", datetime.now(timezone.utc)),
        instrument_id=instrument_id,
        manufacturing_batch_id=batch_id,
        telemetry_category=category,
        design_revision_id=kwargs.get("design_revision_id"),
        hardware_sku=kwargs.get("hardware_sku"),
        metrics={
            "test_metric": MetricValue(
                value=1.0,
                unit=MetricUnit.COUNT,
                aggregation=AggregationType.SUM,
            ),
        },
    )


# =============================================================================
# Telemetry ID Generation Tests
# =============================================================================


def test_generate_telemetry_id_format():
    """Telemetry IDs follow expected format."""
    tid = generate_telemetry_id()
    assert tid.startswith("telem_")
    parts = tid.split("_")
    assert len(parts) == 3
    assert len(parts[1]) == 14  # YYYYMMDDHHMMSS
    assert len(parts[2]) == 6   # 6-digit counter


def test_generate_telemetry_id_unique():
    """Telemetry IDs are unique."""
    ids = [generate_telemetry_id() for _ in range(100)]
    assert len(set(ids)) == 100


# =============================================================================
# Store Put Tests
# =============================================================================


def test_store_put_returns_stored_telemetry(store, sample_payload):
    """Store.put() returns a StoredTelemetry record."""
    result = store.put(sample_payload)

    assert isinstance(result, StoredTelemetry)
    assert result.telemetry_id.startswith("telem_")
    assert result.payload == sample_payload
    assert result.partition == datetime.now(timezone.utc).strftime("%Y-%m-%d")
    assert result.warnings == []


def test_store_put_with_warnings(store, sample_payload):
    """Store.put() preserves warnings."""
    warnings = ["Suspicious metric name: practice_hours"]
    result = store.put(sample_payload, warnings=warnings)

    assert result.warnings == warnings


def test_store_put_creates_partition_dir(store, sample_payload, temp_store_dir):
    """Store.put() creates date partition directory."""
    store.put(sample_payload)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    partition_dir = Path(temp_store_dir) / today
    assert partition_dir.exists()
    assert partition_dir.is_dir()


def test_store_put_creates_json_file(store, sample_payload, temp_store_dir):
    """Store.put() creates JSON file in partition."""
    result = store.put(sample_payload)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    json_path = Path(temp_store_dir) / today / f"{result.telemetry_id}.json"
    assert json_path.exists()

    # Verify JSON content
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["telemetry_id"] == result.telemetry_id
    assert data["payload"]["instrument_id"] == "sg-test-0001"


def test_store_put_updates_index(store, sample_payload, temp_store_dir):
    """Store.put() updates the global index."""
    result = store.put(sample_payload)

    index_path = Path(temp_store_dir) / "_index.json"
    assert index_path.exists()

    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert result.telemetry_id in index
    assert index[result.telemetry_id]["instrument_id"] == "sg-test-0001"


# =============================================================================
# Store Get Tests
# =============================================================================


def test_store_get_existing_record(store, sample_payload):
    """Store.get() retrieves existing record."""
    stored = store.put(sample_payload)

    retrieved = store.get(stored.telemetry_id)

    assert retrieved is not None
    assert retrieved.telemetry_id == stored.telemetry_id
    assert retrieved.payload.instrument_id == sample_payload.instrument_id


def test_store_get_nonexistent_returns_none(store):
    """Store.get() returns None for nonexistent ID."""
    result = store.get("telem_nonexistent_000000")
    assert result is None


def test_store_get_preserves_all_fields(store, sample_payload):
    """Store.get() preserves all payload fields."""
    warnings = ["Test warning"]
    stored = store.put(sample_payload, warnings=warnings)

    retrieved = store.get(stored.telemetry_id)

    assert retrieved.payload.instrument_id == sample_payload.instrument_id
    assert retrieved.payload.manufacturing_batch_id == sample_payload.manufacturing_batch_id
    assert retrieved.payload.telemetry_category == sample_payload.telemetry_category
    assert len(retrieved.payload.metrics) == 2
    assert retrieved.warnings == warnings


# =============================================================================
# Store List Tests
# =============================================================================


def test_store_list_empty(store):
    """Store.list_telemetry() returns empty list for empty store."""
    result = store.list_telemetry()
    assert result == []


def test_store_list_returns_all(store):
    """Store.list_telemetry() returns all records."""
    payloads = [
        make_payload("sg-001", "batch-01", TelemetryCategory.UTILIZATION),
        make_payload("sg-002", "batch-01", TelemetryCategory.HARDWARE_PERFORMANCE),
        make_payload("sg-003", "batch-02", TelemetryCategory.ENVIRONMENT),
    ]
    for p in payloads:
        store.put(p)

    result = store.list_telemetry()
    assert len(result) == 3


def test_store_list_filter_by_instrument(store):
    """Store.list_telemetry() filters by instrument_id."""
    store.put(make_payload("sg-001", "batch-01", TelemetryCategory.UTILIZATION))
    store.put(make_payload("sg-001", "batch-01", TelemetryCategory.HARDWARE_PERFORMANCE))
    store.put(make_payload("sg-002", "batch-01", TelemetryCategory.UTILIZATION))

    result = store.list_telemetry(instrument_id="sg-001")
    assert len(result) == 2
    assert all(r.payload.instrument_id == "sg-001" for r in result)


def test_store_list_filter_by_batch(store):
    """Store.list_telemetry() filters by manufacturing_batch_id."""
    store.put(make_payload("sg-001", "batch-01", TelemetryCategory.UTILIZATION))
    store.put(make_payload("sg-002", "batch-01", TelemetryCategory.UTILIZATION))
    store.put(make_payload("sg-003", "batch-02", TelemetryCategory.UTILIZATION))

    result = store.list_telemetry(manufacturing_batch_id="batch-01")
    assert len(result) == 2
    assert all(r.payload.manufacturing_batch_id == "batch-01" for r in result)


def test_store_list_filter_by_category(store):
    """Store.list_telemetry() filters by category."""
    store.put(make_payload("sg-001", "batch-01", TelemetryCategory.UTILIZATION))
    store.put(make_payload("sg-002", "batch-01", TelemetryCategory.HARDWARE_PERFORMANCE))
    store.put(make_payload("sg-003", "batch-01", TelemetryCategory.UTILIZATION))

    result = store.list_telemetry(category=TelemetryCategory.UTILIZATION)
    assert len(result) == 2
    assert all(r.payload.telemetry_category == TelemetryCategory.UTILIZATION for r in result)


def test_store_list_pagination(store):
    """Store.list_telemetry() supports pagination."""
    for i in range(10):
        store.put(make_payload(f"sg-{i:03d}", "batch-01", TelemetryCategory.UTILIZATION))

    # Get first page
    page1 = store.list_telemetry(limit=3, offset=0)
    assert len(page1) == 3

    # Get second page
    page2 = store.list_telemetry(limit=3, offset=3)
    assert len(page2) == 3

    # Ensure different records
    page1_ids = {r.telemetry_id for r in page1}
    page2_ids = {r.telemetry_id for r in page2}
    assert page1_ids.isdisjoint(page2_ids)


def test_store_list_combined_filters(store):
    """Store.list_telemetry() supports combined filters."""
    store.put(make_payload("sg-001", "batch-01", TelemetryCategory.UTILIZATION))
    store.put(make_payload("sg-001", "batch-01", TelemetryCategory.HARDWARE_PERFORMANCE))
    store.put(make_payload("sg-001", "batch-02", TelemetryCategory.UTILIZATION))
    store.put(make_payload("sg-002", "batch-01", TelemetryCategory.UTILIZATION))

    result = store.list_telemetry(
        instrument_id="sg-001",
        manufacturing_batch_id="batch-01",
    )
    assert len(result) == 2


# =============================================================================
# Store Count Tests
# =============================================================================


def test_store_count_empty(store):
    """Store.count() returns 0 for empty store."""
    assert store.count() == 0


def test_store_count_all(store):
    """Store.count() returns total record count."""
    for i in range(5):
        store.put(make_payload(f"sg-count-{i:04d}", "batch-01", TelemetryCategory.UTILIZATION))

    assert store.count() == 5


def test_store_count_with_filters(store):
    """Store.count() respects filters."""
    store.put(make_payload("sg-001", "batch-01", TelemetryCategory.UTILIZATION))
    store.put(make_payload("sg-001", "batch-01", TelemetryCategory.HARDWARE_PERFORMANCE))
    store.put(make_payload("sg-002", "batch-01", TelemetryCategory.UTILIZATION))

    assert store.count(instrument_id="sg-001") == 2
    assert store.count(category=TelemetryCategory.UTILIZATION) == 2
    assert store.count(instrument_id="sg-001", category=TelemetryCategory.UTILIZATION) == 1


# =============================================================================
# Instrument Summary Tests
# =============================================================================


def test_store_instrument_summary_empty(store):
    """Store.get_instrument_summary() returns empty summary for unknown instrument."""
    summary = store.get_instrument_summary("sg-unknown")

    assert summary["instrument_id"] == "sg-unknown"
    assert summary["total_records"] == 0
    assert summary["categories"] == {}
    assert summary["first_seen_utc"] is None
    assert summary["last_seen_utc"] is None


def test_store_instrument_summary_with_records(store):
    """Store.get_instrument_summary() returns correct statistics."""
    store.put(make_payload("sg-001", "batch-01", TelemetryCategory.UTILIZATION))
    store.put(make_payload("sg-001", "batch-01", TelemetryCategory.HARDWARE_PERFORMANCE))
    store.put(make_payload("sg-001", "batch-02", TelemetryCategory.UTILIZATION))
    store.put(make_payload("sg-002", "batch-01", TelemetryCategory.UTILIZATION))

    summary = store.get_instrument_summary("sg-001")

    assert summary["instrument_id"] == "sg-001"
    assert summary["total_records"] == 3
    assert summary["categories"]["utilization"] == 2
    assert summary["categories"]["hardware_performance"] == 1
    assert "batch-01" in summary["batches"]
    assert "batch-02" in summary["batches"]
    assert summary["first_seen_utc"] is not None
    assert summary["last_seen_utc"] is not None


# =============================================================================
# Index Rebuild Tests
# =============================================================================


def test_store_rebuild_index(store, temp_store_dir):
    """Store.rebuild_index() reconstructs index from files."""
    # Store some records
    store.put(make_payload("sg-001", "batch-01", TelemetryCategory.UTILIZATION))
    store.put(make_payload("sg-002", "batch-01", TelemetryCategory.HARDWARE_PERFORMANCE))

    # Delete index
    index_path = Path(temp_store_dir) / "_index.json"
    index_path.unlink()

    # Rebuild
    count = store.rebuild_index()

    assert count == 2
    assert index_path.exists()

    # Verify we can still list
    result = store.list_telemetry()
    assert len(result) == 2


# =============================================================================
# StoredTelemetry Serialization Tests
# =============================================================================


def test_stored_telemetry_to_dict(sample_payload):
    """StoredTelemetry.to_dict() produces valid JSON-serializable dict."""
    stored = StoredTelemetry(
        telemetry_id="telem_20260110170000_000001",
        payload=sample_payload,
        received_at_utc=datetime(2026, 1, 10, 17, 0, 0, tzinfo=timezone.utc),
        partition="2026-01-10",
        warnings=["Test warning"],
    )

    data = stored.to_dict()

    assert data["telemetry_id"] == "telem_20260110170000_000001"
    assert data["partition"] == "2026-01-10"
    assert data["warnings"] == ["Test warning"]
    assert "payload" in data

    # Verify JSON serializable
    json_str = json.dumps(data)
    assert json_str


def test_stored_telemetry_from_dict(sample_payload):
    """StoredTelemetry.from_dict() reconstructs record from dict."""
    original = StoredTelemetry(
        telemetry_id="telem_20260110170000_000001",
        payload=sample_payload,
        received_at_utc=datetime(2026, 1, 10, 17, 0, 0, tzinfo=timezone.utc),
        partition="2026-01-10",
        warnings=["Test warning"],
    )

    data = original.to_dict()
    restored = StoredTelemetry.from_dict(data)

    assert restored.telemetry_id == original.telemetry_id
    assert restored.partition == original.partition
    assert restored.warnings == original.warnings
    assert restored.payload.instrument_id == original.payload.instrument_id


# =============================================================================
# Edge Cases
# =============================================================================


def test_store_concurrent_writes(store):
    """Store handles multiple sequential writes correctly."""
    # Simulate rapid writes
    for i in range(20):
        store.put(make_payload(f"sg-{i:03d}", "batch-01", TelemetryCategory.UTILIZATION))

    assert store.count() == 20


def test_store_special_characters_in_ids(store):
    """Store handles special characters in instrument/batch IDs."""
    payload = make_payload(
        "sg-special_test.v2",
        "batch-2026.01.10-rev-a",
        TelemetryCategory.UTILIZATION,
    )
    stored = store.put(payload)
    retrieved = store.get(stored.telemetry_id)

    assert retrieved is not None
    assert retrieved.payload.instrument_id == "sg-special_test.v2"
    assert retrieved.payload.manufacturing_batch_id == "batch-2026.01.10-rev-a"
