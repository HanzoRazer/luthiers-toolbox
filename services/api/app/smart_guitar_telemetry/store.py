"""
Smart Guitar Telemetry Store - Date-Partitioned, Append-Only

Stores validated telemetry payloads from Smart Guitar devices.
Uses date-partitioned file storage for efficient time-range queries.

Storage Structure:
    {root}/
    ├── 2026-01-10/
    │   ├── telem_20260110170600_000001.json
    │   └── telem_20260110180000_000002.json
    ├── 2026-01-11/
    │   └── telem_20260111090000_000003.json
    └── _index.json
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .schemas import TelemetryPayload, TelemetryCategory

# =============================================================================
# Configuration
# =============================================================================

STORE_ROOT_DEFAULT = "services/api/data/telemetry/smart_guitar"

# Thread lock for index operations
_INDEX_LOCK = threading.Lock()

# Global counter for telemetry IDs (thread-safe)
_TELEMETRY_COUNTER = 0
_COUNTER_LOCK = threading.Lock()


def _get_store_root() -> str:
    """Get the store root from environment or default."""
    return os.getenv("SMART_GUITAR_TELEMETRY_DIR", STORE_ROOT_DEFAULT)


# =============================================================================
# Telemetry ID Generation
# =============================================================================


def generate_telemetry_id() -> str:
    """Generate a unique telemetry ID."""
    global _TELEMETRY_COUNTER
    with _COUNTER_LOCK:
        _TELEMETRY_COUNTER += 1
        counter = _TELEMETRY_COUNTER
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"telem_{ts}_{counter:06d}"


# =============================================================================
# Stored Telemetry Record
# =============================================================================


class StoredTelemetry:
    """A telemetry record as stored in the database."""

    def __init__(
        self,
        telemetry_id: str,
        payload: TelemetryPayload,
        received_at_utc: datetime,
        partition: str,
        warnings: Optional[List[str]] = None,
    ):
        self.telemetry_id = telemetry_id
        self.payload = payload
        self.received_at_utc = received_at_utc
        self.partition = partition
        self.warnings = warnings or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "telemetry_id": self.telemetry_id,
            "received_at_utc": self.received_at_utc.isoformat(),
            "partition": self.partition,
            "warnings": self.warnings,
            "payload": self.payload.model_dump(mode="json"),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StoredTelemetry":
        """Create from dictionary."""
        return cls(
            telemetry_id=data["telemetry_id"],
            payload=TelemetryPayload.model_validate(data["payload"]),
            received_at_utc=datetime.fromisoformat(data["received_at_utc"].replace("Z", "+00:00")),
            partition=data["partition"],
            warnings=data.get("warnings", []),
        )


# =============================================================================
# Helper Functions
# =============================================================================


def _read_json_file(path: Path) -> Dict[str, Any]:
    """Read a JSON file, returning empty dict if not found."""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_json_file(path: Path, data: Any) -> None:
    """Atomically write a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        os.replace(tmp, path)
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise


# =============================================================================
# Telemetry Store
# =============================================================================


