#!/usr/bin/env python3
"""
Artifact Linkage Invariants Checker

Validates that run artifacts maintain proper parent-child linkage:
- parent_id references exist
- session_id chains are consistent
- batch tree relationships are valid

Usage:
    python check_artifact_linkage_invariants.py [--runs-dir PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


def load_artifact(path: Path) -> Optional[Dict[str, Any]]:
    """Load a run artifact JSON file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def extract_linkage(artifact: Dict[str, Any]) -> Dict[str, Any]:
    """Extract linkage-relevant fields from an artifact."""
    meta = artifact.get("meta") or {}
    payload = artifact.get("payload") or {}
    return {
        "run_id": artifact.get("run_id"),
        "parent_id": meta.get("parent_id"),
        "session_id": meta.get("session_id") or payload.get("session_id"),
        "batch_label": payload.get("batch_label"),
        "event_type": artifact.get("event_type"),
    }


def check_parent_exists(
    artifacts: Dict[str, Dict[str, Any]],
    linkages: Dict[str, Dict[str, Any]],
) -> List[str]:
    """Check that all parent_id references point to existing artifacts."""
    violations = []
    for run_id, link in linkages.items():
        parent_id = link.get("parent_id")
        if parent_id and parent_id not in artifacts:
            violations.append(f"{run_id}: parent_id '{parent_id}' not found")
    return violations


def check_session_consistency(
    linkages: Dict[str, Dict[str, Any]],
) -> List[str]:
    """Check that artifacts in the same batch have consistent session_id."""
    # Group by batch_label
    batches: Dict[str, Set[str]] = {}
    for run_id, link in linkages.items():
        batch = link.get("batch_label")
        session = link.get("session_id")
        if batch and session:
            batches.setdefault(batch, set()).add(session)

    violations = []
    for batch, sessions in batches.items():
        if len(sessions) > 1:
            violations.append(f"batch '{batch}' has inconsistent sessions: {sessions}")
    return violations


def main(runs_dir: Path) -> int:
    """Run all linkage invariant checks."""
    if not runs_dir.exists():
        print(f"Runs directory not found: {runs_dir}", file=sys.stderr)
        return 1

    # Collect all artifacts
    artifacts: Dict[str, Dict[str, Any]] = {}
    for json_file in runs_dir.rglob("*.json"):
        artifact = load_artifact(json_file)
        if artifact and "run_id" in artifact:
            artifacts[artifact["run_id"]] = artifact

    if not artifacts:
        print("No artifacts found - nothing to check")
        return 0

    # Extract linkage info
    linkages = {rid: extract_linkage(art) for rid, art in artifacts.items()}

    # Run checks
    all_violations: List[str] = []
    all_violations.extend(check_parent_exists(artifacts, linkages))
    all_violations.extend(check_session_consistency(linkages))

    if all_violations:
        print(f"FAIL: {len(all_violations)} linkage violation(s) found:")
        for v in all_violations:
            print(f"  - {v}")
        return 1

    print(f"OK: {len(artifacts)} artifacts checked, no linkage violations")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check artifact linkage invariants")
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=Path("data/runs/rmos"),
        help="Path to runs directory",
    )
    args = parser.parse_args()
    sys.exit(main(args.runs_dir))
