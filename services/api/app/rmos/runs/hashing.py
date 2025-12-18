"""
RMOS Hashing Utilities

Provides deterministic hashing for run artifacts and payloads.
Critical for replay and drift detection.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Optional


def stable_json_dumps(obj: Any) -> str:
    """
    Produce deterministic JSON string.
    
    - Sorted keys
    - Compact separators
    - UTF-8 encoding
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_of_obj(obj: Any) -> str:
    """Compute SHA256 hash of a JSON-serializable object."""
    s = stable_json_dumps(obj)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha256_of_text(text: str) -> str:
    """Compute SHA256 hash of text content."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_of_bytes(data: bytes) -> str:
    """Compute SHA256 hash of binary data."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# --- NEW FUNCTIONS FROM GAP ANALYSIS ---

def sha256_of_text_safe(text: Optional[str]) -> Optional[str]:
    """
    SHA256 with null handling - returns None if input is None.

    Useful for optional fields where absence should be distinct from empty.
    """
    if text is None:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def summarize_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produce a redaction-friendly request summary for audit logging.

    Extracts key structure and identifiers without sensitive payloads.
    Limits exposure while preserving auditability.

    Args:
        request: The full request dict to summarize

    Returns:
        Summary dict with keys, context identifiers, but no full payloads
    """
    if not isinstance(request, dict):
        return {"type": str(type(request)), "note": "non-dict request"}

    keys = list(request.keys())
    summary: Dict[str, Any] = {"keys": keys[:50]}

    # Extract design structure
    design = request.get("design")
    if isinstance(design, dict):
        summary["design_keys"] = list(design.keys())[:50]

    # Extract context identifiers
    ctx = request.get("context") or request.get("ctx")
    if isinstance(ctx, dict):
        summary["context_keys"] = list(ctx.keys())[:50]
        # Preserve safe identifiers for audit correlation
        if "model_id" in ctx:
            summary["model_id"] = ctx.get("model_id")
        if "feasibility_engine_id" in ctx:
            summary["feasibility_engine_id"] = ctx.get("feasibility_engine_id")
        if "tool_id" in ctx:
            summary["tool_id"] = ctx.get("tool_id")
        if "material_id" in ctx:
            summary["material_id"] = ctx.get("material_id")

    return summary
