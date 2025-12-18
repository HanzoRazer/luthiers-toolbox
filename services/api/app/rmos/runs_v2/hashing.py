"""
RMOS Hashing Utilities v2

Deterministic hashing for run artifacts and payloads.
Critical for replay, drift detection, and audit verification.

Contract Compliance: RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Optional


def stable_json_dumps(obj: Any) -> str:
    """
    Produce deterministic JSON string.

    MANDATORY per governance contract:
    - Sorted keys alphabetically
    - Compact separators (",", ":")
    - UTF-8 encoding
    - ensure_ascii=False for Unicode
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def sha256_of_obj(obj: Any) -> str:
    """
    Compute SHA256 hash of a JSON-serializable object.

    Uses stable_json_dumps for deterministic serialization.
    """
    s = stable_json_dumps(obj)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha256_of_text(text: str) -> str:
    """Compute SHA256 hash of text content."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_of_text_safe(text: Optional[str]) -> Optional[str]:
    """
    SHA256 with null handling - returns None if input is None.

    Useful for optional fields where absence should be distinct from empty.
    """
    if text is None:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_of_bytes(data: bytes) -> str:
    """Compute SHA256 hash of binary data."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str) -> str:
    """
    Compute SHA256 hash of a file.

    Reads in chunks to handle large files efficiently.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def summarize_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produce a redaction-friendly request summary for audit logging.

    MANDATORY per governance contract:
    - Client feasibility MUST be stripped
    - Extracts key structure and identifiers without sensitive payloads
    - Limits exposure while preserving auditability

    Args:
        request: The full request dict to summarize

    Returns:
        Summary dict with keys, context identifiers, but no full payloads
    """
    if not isinstance(request, dict):
        return {"type": str(type(request)), "note": "non-dict request"}

    # Start with top-level keys (limited to 50)
    keys = list(request.keys())
    summary: Dict[str, Any] = {"keys": keys[:50]}

    # CRITICAL: Never include client feasibility
    if "feasibility" in keys:
        summary["note"] = "client_feasibility_stripped"

    # Extract design structure (keys only, no values)
    design = request.get("design")
    if isinstance(design, dict):
        summary["design_keys"] = list(design.keys())[:50]

    # Extract context identifiers (safe for audit)
    ctx = request.get("context") or request.get("ctx")
    if isinstance(ctx, dict):
        summary["context_keys"] = list(ctx.keys())[:50]
        # Preserve safe identifiers for audit correlation
        safe_keys = ["model_id", "feasibility_engine_id", "tool_id", "material_id", "machine_id"]
        for key in safe_keys:
            if key in ctx:
                summary[key] = ctx.get(key)

    return summary


def compute_feasibility_hash(feasibility: Dict[str, Any]) -> str:
    """
    Compute the canonical feasibility hash.

    This is the REQUIRED feasibility_sha256 field per governance contract.
    """
    return sha256_of_obj(feasibility)