class TelemetryStore:
    """
    Date-partitioned, append-only telemetry store.

    Thread-safe for concurrent writes.
    """

    def __init__(self, root_dir: Optional[str] = None):
        """
        Initialize the store.

        Args:
            root_dir: Root directory for storage. Defaults to SMART_GUITAR_TELEMETRY_DIR env var.
        """
        self.root = Path(root_dir or _get_store_root()).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._index_path = self.root / "_index.json"

    def _date_partition(self, dt: datetime) -> str:
        """Get date partition string from datetime."""
        return dt.strftime("%Y-%m-%d")

    def _path_for(self, telemetry_id: str, partition: str) -> Path:
        """Get the file path for a telemetry record."""
        return self.root / partition / f"{telemetry_id}.json"

    def _read_index(self) -> Dict[str, Dict[str, Any]]:
        """Read the global index file."""
        with _INDEX_LOCK:
            return _read_json_file(self._index_path)

    def _write_index(self, index: Dict[str, Dict[str, Any]]) -> None:
        """Write the global index file atomically."""
        with _INDEX_LOCK:
            _write_json_file(self._index_path, index)

    def _update_index_entry(self, telemetry_id: str, meta: Dict[str, Any]) -> None:
        """Add or update a single entry in the index."""
        with _INDEX_LOCK:
            index = _read_json_file(self._index_path)
            index[telemetry_id] = meta
            _write_json_file(self._index_path, index)

    def _extract_index_meta(self, record: StoredTelemetry) -> Dict[str, Any]:
        """Extract lightweight metadata for the index."""
        payload = record.payload
        return {
            "telemetry_id": record.telemetry_id,
            "received_at_utc": record.received_at_utc.isoformat(),
            "partition": record.partition,
            "instrument_id": payload.instrument_id,
            "manufacturing_batch_id": payload.manufacturing_batch_id,
            "telemetry_category": payload.telemetry_category.value,
            "emitted_at_utc": payload.emitted_at_utc.isoformat(),
            "metric_count": len(payload.metrics),
            "metric_names": list(payload.metrics.keys()),
            "design_revision_id": payload.design_revision_id,
            "hardware_sku": payload.hardware_sku,
            "has_warnings": len(record.warnings) > 0,
        }

    def put(
        self,
        payload: TelemetryPayload,
        warnings: Optional[List[str]] = None,
    ) -> StoredTelemetry:
        """
        Store a validated telemetry payload.

        Args:
            payload: The validated TelemetryPayload
            warnings: Any validation warnings

        Returns:
            StoredTelemetry record with assigned ID
        """
        received_at = datetime.now(timezone.utc)
        telemetry_id = generate_telemetry_id()
        partition = self._date_partition(received_at)

        record = StoredTelemetry(
            telemetry_id=telemetry_id,
            payload=payload,
            received_at_utc=received_at,
            partition=partition,
            warnings=warnings or [],
        )

        # Ensure partition directory exists
        path = self._path_for(telemetry_id, partition)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write
        tmp = path.with_suffix(".json.tmp")
        try:
            tmp.write_text(
                json.dumps(record.to_dict(), indent=2, ensure_ascii=False, default=str),
                encoding="utf-8",
            )
            os.replace(tmp, path)

            # Update index
            self._update_index_entry(telemetry_id, self._extract_index_meta(record))

        except Exception:
            if tmp.exists():
                tmp.unlink()
            raise

        return record

    def get(self, telemetry_id: str) -> Optional[StoredTelemetry]:
        """
        Retrieve a telemetry record by ID.

        Args:
            telemetry_id: The telemetry ID

        Returns:
            StoredTelemetry if found, None otherwise
        """
        # Check index first for partition
        index = self._read_index()
        meta = index.get(telemetry_id)

        if meta and meta.get("partition"):
            path = self._path_for(telemetry_id, meta["partition"])
            if path.exists():
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    return StoredTelemetry.from_dict(data)
                except Exception:
                    pass

        # Fall back to scanning partitions
        partitions = sorted(
            [p for p in self.root.iterdir() if p.is_dir() and not p.name.startswith("_")],
            reverse=True,
        )

        for partition in partitions:
            path = partition / f"{telemetry_id}.json"
            if path.exists():
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    return StoredTelemetry.from_dict(data)
                except Exception:
                    continue

        return None

    def list_telemetry(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        instrument_id: Optional[str] = None,
        manufacturing_batch_id: Optional[str] = None,
        category: Optional[TelemetryCategory] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[StoredTelemetry]:
        """
        List telemetry records with optional filtering.

        Args:
            limit: Maximum results
            offset: Number to skip
            instrument_id: Filter by instrument
            manufacturing_batch_id: Filter by batch
            category: Filter by telemetry category
            date_from: Filter by received date >=
            date_to: Filter by received date <=

        Returns:
            List of matching StoredTelemetry records
        """
        index = self._read_index()

        if not index:
            self.rebuild_index()
            index = self._read_index()

        def matches(meta: Dict[str, Any]) -> bool:
            if instrument_id and meta.get("instrument_id") != instrument_id:
                return False
            if manufacturing_batch_id and meta.get("manufacturing_batch_id") != manufacturing_batch_id:
                return False
            if category and meta.get("telemetry_category") != category.value:
                return False

            if date_from or date_to:
                received = meta.get("received_at_utc")
                if received:
                    try:
                        received_dt = datetime.fromisoformat(received.replace("Z", "+00:00"))
                        if date_from and received_dt < date_from:
                            return False
                        if date_to and received_dt > date_to:
                            return False
                    except Exception:
                        pass

            return True

        # Filter and sort
        matching = [m for m in index.values() if matches(m)]
        matching.sort(key=lambda m: m.get("received_at_utc", ""), reverse=True)

        # Paginate
        page = matching[offset:offset + limit]

        # Load full records
        results: List[StoredTelemetry] = []
        for meta in page:
            telemetry_id = meta.get("telemetry_id")
            partition = meta.get("partition")
            if telemetry_id and partition:
                path = self._path_for(telemetry_id, partition)
                if path.exists():
                    try:
                        data = json.loads(path.read_text(encoding="utf-8"))
                        results.append(StoredTelemetry.from_dict(data))
                    except Exception:
                        continue

        return results

    def count(
        self,
        *,
        instrument_id: Optional[str] = None,
        manufacturing_batch_id: Optional[str] = None,
        category: Optional[TelemetryCategory] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> int:
        """Count telemetry records matching filters."""
        index = self._read_index()

        def matches(meta: Dict[str, Any]) -> bool:
            if instrument_id and meta.get("instrument_id") != instrument_id:
                return False
            if manufacturing_batch_id and meta.get("manufacturing_batch_id") != manufacturing_batch_id:
                return False
            if category and meta.get("telemetry_category") != category.value:
                return False

            if date_from or date_to:
                received = meta.get("received_at_utc")
                if received:
                    try:
                        received_dt = datetime.fromisoformat(received.replace("Z", "+00:00"))
                        if date_from and received_dt < date_from:
                            return False
                        if date_to and received_dt > date_to:
                            return False
                    except Exception:
                        pass

            return True

        return sum(1 for m in index.values() if matches(m))

    def get_instrument_summary(self, instrument_id: str) -> Dict[str, Any]:
        """
        Get summary statistics for an instrument.

        Args:
            instrument_id: The instrument ID

        Returns:
            Dict with summary statistics
        """
        index = self._read_index()

        records = [m for m in index.values() if m.get("instrument_id") == instrument_id]

        if not records:
            return {
                "instrument_id": instrument_id,
                "total_records": 0,
                "categories": {},
                "first_seen_utc": None,
                "last_seen_utc": None,
            }

        # Sort by received_at
        records.sort(key=lambda m: m.get("received_at_utc", ""))

        # Count by category
        category_counts: Dict[str, int] = {}
        for r in records:
            cat = r.get("telemetry_category", "unknown")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return {
            "instrument_id": instrument_id,
            "total_records": len(records),
            "categories": category_counts,
            "first_seen_utc": records[0].get("received_at_utc"),
            "last_seen_utc": records[-1].get("received_at_utc"),
            "batches": list(set(r.get("manufacturing_batch_id") for r in records if r.get("manufacturing_batch_id"))),
        }

    def rebuild_index(self) -> int:
        """
        Rebuild the index by scanning all partitions.

        Returns:
            Number of records indexed
        """
        index: Dict[str, Dict[str, Any]] = {}

        partitions = [
            p for p in self.root.iterdir()
            if p.is_dir() and not p.name.startswith("_")
        ]

        for partition in partitions:
            for path in partition.glob("*.json"):
                if path.suffix == ".tmp":
                    continue

                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    record = StoredTelemetry.from_dict(data)
                    index[record.telemetry_id] = self._extract_index_meta(record)
                except Exception:
                    continue

        self._write_index(index)
        return len(index)


# =============================================================================
# Module-level convenience functions
# =============================================================================

_default_store: Optional[TelemetryStore] = None


def _get_default_store() -> TelemetryStore:
    """Get or create the default store instance."""
    global _default_store
    if _default_store is None:
        _default_store = TelemetryStore()
    return _default_store


def store_telemetry(
    payload: TelemetryPayload,
    warnings: Optional[List[str]] = None,
) -> StoredTelemetry:
    """Store a validated telemetry payload."""
    store = _get_default_store()
    return store.put(payload, warnings=warnings)


def get_telemetry(telemetry_id: str) -> Optional[StoredTelemetry]:
    """Retrieve a telemetry record by ID."""
    store = _get_default_store()
    return store.get(telemetry_id)


def list_telemetry(
    *,
    limit: int = 50,
    offset: int = 0,
    instrument_id: Optional[str] = None,
    manufacturing_batch_id: Optional[str] = None,
    category: Optional[TelemetryCategory] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> List[StoredTelemetry]:
    """List telemetry records with optional filtering."""
    store = _get_default_store()
    return store.list_telemetry(
        limit=limit,
        offset=offset,
        instrument_id=instrument_id,
        manufacturing_batch_id=manufacturing_batch_id,
        category=category,
        date_from=date_from,
        date_to=date_to,
    )


def count_telemetry(
    *,
    instrument_id: Optional[str] = None,
    manufacturing_batch_id: Optional[str] = None,
    category: Optional[TelemetryCategory] = None,
) -> int:
    """Count telemetry records matching filters."""
    store = _get_default_store()
    return store.count(
        instrument_id=instrument_id,
        manufacturing_batch_id=manufacturing_batch_id,
        category=category,
    )


def get_instrument_summary(instrument_id: str) -> Dict[str, Any]:
    """Get summary statistics for an instrument."""
    store = _get_default_store()
    return store.get_instrument_summary(instrument_id)
