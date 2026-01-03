#!/usr/bin/env python3
"""
Validate RunArtifact Contract (index_meta + parent linkage invariants)

Unlike check_artifact_linkage_invariants.py (which creates artifacts),
this script validates *existing* artifacts returned by:
  GET /api/rmos/runs

Use cases:
  - CI smoke: validate latest N artifacts for required keys
  - Forensics: validate a specific session_id / batch_label
  - Refactor safety: detect contract drift before merging router changes

Env:
  CONTRACT_API_URL                 default http://127.0.0.1:8000
  CONTRACT_SESSION_ID              optional
  CONTRACT_BATCH_LABEL             optional
  CONTRACT_LIMIT                   default 200
  CONTRACT_FAIL_FAST               default false
  CONTRACT_VERBOSE                 default true

Required meta keys (minimum invariant):
  index_meta.tool_kind
  index_meta.batch_label
  index_meta.session_id

Parent linkage invariants (when present):
  - if kind contains "plan": must link to spec
  - if kind contains "decision": must link to plan
  - if kind contains "execution" or "toolpaths": must link to decision

This script is tolerant to naming variations:
  - accepts parent_*_artifact_id OR parent_artifact_id OR parent_id
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


def _bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


def _get(url: str, timeout_s: int = 20) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout_s) as r:
        raw = r.read().decode("utf-8", errors="ignore")
    return json.loads(raw) if raw else {}


def _norm(s: Any) -> str:
    return str(s) if s is not None else ""


def _id(a: Dict[str, Any]) -> str:
    return _norm(a.get("id") or a.get("artifact_id") or a.get("run_id"))


def _kind(a: Dict[str, Any]) -> str:
    return _norm(a.get("kind") or a.get("type") or "")


def _meta(a: Dict[str, Any]) -> Dict[str, Any]:
    m = a.get("index_meta") or a.get("meta") or {}
    return m if isinstance(m, dict) else {}


def _pick(d: Dict[str, Any], keys: List[str]) -> Optional[str]:
    for k in keys:
        v = d.get(k)
        if v not in (None, "", []):
            return _norm(v)
    return None


@dataclass
class Violation:
    artifact_id: str
    kind: str
    message: str


def main() -> int:
    api = os.getenv("CONTRACT_API_URL", "http://127.0.0.1:8000").rstrip("/")
    session_id = os.getenv("CONTRACT_SESSION_ID")
    batch_label = os.getenv("CONTRACT_BATCH_LABEL")
    limit = int(os.getenv("CONTRACT_LIMIT", "200"))
    fail_fast = _bool("CONTRACT_FAIL_FAST", False)
    verbose = _bool("CONTRACT_VERBOSE", True)

    from urllib.parse import urlencode

    params = {"limit": str(limit)}
    if session_id:
        params["session_id"] = session_id
    if batch_label:
        params["batch_label"] = batch_label

    runs = _get(f"{api}/api/rmos/runs?{urlencode(params)}")
    items = runs.get("items") or runs.get("runs") or runs.get("artifacts") or []
    if not isinstance(items, list):
        print(f"❌ Unexpected /api/rmos/runs response shape: {runs}", file=sys.stderr)
        return 2

    # Index by id for linkage checks
    by_id: Dict[str, Dict[str, Any]] = {}
    for a in items:
        if isinstance(a, dict):
            by_id[_id(a)] = a

    required_meta_keys = ["tool_kind", "batch_label", "session_id"]
    violations: List[Violation] = []

    def v(a: Dict[str, Any], msg: str) -> None:
        viol = Violation(artifact_id=_id(a), kind=_kind(a), message=msg)
        violations.append(viol)
        if fail_fast:
            raise RuntimeError(f"{viol.kind}({viol.artifact_id}): {viol.message}")

    for a in items:
        if not isinstance(a, dict):
            continue
        k = _kind(a).lower()
        meta = _meta(a)

        # Required meta keys
        for mk in required_meta_keys:
            if meta.get(mk) in (None, ""):
                v(a, f"missing index_meta.{mk}")

        # Parent linkage checks (best-effort based on kind string)
        parent = _pick(meta, ["parent_artifact_id", "parent_id", "parent_run_id"]) or _pick(
            meta,
            [
                "parent_batch_spec_artifact_id",
                "parent_batch_plan_artifact_id",
                "parent_batch_decision_artifact_id",
                "parent_batch_execution_artifact_id",
            ],
        )

        if "plan" in k:
            p = _pick(meta, ["parent_batch_spec_artifact_id", "parent_artifact_id", "parent_id"])
            if not p:
                v(a, "plan missing parent spec link (parent_batch_spec_artifact_id|parent_artifact_id|parent_id)")
        if "decision" in k or "approve" in k:
            p = _pick(meta, ["parent_batch_plan_artifact_id", "parent_artifact_id", "parent_id"])
            if not p:
                v(a, "decision missing parent plan link (parent_batch_plan_artifact_id|parent_artifact_id|parent_id)")
        if "execution" in k or "toolpaths" in k:
            p = _pick(meta, ["parent_batch_decision_artifact_id", "parent_artifact_id", "parent_id"])
            if not p:
                v(a, "execution/toolpaths missing parent decision link (parent_batch_decision_artifact_id|parent_artifact_id|parent_id)")

        # If a parent is declared, ensure it exists in result set (when validating a filtered set)
        if parent and session_id and parent not in by_id:
            v(a, f"declares parent {parent} but parent not present in queried result set (hint: increase CONTRACT_LIMIT)")

    if verbose:
        print("--- RunArtifact Contract Validator ---")
        print(f"API: {api}")
        print(f"Filters: session_id={session_id!r} batch_label={batch_label!r} limit={limit}")
        print(f"Artifacts scanned: {len([a for a in items if isinstance(a, dict)])}")
        print(f"Violations: {len(violations)}")

    if violations:
        print("❌ Violations:")
        for viol in violations[:200]:
            print(f"  - {viol.kind}({viol.artifact_id}): {viol.message}")
        if len(violations) > 200:
            print(f"… truncated (showing first 200 of {len(violations)})")
        return 1

    print("✅ PASS: No contract violations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
