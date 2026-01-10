from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from .batch_tree import list_batch_tree


def _created_utc(art: Dict[str, Any]) -> str:
    payload = art.get("payload") or art.get("data") or {}
    if isinstance(payload, dict) and isinstance(payload.get("created_utc"), str):
        return payload["created_utc"]
    if isinstance(art.get("created_utc"), str):
        return art["created_utc"]
    return ""


def _kind(art: Dict[str, Any]) -> str:
    return str(art.get("kind") or (art.get("index_meta") or {}).get("kind") or "")


def _risk_bucket(art: Dict[str, Any]) -> Optional[str]:
    payload = art.get("payload") or art.get("data") or {}
    meta = art.get("index_meta") or {}
    for k in ("risk_bucket", "risk_level", "risk"):
        v = None
        if isinstance(payload, dict):
            v = payload.get(k)
        if not v and isinstance(meta, dict):
            v = meta.get(k)
        if v:
            return str(v).upper()
    return None


def _status(art: Dict[str, Any]) -> Optional[str]:
    payload = art.get("payload") or art.get("data") or {}
    for k in ("status", "run_status", "state"):
        if isinstance(payload, dict) and payload.get(k):
            return str(payload.get(k)).upper()
    if art.get("status"):
        return str(art.get("status")).upper()
    return None


def _headline(art: Dict[str, Any]) -> str:
    k = _kind(art).lower()
    payload = art.get("payload") or art.get("data") or {}
    if not isinstance(payload, dict):
        payload = {}

    if "batch_spec" in k:
        tool_id = payload.get("tool_id") or (payload.get("context") or {}).get("tool_id")
        items = payload.get("items") or []
        return f"Spec (tool={tool_id}, items={len(items) if isinstance(items, list) else 'n/a'})"

    if "batch_plan" in k:
        setups = payload.get("setups") or []
        return f"Plan (setups={len(setups) if isinstance(setups, list) else 'n/a'})"

    if "decision" in k or "approve" in k:
        choice = payload.get("selected_setup_key") or payload.get("choice") or payload.get("decision")
        rb = payload.get("risk_bucket") or payload.get("risk_level")
        return f"Decision (choice={choice}, risk={rb})"

    if "toolpaths" in k:
        stats = payload.get("statistics") or {}
        moves = stats.get("move_count") or payload.get("move_count")
        return f"Toolpaths (moves={moves})"

    if "execution" in k:
        return "Execution"

    if "job_log" in k or "joblog" in k:
        notes = payload.get("notes") or payload.get("operator_notes") or ""
        txt = notes if isinstance(notes, str) else ""
        return f"Job log ({txt[:60] + '…' if len(txt) > 60 else txt})"

    if "learning" in k:
        return "Learning event"

    return "Artifact"


def _type_bucket(kind: str) -> str:
    k = (kind or "").lower()
    if "batch_spec" in k:
        return "spec"
    if "batch_plan" in k:
        return "plan"
    if "decision" in k or "approve" in k:
        return "decision"
    if "toolpaths" in k:
        return "toolpaths"
    if "execution" in k:
        return "execution"
    if "job_log" in k or "joblog" in k:
        return "job_log"
    if "learning" in k:
        return "learning_event"
    return "other"


@dataclass
class GroupedTimelinePorts:
    list_runs_filtered: Any
    get_run: Any


