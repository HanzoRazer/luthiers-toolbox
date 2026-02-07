from __future__ import annotations

import io
import json
import zipfile
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .batch_tree import list_batch_tree


def _safe_json(obj: Any) -> bytes:
    return json.dumps(obj, indent=2, sort_keys=True, default=str).encode("utf-8")


def _artifact_id(a: Dict[str, Any]) -> Optional[str]:
    v = a.get("id") or a.get("artifact_id")
    return str(v) if v else None


def _artifact_payload(a: Dict[str, Any]) -> Dict[str, Any]:
    p = a.get("payload") or a.get("data") or {}
    return p if isinstance(p, dict) else {"_raw": p}


def _artifact_meta(a: Dict[str, Any]) -> Dict[str, Any]:
    m = a.get("index_meta") or {}
    return m if isinstance(m, dict) else {}


@dataclass
class AuditExportPorts:
    """
    Minimal ports for audit export so we can unit-test easily.
    """

    list_runs_filtered: Any  # callable(**filters) -> dict|list
    get_run: Any  # callable(artifact_id) -> dict|None
    list_attachments: Any  # callable(artifact_id) -> list[dict]
    get_attachment_bytes: Any  # callable(artifact_id, attachment_id|sha|path) -> bytes


def build_batch_audit_zip(
    ports: AuditExportPorts,
    *,
    session_id: str,
    batch_label: str,
    tool_kind: Optional[str] = None,
    include_attachments: bool = True,
    max_nodes: int = 2000,
) -> Tuple[bytes, Dict[str, Any]]:
    """
    Creates a ZIP with:
      - manifest.json (tree + summary)
      - artifacts/<kind>__<id>.json (payload + index_meta)
      - attachments/<artifact_id>/<name_or_sha> (raw bytes) if enabled
    Returns (zip_bytes, manifest_dict).
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

    manifest: Dict[str, Any] = {
        "session_id": session_id,
        "batch_label": batch_label,
        "tool_kind": tool_kind,
        "root_artifact_id": root_id,
        "node_count": tree.get("node_count", len(nodes)),
        "nodes": nodes,
        "export": {
            "include_attachments": include_attachments,
            "format_version": 1,
        },
    }

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", _safe_json(manifest))

        # Write artifact payloads
        for n in nodes:
            aid = n.get("id")
            if not aid:
                continue
            art = ports.get_run(aid) or {}
            kind = str(art.get("kind") or n.get("kind") or "artifact")
            safe_kind = kind.replace("/", "_")
            fname = f"artifacts/{safe_kind}__{aid}.json"
            z.writestr(
                fname,
                _safe_json(
                    {
                        "id": aid,
                        "kind": kind,
                        "created_utc": n.get("created_utc"),
                        "parent_id": n.get("parent_id"),
                        "index_meta": _artifact_meta(art) or n.get("index_meta") or {},
                        "payload": _artifact_payload(art),
                    }
                ),
            )

            # Attachments (best-effort)
            if include_attachments:
                try:
                    atts = ports.list_attachments(aid) or []
                except (OSError, RuntimeError, KeyError):  # WP-1: narrowed from except Exception
                    atts = []
                for att in atts:
                    if not isinstance(att, dict):
                        continue
                    # Support multiple attachment schemas:
                    # - {"id": "...", "name": "...", "sha256": "..."}
                    # - {"sha256": "...", "filename": "..."}
                    att_name = (
                        att.get("name")
                        or att.get("filename")
                        or att.get("path")
                        or att.get("sha256")
                        or att.get("id")
                        or "attachment"
                    )
                    att_key = att.get("id") or att.get("sha256") or att.get("path") or att_name
                    try:
                        b = ports.get_attachment_bytes(aid, att_key)
                    except (OSError, KeyError):  # WP-1: narrowed from except Exception
                        continue
                    z.writestr(f"attachments/{aid}/{att_name}", b)

    return buf.getvalue(), manifest
