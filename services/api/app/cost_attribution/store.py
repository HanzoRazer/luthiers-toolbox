from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from .models import CostFact


def _ymd(dt: datetime) -> str:
    """Format datetime as YYYY-MM-DD."""
    return dt.strftime("%Y-%m-%d")


def _ensure_dir(p: Path) -> None:
    """Ensure directory exists."""
    p.mkdir(parents=True, exist_ok=True)


def append_cost_facts(repo_root: Path, facts: List[CostFact]) -> None:
    """
    Append cost facts to date-partitioned JSONL storage.

    Args:
        repo_root: Path to repository root
        facts: List of CostFact objects to persist
    """
    if not facts:
        return

    base = repo_root / "data" / "cost_facts"
    _ensure_dir(base)

    # Partition by emitted date (same pattern as telemetry)
    day = _ymd(facts[0].emitted_at_utc)
    path = base / f"cost_facts_{day}.jsonl"

    with path.open("a", encoding="utf-8") as f:
        for cf in facts:
            f.write(json.dumps({
                "manufacturing_batch_id": cf.manufacturing_batch_id,
                "instrument_id": cf.instrument_id,
                "cost_dimension": cf.cost_dimension,
                "value": cf.value,
                "unit": cf.unit,
                "aggregation": cf.aggregation,
                "source_metric_key": cf.source_metric_key,
                "emitted_at_utc": cf.emitted_at_utc.isoformat(),
                "telemetry_category": cf.telemetry_category,
                "telemetry_schema_version": cf.telemetry_schema_version,
                "meta": cf.meta or {},
            }, sort_keys=True) + "\n")


def summarize_by_batch(repo_root: Path, manufacturing_batch_id: str) -> Dict[str, Any]:
    """
    Summarize cost facts for a manufacturing batch.

    Args:
        repo_root: Path to repository root
        manufacturing_batch_id: Batch ID to summarize

    Returns:
        Summary dict with cost_breakdown by dimension
    """
    base = repo_root / "data" / "cost_facts"
    if not base.exists():
        return {
            "manufacturing_batch_id": manufacturing_batch_id,
            "cost_breakdown": {},
            "currency": "USD",
        }

    totals: Dict[str, float] = {}
    for fp in sorted(base.glob("cost_facts_*.jsonl")):
        for line in fp.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            obj = json.loads(line)
            if obj.get("manufacturing_batch_id") != manufacturing_batch_id:
                continue
            dim = obj["cost_dimension"]
            totals[dim] = float(totals.get(dim, 0.0)) + float(obj.get("value", 0.0))

    return {
        "manufacturing_batch_id": manufacturing_batch_id,
        "cost_breakdown": totals,
        "currency": "USD",
    }


def summarize_by_instrument(repo_root: Path, instrument_id: str) -> Dict[str, Any]:
    """
    Summarize cost facts for a specific instrument.

    Args:
        repo_root: Path to repository root
        instrument_id: Instrument ID to summarize

    Returns:
        Summary dict with cost_breakdown by dimension
    """
    base = repo_root / "data" / "cost_facts"
    if not base.exists():
        return {
            "instrument_id": instrument_id,
            "cost_breakdown": {},
            "currency": "USD",
        }

    totals: Dict[str, float] = {}
    for fp in sorted(base.glob("cost_facts_*.jsonl")):
        for line in fp.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            obj = json.loads(line)
            if obj.get("instrument_id") != instrument_id:
                continue
            dim = obj["cost_dimension"]
            totals[dim] = float(totals.get(dim, 0.0)) + float(obj.get("value", 0.0))

    return {
        "instrument_id": instrument_id,
        "cost_breakdown": totals,
        "currency": "USD",
    }
