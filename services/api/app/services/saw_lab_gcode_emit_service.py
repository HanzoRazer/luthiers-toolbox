from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

# Type alias for artifact reader callable
ArtifactReader = Callable[[str], Any]


def _default_artifact_reader() -> ArtifactReader:
    """Return the default RMOS artifact reader."""
    from app.rmos.run_artifacts.store import read_run_artifact
    return read_run_artifact


def emit_gcode_from_moves(moves: List[Dict[str, Any]]) -> str:
    """
    Convert SawToolpathMove dicts to G-code string.

    Each move has: code, x, y, z, f, comment (all optional except code).
    """
    lines: List[str] = []
    for m in moves:
        code = m.get("code", "")
        if not code:
            continue

        parts = [code]
        if m.get("x") is not None:
            parts.append(f"X{float(m['x']):.4f}")
        if m.get("y") is not None:
            parts.append(f"Y{float(m['y']):.4f}")
        if m.get("z") is not None:
            parts.append(f"Z{float(m['z']):.4f}")
        if m.get("f") is not None:
            parts.append(f"F{float(m['f']):.1f}")

        line = " ".join(parts)
        if m.get("comment"):
            line += f"  ({m['comment']})"
        lines.append(line)

    return "\n".join(lines)


def export_op_toolpaths_gcode(
    *,
    op_toolpaths_artifact_id: str,
    read_artifact: Optional[ArtifactReader] = None,
) -> Dict[str, Any]:
    """
    Export G-code for a single op toolpath artifact.

    Args:
        op_toolpaths_artifact_id: The artifact ID to export
        read_artifact: Optional artifact reader callable (defaults to RMOS)

    Returns:
        {
            "gcode": str,
            "filename": str,
            "op_id": str,
            "status": str,
            "has_toolpaths": bool,
        }
    """
    if read_artifact is None:
        read_artifact = _default_artifact_reader()

    art = read_artifact(op_toolpaths_artifact_id)
    art_d: Dict[str, Any] = art if isinstance(art, dict) else {
        "artifact_id": getattr(art, "artifact_id", None) or getattr(art, "id", None),
        "kind": getattr(art, "kind", None),
        "status": getattr(art, "status", None),
        "payload": getattr(art, "payload", None),
    }

    kind = art_d.get("kind", "")
    if kind != "saw_batch_op_toolpaths":
        raise ValueError(f"Expected kind='saw_batch_op_toolpaths', got '{kind}'")

    payload = art_d.get("payload") or {}
    if not isinstance(payload, dict):
        payload = {}

    op_id = payload.get("op_id", "unknown")
    status = art_d.get("status", "UNKNOWN")
    toolpaths = payload.get("toolpaths") or {}
    moves = toolpaths.get("moves") or []

    if not moves:
        return {
            "gcode": f"( No toolpaths generated for op {op_id} )\n( Status: {status} )\n",
            "filename": f"{op_id}.ngc",
            "op_id": op_id,
            "status": status,
            "has_toolpaths": False,
        }

    gcode = emit_gcode_from_moves(moves)
    return {
        "gcode": gcode,
        "filename": f"{op_id}.ngc",
        "op_id": op_id,
        "status": status,
        "has_toolpaths": True,
    }


def export_execution_gcode(
    *,
    batch_execution_artifact_id: str,
    read_artifact: Optional[ArtifactReader] = None,
) -> Dict[str, Any]:
    """
    Export combined G-code for all OK ops in an execution.

    Each op gets full header and ends with spindle stop + retract.
    Only final op gets M30.

    Args:
        batch_execution_artifact_id: The execution artifact ID
        read_artifact: Optional artifact reader callable (defaults to RMOS)

    Returns:
        {
            "gcode": str,
            "filename": str,
            "batch_label": str,
            "op_count": int,
            "ok_count": int,
            "blocked_count": int,
        }
    """
    if read_artifact is None:
        read_artifact = _default_artifact_reader()

    parent = read_artifact(batch_execution_artifact_id)
    parent_d: Dict[str, Any] = parent if isinstance(parent, dict) else {
        "artifact_id": getattr(parent, "artifact_id", None) or getattr(parent, "id", None),
        "kind": getattr(parent, "kind", None),
        "status": getattr(parent, "status", None),
        "payload": getattr(parent, "payload", None),
        "index_meta": getattr(parent, "index_meta", None),
    }

    kind = parent_d.get("kind", "")
    if kind != "saw_batch_execution":
        raise ValueError(f"Expected kind='saw_batch_execution', got '{kind}'")

    payload = parent_d.get("payload") or {}
    if not isinstance(payload, dict):
        payload = {}

    meta = parent_d.get("index_meta") or {}
    if not isinstance(meta, dict):
        meta = {}

    batch_label = payload.get("batch_label") or meta.get("batch_label") or "batch"
    children = payload.get("children") or []
    results = payload.get("results") or []
    summary = payload.get("summary") or {}

    # Build header comment
    header_lines = [
        f"( Batch: {batch_label} )",
        f"( Execution: {batch_execution_artifact_id} )",
        f"( Ops: {summary.get('ok_count', 0)} OK, {summary.get('blocked_count', 0)} BLOCKED )",
        "",
    ]

    # Collect OK ops' G-code
    op_gcode_blocks: List[str] = []
    ok_count = 0
    blocked_count = 0

    for child in children:
        child_id = child.get("artifact_id") if isinstance(child, dict) else None
        if not child_id:
            continue

        try:
            result = export_op_toolpaths_gcode(op_toolpaths_artifact_id=child_id, read_artifact=read_artifact)
        except Exception:
            continue

        if not result.get("has_toolpaths"):
            blocked_count += 1
            continue

        ok_count += 1
        op_id = result.get("op_id", "unknown")
        op_gcode = result.get("gcode", "")

        # Remove M30 from all but the last op (we'll add it at the end)
        op_lines = op_gcode.split("\n")
        op_lines = [ln for ln in op_lines if not ln.strip().startswith("M30")]

        block = [
            f"( ========== Op: {op_id} ========== )",
            "\n".join(op_lines),
            "",
        ]
        op_gcode_blocks.append("\n".join(block))

    # Combine all blocks
    if not op_gcode_blocks:
        combined = "\n".join(header_lines) + "\n( No OK operations to export )\n"
    else:
        combined = "\n".join(header_lines) + "\n".join(op_gcode_blocks) + "\nM30  (Program end)\n"

    # Sanitize filename
    safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in batch_label)
    filename = f"{safe_label}_{batch_execution_artifact_id[:8]}.ngc"

    return {
        "gcode": combined,
        "filename": filename,
        "batch_label": batch_label,
        "op_count": len(children),
        "ok_count": ok_count,
        "blocked_count": blocked_count,
    }