def build_grouped_timeline(
    ports: GroupedTimelinePorts,
    *,
    session_id: str,
    batch_label: str,
    tool_kind: Optional[str] = None,
    max_nodes: int = 2000,
    include_types: Optional[Set[str]] = None,
    collapse_other: bool = False,
    collapse_other_under: str = "auto",
) -> Dict[str, Any]:
    """
    Tree-aware grouped timeline:
      - Uses batch-tree order (BFS from root)
      - Emits nested children structure (UI friendly)
      - Each node includes compact summary fields + children
    """
    tree = list_batch_tree(
        list_runs_filtered=ports.list_runs_filtered,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
        limit=max_nodes,
    )
    nodes: List[Dict[str, Any]] = tree.get("nodes") or []
    root_id = tree.get("root_artifact_id")

    # Build a map of id -> node skeleton (from batch-tree) with children IDs
    skel: Dict[str, Dict[str, Any]] = {n["id"]: n for n in nodes if isinstance(n, dict) and n.get("id")}

    # Build enriched nodes with details, keeping children as IDs for now
    enriched: Dict[str, Dict[str, Any]] = {}
    for nid, n in skel.items():
        art = ports.get_run(nid) or {}
        kind = _kind(art) or str(n.get("kind") or "")
        typ = _type_bucket(kind)
        enriched[nid] = {
            "id": nid,
            "kind": kind,
            "type": typ,
            "created_utc": _created_utc(art) or str(n.get("created_utc") or ""),
            "parent_id": n.get("parent_id"),
            "status": _status(art),
            "risk_bucket": _risk_bucket(art),
            "headline": _headline(art),
            "children": list(n.get("children") or []),
        }

    # Default include_types = all
    if include_types is not None:
        include_types = {t.strip() for t in include_types if t and t.strip()}
        if not include_types:
            include_types = None

    def _is_included(node: Dict[str, Any]) -> bool:
        if include_types is None:
            return True
        return (node.get("type") or "other") in include_types

    # Helper: find nearest "batch parent" for collapsing "other"
    # collapse_other_under options:
    #   - "auto": nearest ancestor whose type is in {"spec","plan","decision","toolpaths","execution"}
    #   - explicit type: "spec"|"plan"|"decision"|"toolpaths"|"execution"
    CORE_TYPES = {"spec", "plan", "decision", "toolpaths", "execution"}

    def _nearest_anchor(start_id: str) -> Optional[str]:
        cur = enriched.get(start_id)
        seen: Set[str] = set()
        while cur:
            cid = cur.get("id")
            if not cid or cid in seen:
                break
            seen.add(cid)
            ctype = cur.get("type") or "other"
            if collapse_other_under == "auto":
                if ctype in CORE_TYPES:
                    return cid
            else:
                if ctype == collapse_other_under:
                    return cid
            pid = cur.get("parent_id")
            cur = enriched.get(pid) if pid else None
        return None

    # Precompute children lists with filtering + optional collapsing.
    # We do this once to avoid duplicating logic during materialization.
    filtered_children: Dict[str, List[str]] = {nid: [] for nid in enriched.keys()}
    for nid, node in enriched.items():
        filtered_children[nid] = []

    # First pass: direct include filtering (keep ids)
    for nid, node in enriched.items():
        kept: List[str] = []
        for cid in node.get("children") or []:
            child = enriched.get(cid)
            if not child:
                continue
            if _is_included(child):
                kept.append(cid)
            else:
                # If excluded, we still may want to keep its descendants by "lifting" them up.
                # This implements "hide leaf nodes by type" without losing the run signal.
                stack = list(child.get("children") or [])
                while stack:
                    gcid = stack.pop(0)
                    gchild = enriched.get(gcid)
                    if not gchild:
                        continue
                    if _is_included(gchild):
                        kept.append(gcid)
                    else:
                        stack.extend(list(gchild.get("children") or []))
        # de-dupe, stable
        seen_c: Set[str] = set()
        deduped: List[str] = []
        for x in kept:
            if x not in seen_c:
                seen_c.add(x)
                deduped.append(x)
        filtered_children[nid] = deduped

    # Second pass: collapse "other" under nearest anchor
    if collapse_other:
        # Build reverse parent pointers to handle re-homing safely.
        # We'll create an "other_collapsed" map: anchor_id -> list[other_ids]
        other_collapsed: Dict[str, List[str]] = {}
        for nid, node in enriched.items():
            if node.get("type") != "other":
                continue
            if include_types is not None and "other" in include_types:
                # If user explicitly included "other", don't collapse them away.
                continue
            anchor = _nearest_anchor(nid)
            if not anchor:
                continue
            other_collapsed.setdefault(anchor, []).append(nid)

        # Remove "other" from wherever it currently sits, then attach under anchor.
        # Because our tree is built from filtered_children, we mutate that structure.
        for pid, kids in list(filtered_children.items()):
            filtered_children[pid] = [k for k in kids if enriched.get(k, {}).get("type") != "other"]

        for anchor, others in other_collapsed.items():
            # attach (stable by created_utc)
            others.sort(key=lambda oid: (enriched.get(oid, {}).get("created_utc") or "9999", oid))
            filtered_children[anchor].extend([o for o in others if o not in filtered_children[anchor]])

    # Convert children IDs to nested dicts (depth-first) from root
    def _materialize(node_id: str, depth: int = 0, seen: Optional[set] = None) -> Dict[str, Any]:
        if seen is None:
            seen = set()
        if node_id in seen:
            # cycle guard
            return {"id": node_id, "cycle": True}
        seen.add(node_id)
        base = enriched.get(node_id) or {"id": node_id}
        node = dict(base)
        child_ids = list(filtered_children.get(node_id, []))
        out_children = []
        for cid in child_ids:
            if cid in enriched:
                out_children.append(_materialize(cid, depth + 1, seen))
            else:
                out_children.append({"id": cid, "missing": True})
        # stable child ordering by created_utc then id
        out_children.sort(key=lambda x: (x.get("created_utc") or "9999", x.get("id") or ""))
        node["children"] = out_children
        node["depth"] = depth
        return node

    # If root is excluded by include_types, we still emit it as an anchor container (specifically for UI),
    # but mark it filtered. This prevents an empty response when the user filters types aggressively.
    grouped_root = None
    if root_id and root_id in enriched:
        grouped_root = _materialize(root_id, 0)
        if include_types is not None and not _is_included(enriched[root_id]):
            grouped_root["filtered_root"] = True

    # Also provide a flat, grouped-by-type summary for quick UI panels
    by_type: Dict[str, List[Dict[str, Any]]] = {}
    for n in enriched.values():
        by_type.setdefault(n.get("type") or "other", []).append(
            {k: n.get(k) for k in ("id", "kind", "created_utc", "status", "risk_bucket", "headline", "parent_id")}
        )
    for t in by_type:
        by_type[t].sort(key=lambda x: (x.get("created_utc") or "9999", x.get("id") or ""))

    return {
        "session_id": session_id,
        "batch_label": batch_label,
        "tool_kind": tool_kind,
        "root_artifact_id": root_id,
        "node_count": tree.get("node_count", len(enriched)),
        "grouped_root": grouped_root,
        "by_type": by_type,
        "filters": {
            "include_types": sorted(list(include_types)) if include_types is not None else None,
            "collapse_other": collapse_other,
            "collapse_other_under": collapse_other_under,
        },
    }
