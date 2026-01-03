#!/usr/bin/env python3
"""
Artifact Linkage Invariants Gate (OPERATION lane)

End-to-end gate that:
  1) boots a minimal Saw batch flow via HTTP:
       spec -> plan -> approve -> toolpaths -> job-log
  2) queries /api/rmos/runs filtered by (session_id, batch_label)
  3) validates required index_meta keys + parent linkage invariants across artifacts

This is a *governance gate*, not a unit test:
  - it detects drift in artifact wiring/lineage that would break UI, diffing, audit.

Env:
  ARTIFACT_GATE_API_URL            default http://127.0.0.1:8000
  ARTIFACT_GATE_SESSION_ID         default sess_artifact_gate
  ARTIFACT_GATE_BATCH_LABEL        default artifact_gate_batch
  ARTIFACT_GATE_TOOL_ID            default saw:thin_140
  ARTIFACT_GATE_MATERIAL_ID        default maple
  ARTIFACT_GATE_FAIL_FAST          default true
  ARTIFACT_GATE_VERBOSE            default true

Notes:
  - Uses only public API surface (no direct DB reads).
  - Tolerant to extra fields; strict on required invariants.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


def _bool_env(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


def _jpost(url: str, payload: Dict[str, Any], timeout_s: int = 20) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        method="POST",
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        raw = resp.read().decode("utf-8", errors="ignore")
    return json.loads(raw) if raw else {}


def _post(url: str, payload: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, str]] = None, timeout_s: int = 20) -> Dict[str, Any]:
    if params:
        from urllib.parse import urlencode
        url = url + ("&" if "?" in url else "?") + urlencode(params)
    if payload is None:
        data = b""
        req = urllib.request.Request(url, method="POST", data=data, headers={"Accept": "application/json"})
    else:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, method="POST", data=data, headers={"Content-Type": "application/json", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        raw = resp.read().decode("utf-8", errors="ignore")
    return json.loads(raw) if raw else {}


def _jget(url: str, timeout_s: int = 20) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        raw = resp.read().decode("utf-8", errors="ignore")
    return json.loads(raw) if raw else {}


def _norm(s: Any) -> str:
    return str(s) if s is not None else ""


def _get_meta(art: Dict[str, Any]) -> Dict[str, Any]:
    m = art.get("index_meta") or art.get("meta") or {}
    return m if isinstance(m, dict) else {}


def _id(art: Dict[str, Any]) -> str:
    return _norm(art.get("id") or art.get("artifact_id") or art.get("run_id"))


def _kind(art: Dict[str, Any]) -> str:
    return _norm(art.get("kind") or art.get("type") or "")


def _require(cond: bool, msg: str, *, fail_fast: bool) -> List[str]:
    if cond:
        return []
    if fail_fast:
        raise RuntimeError(msg)
    return [msg]


def _pick_first(d: Dict[str, Any], keys: List[str]) -> Optional[str]:
    for k in keys:
        v = d.get(k)
        if v:
            return _norm(v)
    return None


def main() -> int:
    api = os.getenv("ARTIFACT_GATE_API_URL", "http://127.0.0.1:8000").rstrip("/")
    session_id = os.getenv("ARTIFACT_GATE_SESSION_ID", "sess_artifact_gate")
    batch_label = os.getenv("ARTIFACT_GATE_BATCH_LABEL", "artifact_gate_batch")
    tool_id = os.getenv("ARTIFACT_GATE_TOOL_ID", "saw:thin_140")
    material_id = os.getenv("ARTIFACT_GATE_MATERIAL_ID", "maple")
    fail_fast = _bool_env("ARTIFACT_GATE_FAIL_FAST", True)
    verbose = _bool_env("ARTIFACT_GATE_VERBOSE", True)

    # 1) Spec
    spec = _jpost(
        f"{api}/api/saw/batch/spec",
        {
            "batch_label": batch_label,
            "session_id": session_id,
            "tool_id": tool_id,
            "items": [
                {
                    "part_id": "p1",
                    "qty": 1,
                    "material_id": material_id,
                    "thickness_mm": 6.0,
                    "length_mm": 300.0,
                    "width_mm": 30.0,
                }
            ],
        },
    )
    spec_id = _pick_first(spec, ["batch_spec_artifact_id", "artifact_id", "id"])
    if not spec_id:
        print(f"❌ Spec response missing spec id fields: {spec}", file=sys.stderr)
        return 2

    # 2) Plan
    plan = _jpost(f"{api}/api/saw/batch/plan", {"batch_spec_artifact_id": spec_id})
    plan_id = _pick_first(plan, ["batch_plan_artifact_id", "artifact_id", "id"])
    setups = plan.get("setups") or []
    if not plan_id or not setups:
        print(f"❌ Plan response missing required fields (plan_id/setups): {plan}", file=sys.stderr)
        return 2

    setup_order = [_norm(s.get("setup_key")) for s in setups if isinstance(s, dict) and s.get("setup_key")]
    op_order: List[str] = []
    for s in setups:
        if not isinstance(s, dict):
            continue
        for op in (s.get("ops") or []):
            if isinstance(op, dict) and op.get("op_id"):
                op_order.append(_norm(op["op_id"]))

    if not setup_order or not op_order:
        print(f"❌ Plan response missing setup_key/op_id: {plan}", file=sys.stderr)
        return 2

    # 3) Approve
    decision = _jpost(
        f"{api}/api/saw/batch/approve",
        {
            "batch_plan_artifact_id": plan_id,
            "approved_by": "artifact-gate",
            "reason": "artifact linkage invariants gate",
            "setup_order": setup_order,
            "op_order": op_order,
        },
    )
    decision_id = _pick_first(decision, ["batch_decision_artifact_id", "artifact_id", "id"])
    if not decision_id:
        print(f"❌ Approve response missing decision id: {decision}", file=sys.stderr)
        return 2

    # 4) Toolpaths / Execution
    exe = _jpost(f"{api}/api/saw/batch/toolpaths", {"batch_decision_artifact_id": decision_id})
    exec_id = _pick_first(exe, ["batch_execution_artifact_id", "artifact_id", "id"])
    if not exec_id:
        print(f"❌ Toolpaths response missing execution id: {exe}", file=sys.stderr)
        return 2

    # 5) Job log (so rollups/learning hooks have data)
    _post(
        f"{api}/api/saw/batch/job-log",
        payload={"metrics": {"burn": True, "parts_ok": 1, "cut_time_s": 10, "setup_time_s": 2}},
        params={
            "batch_execution_artifact_id": exec_id,
            "operator": "artifact-gate",
            "notes": "burn",
            "status": "COMPLETED",
        },
    )

    # 6) Query artifacts by session_id + batch_label
    # Standard runs endpoint per your conventions: /api/rmos/runs
    from urllib.parse import urlencode

    q = urlencode({"session_id": session_id, "batch_label": batch_label, "limit": 500})
    runs = _jget(f"{api}/api/rmos/runs?{q}")
    items = runs.get("items") or runs.get("runs") or runs.get("artifacts") or []
    if not isinstance(items, list) or not items:
        print(f"❌ No artifacts returned for session_id+batch_label. Response: {runs}", file=sys.stderr)
        return 2

    # Build index by kind for validation
    by_kind: Dict[str, List[Dict[str, Any]]] = {}
    for art in items:
        if not isinstance(art, dict):
            continue
        by_kind.setdefault(_kind(art), []).append(art)

    # Expected minimum kinds (tolerant: toolpaths may be separate artifacts)
    expected_min = {
        "saw_batch_spec",
        "saw_batch_plan",
        "saw_batch_decision",
        "saw_batch_execution",
    }
    # A few repos use alternate names; allow these aliases:
    kind_aliases = {
        "saw_batch_spec": ["saw_batch_spec", "saw_batch_spec_v1"],
        "saw_batch_plan": ["saw_batch_plan", "saw_batch_plan_v1"],
        "saw_batch_decision": ["saw_batch_decision", "saw_batch_decision_v1"],
        "saw_batch_execution": ["saw_batch_execution", "saw_batch_execution_v1"],
    }

    errors: List[str] = []

    def _find_one(canon: str) -> Optional[Dict[str, Any]]:
        for k in kind_aliases.get(canon, [canon]):
            lst = by_kind.get(k) or []
            if lst:
                # newest-first if timestamps exist, else first
                return lst[0]
        return None

    spec_art = _find_one("saw_batch_spec")
    plan_art = _find_one("saw_batch_plan")
    dec_art = _find_one("saw_batch_decision")
    exe_art = _find_one("saw_batch_execution")

    for canon in expected_min:
        if _find_one(canon) is None:
            errors += _require(False, f"Missing expected artifact kind: {canon}", fail_fast=fail_fast)

    if not (spec_art and plan_art and dec_art and exe_art):
        # already reported above
        if errors:
            print("❌ Artifact linkage invariants FAILED:")
            for e in errors:
                print("  -", e)
        return 1

    # Validate required index_meta keys on all artifacts in this session/batch label
    required_meta_keys = ["tool_kind", "batch_label", "session_id"]
    for art in items:
        if not isinstance(art, dict):
            continue
        meta = _get_meta(art)
        for k in required_meta_keys:
            errors += _require(k in meta and meta.get(k) not in (None, ""), f"{_kind(art)}({_id(art)}): missing index_meta.{k}", fail_fast=fail_fast)

    # Validate parent link invariants (tolerant to naming)
    spec_id_rt = _id(spec_art)
    plan_id_rt = _id(plan_art)
    dec_id_rt = _id(dec_art)
    exe_id_rt = _id(exe_art)

    plan_meta = _get_meta(plan_art)
    dec_meta = _get_meta(dec_art)
    exe_meta = _get_meta(exe_art)

    # plan -> spec
    plan_parent = _pick_first(plan_meta, ["parent_batch_spec_artifact_id", "parent_artifact_id", "parent_id"])
    errors += _require(plan_parent == spec_id_rt, f"plan parent mismatch: expected {spec_id_rt}, got {plan_parent}", fail_fast=fail_fast)

    # decision -> plan
    dec_parent = _pick_first(dec_meta, ["parent_batch_plan_artifact_id", "parent_artifact_id", "parent_id"])
    errors += _require(dec_parent == plan_id_rt, f"decision parent mismatch: expected {plan_id_rt}, got {dec_parent}", fail_fast=fail_fast)

    # execution -> decision
    exe_parent = _pick_first(exe_meta, ["parent_batch_decision_artifact_id", "parent_artifact_id", "parent_id"])
    errors += _require(exe_parent == dec_id_rt, f"execution parent mismatch: expected {dec_id_rt}, got {exe_parent}", fail_fast=fail_fast)

    if verbose:
        print("✅ Artifact Linkage Invariants Gate PASS")
        print(f"  session_id: {session_id}")
        print(f"  batch_label: {batch_label}")
        print(f"  spec: {spec_id_rt}")
        print(f"  plan: {plan_id_rt}")
        print(f"  decision: {dec_id_rt}")
        print(f"  execution: {exe_id_rt}")
        print(f"  artifacts_returned: {len(items)}")

    if errors:
        print("❌ Artifact linkage invariants FAILED:")
        for e in errors:
            print("  -", e)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
