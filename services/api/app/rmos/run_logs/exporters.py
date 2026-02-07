"""
Run Log exporters - CSV and JSONL output.

Generation strategy:
- JSONL (Authoritative Log): Appended once per persisted run, synchronous
- CSV (Convenience View): Regenerated on demand, can be rebuilt from JSONL
"""
from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Iterator, List, Optional

from .schemas import RunLogEntry, CSV_COLUMNS


def _get_log_dir() -> Path:
    """Get the run logs directory, creating if needed."""
    base = os.environ.get("RMOS_RUNS_DIR", "data/rmos_runs")
    log_dir = Path(base) / "run_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def _flatten_entry_for_csv(entry: RunLogEntry) -> dict:
    """Flatten a RunLogEntry to CSV row dict."""
    # Compute bbox dimensions if available
    bbox_width = None
    bbox_height = None
    if entry.input_summary.bbox_mm and len(entry.input_summary.bbox_mm) >= 4:
        bbox = entry.input_summary.bbox_mm
        bbox_width = abs(bbox[2] - bbox[0])
        bbox_height = abs(bbox[3] - bbox[1])

    return {
        "run_id": entry.run_id,
        "created_at_utc": entry.created_at_utc.isoformat() if entry.created_at_utc else "",
        "mode": entry.mode,
        "tool_id": entry.tool_id or "",
        "status": entry.status,
        "risk_level": entry.risk_level,
        "warning_count": entry.warning_count,
        "override_applied": str(entry.override_applied).lower(),
        "block_reason": entry.block_reason or "",
        "rules_triggered": "|".join(entry.rules_triggered),
        "input_filename": entry.input_summary.filename or "",
        "loop_count": entry.input_summary.loop_count or "",
        "bbox_width_mm": bbox_width or "",
        "bbox_height_mm": bbox_height or "",
        "tool_d_mm": entry.cam_summary.tool_d_mm if entry.cam_summary else "",
        "stepover": entry.cam_summary.stepover if entry.cam_summary else "",
        "stepdown_mm": entry.cam_summary.stepdown_mm if entry.cam_summary else "",
        "z_rough_mm": entry.cam_summary.z_rough_mm if entry.cam_summary else "",
        "strategy": entry.cam_summary.strategy if entry.cam_summary else "",
        "gcode_lines": entry.outputs.gcode_lines if entry.outputs else "",
        "gcode_inline": str(entry.outputs.inline).lower() if entry.outputs else "",
        "feasibility_sha256": entry.hashes.feasibility_sha256 or "",
        "gcode_sha256": entry.hashes.gcode_sha256 or "",
        "parent_run_id": entry.lineage.parent_run_id or "",
    }


# =============================================================================
# JSONL Export (Authoritative)
# =============================================================================

def append_to_jsonl(entry: RunLogEntry, log_path: Optional[Path] = None) -> Path:
    """
    Append a single RunLogEntry to the JSONL log.

    This is the authoritative append operation - called synchronously
    when a RunArtifact is finalized.

    Returns the path to the log file.
    """
    if log_path is None:
        log_path = _get_log_dir() / "run_log.jsonl"

    # Serialize with ISO timestamps
    data = entry.model_dump(mode="json")

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n")

    return log_path


def export_jsonl(entries: List[RunLogEntry], path: Optional[Path] = None) -> Path:
    """
    Export multiple entries to a new JSONL file.

    Used for batch exports or regenerating logs.
    """
    if path is None:
        path = _get_log_dir() / f"run_log_export_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.jsonl"

    with open(path, "w", encoding="utf-8") as f:
        for entry in entries:
            data = entry.model_dump(mode="json")
            f.write(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n")

    return path


def read_jsonl(path: Optional[Path] = None) -> Iterator[RunLogEntry]:
    """
    Read entries from a JSONL log file.

    Yields RunLogEntry objects, skipping malformed lines.
    """
    if path is None:
        path = _get_log_dir() / "run_log.jsonl"

    if not path.exists():
        return

    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                yield RunLogEntry.model_validate(data)
            except (json.JSONDecodeError, ValueError) as e:  # WP-1: narrowed from except Exception
                # Log error but continue - don't fail on malformed entries
                print(f"Warning: Skipping malformed line {line_num}: {e}")


# =============================================================================
# CSV Export (Convenience View)
# =============================================================================

def export_csv(entries: List[RunLogEntry], path: Optional[Path] = None) -> Path:
    """
    Export entries to a CSV file.

    The CSV is a convenience view - it can be fully regenerated from JSONL.
    """
    if path is None:
        path = _get_log_dir() / "run_log.csv"

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for entry in entries:
            row = _flatten_entry_for_csv(entry)
            writer.writerow(row)

    return path


def export_csv_string(entries: List[RunLogEntry]) -> str:
    """Export entries to a CSV string for API responses."""
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    for entry in entries:
        row = _flatten_entry_for_csv(entry)
        writer.writerow(row)
    return output.getvalue()


def regenerate_csv_from_jsonl(
    jsonl_path: Optional[Path] = None,
    csv_path: Optional[Path] = None,
) -> Path:
    """
    Regenerate CSV from JSONL (rebuilds convenience view from authoritative log).

    This can be run on demand or as a nightly job.
    """
    entries = list(read_jsonl(jsonl_path))
    return export_csv(entries, csv_path)


# =============================================================================
# Query Helpers
# =============================================================================

def get_latest_entries(limit: int = 30, path: Optional[Path] = None) -> List[RunLogEntry]:
    """
    Get the most recent N entries from the log.

    Reads the entire log and returns the last `limit` entries.
    For large logs, consider using a database or indexed storage.
    """
    entries = list(read_jsonl(path))
    return entries[-limit:] if len(entries) > limit else entries


def get_entries_by_risk(risk_level: str, path: Optional[Path] = None) -> List[RunLogEntry]:
    """Get all entries with a specific risk level."""
    return [e for e in read_jsonl(path) if e.risk_level == risk_level.upper()]


def get_entries_with_override(path: Optional[Path] = None) -> List[RunLogEntry]:
    """Get all entries where an override was applied."""
    return [e for e in read_jsonl(path) if e.override_applied]


def count_by_risk_level(path: Optional[Path] = None) -> dict:
    """Count entries by risk level."""
    counts = {"GREEN": 0, "YELLOW": 0, "RED": 0, "UNKNOWN": 0, "ERROR": 0}
    for entry in read_jsonl(path):
        level = entry.risk_level.upper()
        if level in counts:
            counts[level] += 1
        else:
            counts["UNKNOWN"] += 1
    return counts
