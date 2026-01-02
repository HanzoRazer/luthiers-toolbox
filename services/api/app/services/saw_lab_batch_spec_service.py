"""
Saw Lab Batch Spec Service

Creates batch specification artifacts from a list of items.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_batch_spec(
    *,
    batch_label: str,
    session_id: Optional[str],
    tool_id: str,
    items: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Create a batch specification artifact.

    Args:
        batch_label: Label for this batch
        session_id: Optional session identifier
        tool_id: Default tool ID for the batch
        items: List of items to include in the batch

    Returns:
        Dict with batch_spec_artifact_id and metadata
    """
    from app.rmos.run_artifacts.store import write_run_artifact

    # Generate op_ids for each item
    processed_items = []
    for i, item in enumerate(items):
        item_copy = dict(item)
        if "op_id" not in item_copy:
            item_copy["op_id"] = f"op_{uuid.uuid4().hex[:8]}"
        processed_items.append(item_copy)

    payload = {
        "created_utc": _utc_now_iso(),
        "batch_label": batch_label,
        "session_id": session_id,
        "tool_id": tool_id,
        "items": processed_items,
        "item_count": len(processed_items),
    }

    art = write_run_artifact(
        kind="saw_batch_spec",
        status="OK",
        session_id=session_id,
        index_meta={
            "tool_kind": "saw_lab",
            "kind_group": "batch",
            "batch_label": batch_label,
            "session_id": session_id,
            "item_count": len(processed_items),
        },
        payload=payload,
    )

    artifact_id = art.get("artifact_id") if isinstance(art, dict) else getattr(art, "artifact_id", None)

    return {
        "batch_spec_artifact_id": artifact_id,
        "batch_label": batch_label,
        "session_id": session_id,
        "status": "OK",
        "item_count": len(processed_items),
    }
