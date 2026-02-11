from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .artifact_helpers import (
    as_items as _as_items,
    get_id as _get_id,
    get_kind as _get_kind,
    get_created as _created,
    pick_parent_id as _pick_parent_id,
)


def _root_score(kind: str) -> int:
    """
    Higher score = more likely to be the batch root.
    """
    k = (kind or "").lower()
    if "batch_spec" in k:
        return 100
    if k.endswith("_spec") or "spec" in k:
        return 80
    if "batch_parent" in k or "batch_summary" in k:
        return 60
    if "batch_plan" in k:
        return 40
    if "decision" in k:
        return 30
    if "toolpaths" in k:
        return 20
    if "execution" in k:
        return 10
    return 0


def resolve_batch_root(
    *,
    list_runs_filtered: Any,
    session_id: str,
    batch_label: str,
    tool_kind: Optional[str] = None,
    limit: int = 500,
) -> Optional[str]:
    """
    Finds the most likely "root" artifact id for a batch using only (session_id, batch_label).
    Prefers *batch_spec* kinds. Falls back to the artifact with no parent inside the batch.
    """
    res = list_runs_filtered(session_id=session_id, batch_label=batch_label, limit=limit)
    items = _as_items(res)
    if tool_kind:
        items = [
            a for a in items
            if isinstance(a, dict)
            and str((a.get("index_meta") or {}).get("tool_kind") or "") == tool_kind
        ]
    if not items:
        return None

    # Build a set of ids in the batch for "parent is external?" checks
    ids = {i for i in (_get_id(a) for a in items) if i}

    # Candidate scoring: kind score then created time (older tends to be root)
    scored: List[Tuple[int, str, str]] = []
    for a in items:
        if not isinstance(a, dict):
            continue
        aid = _get_id(a)
        if not aid:
            continue
        kind = _get_kind(a)
        score = _root_score(kind)
        created = _created(a)
        scored.append((score, created, aid))

    # Primary pick: highest score; tie-breaker: earliest created timestamp
    scored.sort(key=lambda t: (-t[0], t[1] or "9999", t[2]))
    best = scored[0][2] if scored else None

    # If our best isn't a spec, try finding an internal "no parent within set" node (true root)
    if best:
        best_kind = next((_get_kind(a) for a in items if _get_id(a) == best), "")
        if "batch_spec" in (best_kind or "").lower():
            return best

    # Graph root fallback: node whose parent is missing or outside this batch set
    no_parent_in_set: List[Tuple[str, str]] = []
    for a in items:
        aid = _get_id(a)
        if not aid:
            continue
        pid = _pick_parent_id(a)
        if not pid or pid not in ids:
            no_parent_in_set.append((_created(a), aid))
    no_parent_in_set.sort(key=lambda t: t[0] or "9999")
    return no_parent_in_set[0][1] if no_parent_in_set else best


def list_batch_tree(
    *,
    list_runs_filtered: Any,
    session_id: str,
    batch_label: str,
    tool_kind: Optional[str] = None,
    limit: int = 1000,
) -> Dict[str, Any]:
    """
    Returns a simple tree representation:
      {
        "session_id": ...,
        "batch_label": ...,
        "tool_kind": ...,
        "root_artifact_id": ...,
        "nodes": [
          {"id":..., "kind":..., "created_utc":..., "parent_id":..., "children":[...], "index_meta": {...}},
          ...
        ]
      }
    """
    res = list_runs_filtered(session_id=session_id, batch_label=batch_label, limit=limit)
    items = [a for a in _as_items(res) if isinstance(a, dict)]
    if tool_kind:
        items = [a for a in items if str((a.get("index_meta") or {}).get("tool_kind") or "") == tool_kind]

    # Index nodes
    nodes: Dict[str, Dict[str, Any]] = {}
    for a in items:
        aid = _get_id(a)
        if not aid:
            continue
        nodes[aid] = {
            "id": aid,
            "kind": _get_kind(a),
            "created_utc": _created(a),
            "parent_id": _pick_parent_id(a),
            "children": [],
            "index_meta": a.get("index_meta") or {},
        }

    # Wire children (only if parent exists within batch set)
    for aid, n in nodes.items():
        pid = n.get("parent_id")
        if pid and pid in nodes:
            nodes[pid]["children"].append(aid)

    # Stable child ordering by created_utc then id
    for n in nodes.values():
        n["children"].sort(key=lambda cid: (nodes[cid].get("created_utc") or "9999", cid))

    root_id = resolve_batch_root(
        list_runs_filtered=list_runs_filtered,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
        limit=min(limit, 500),
    )

    # Emit nodes list in BFS-ish order from root if possible, else chronological
    ordered: List[Dict[str, Any]] = []
    if root_id and root_id in nodes:
        q = [root_id]
        seen = set()
        while q:
            cur = q.pop(0)
            if cur in seen:
                continue
            seen.add(cur)
            ordered.append(nodes[cur])
            q.extend(nodes[cur]["children"])
        # include any disconnected nodes (rare)
        for aid in sorted(nodes.keys()):
            if aid not in seen:
                ordered.append(nodes[aid])
    else:
        ordered = sorted(nodes.values(), key=lambda n: (n.get("created_utc") or "9999", n["id"]))

    return {
        "session_id": session_id,
        "batch_label": batch_label,
        "tool_kind": tool_kind,
        "root_artifact_id": root_id,
        "node_count": len(nodes),
        "nodes": ordered,
    }
