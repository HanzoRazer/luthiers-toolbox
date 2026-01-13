from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple
from pathlib import Path

from .models import CostFact
from .policy import load_policy


def _parse_dt(dt_str: str) -> datetime:
    """
    Parse ISO 8601 datetime string.
    emitted_at_utc is date-time per schema; python fromisoformat handles "Z" poorly in older versions.
    Normalize simple "Z" to +00:00.
    """
    if dt_str.endswith("Z"):
        dt_str = dt_str[:-1] + "+00:00"
    return datetime.fromisoformat(dt_str)


def telemetry_to_cost_facts(
    repo_root: Path,
    telemetry_payload: Dict[str, Any],
) -> Tuple[List[CostFact], List[str]]:
    """
    Map a *validated* telemetry payload into internal CostFacts using policy.

    Args:
        repo_root: Path to repository root (for loading policy)
        telemetry_payload: Validated telemetry payload dict

    Returns:
        Tuple of (facts, warnings).
        - facts: List of CostFact objects for allowed metrics
        - warnings: List of warning messages (non-fatal)
    """
    policy_map, forbidden_substrings = load_policy(repo_root)

    warnings: List[str] = []
    facts: List[CostFact] = []

    category = telemetry_payload["telemetry_category"]
    metrics: Dict[str, Any] = telemetry_payload["metrics"]

    manufacturing_batch_id = telemetry_payload["manufacturing_batch_id"]
    instrument_id = telemetry_payload["instrument_id"]
    emitted_at = _parse_dt(telemetry_payload["emitted_at_utc"])
    schema_version = telemetry_payload.get("schema_version", "v1")

    for metric_name, metric_obj in metrics.items():
        # Extra defensive: prevent "key smuggling" from reaching cost layer
        lowered = metric_name.lower()
        if any(s in lowered for s in forbidden_substrings):
            warnings.append(f"Skipped forbidden metric key '{metric_name}' (substring policy).")
            continue

        policy_key = f"{category}.{metric_name}"
        if policy_key not in policy_map:
            # Not mapped -> ignored (v1 policy is explicit allow-list)
            continue

        dim = policy_map[policy_key]

        value = float(metric_obj["value"])
        unit = str(metric_obj["unit"])
        aggregation = str(metric_obj["aggregation"])

        facts.append(
            CostFact(
                manufacturing_batch_id=manufacturing_batch_id,
                instrument_id=instrument_id,
                cost_dimension=dim,  # type: ignore[arg-type]
                value=value,
                unit=unit,
                aggregation=aggregation,
                source_metric_key=policy_key,
                emitted_at_utc=emitted_at,
                telemetry_category=category,
                telemetry_schema_version=schema_version,
                meta={
                    "design_revision_id": telemetry_payload.get("design_revision_id"),
                    "hardware_sku": telemetry_payload.get("hardware_sku"),
                    "component_lot_id": telemetry_payload.get("component_lot_id"),
                },
            )
        )

    return facts, warnings
