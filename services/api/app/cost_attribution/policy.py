from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Set, Tuple

PolicyMapping = Dict[str, str]  # "category.metric" -> cost_dimension

DEFAULT_POLICY_PATH = Path("contracts/telemetry_cost_mapping_policy_v1.json")


def load_policy(
    repo_root: Path,
    policy_path: Path = DEFAULT_POLICY_PATH,
) -> Tuple[PolicyMapping, Set[str]]:
    """
    Load the telemetry-to-cost mapping policy from the contracts directory.

    Returns:
        Tuple of (allowed_mappings, forbidden_substrings)
        - allowed_mappings: dict of "category.metric" -> cost_dimension
        - forbidden_substrings: set of metric key substrings to block
    """
    p = (repo_root / policy_path).resolve()
    data = json.loads(p.read_text(encoding="utf-8"))
    allowed = data.get("allowed_mappings", {})
    forbidden_substrings = set(data.get("forbidden_metric_key_substrings", []))
    return dict(allowed), forbidden_substrings
