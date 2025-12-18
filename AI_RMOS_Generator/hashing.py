"""
RMOS Runs v2 Hashing Utilities

Deterministic hashing for run artifacts and payloads.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional


def sha256_text(text: Optional[str]) -> Optional[str]:
    """Hash text content with SHA256."""
    if text is None:
        return None
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def sha256_json(obj: Any) -> str:
    """
    Hash JSON-serializable object with deterministic ordering.
    
    GOVERNANCE: Used to generate feasibility_sha256 (REQUIRED field).
    """
    if obj is None:
        raise ValueError("Cannot hash None - feasibility_sha256 is REQUIRED")
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Hash raw bytes with SHA256."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    """Hash file contents with SHA256."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_hash(expected: str, actual: str) -> bool:
    """Verify two hashes match (constant-time comparison)."""
    import hmac
    return hmac.compare_digest(expected.lower(), actual.lower())


def summarize_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produce a small, redaction-friendly summary for audit/logging.
    """
    if not isinstance(request, dict):
        return {"type": str(type(request)), "note": "non-dict request"}

    keys = list(request.keys())
    summary: Dict[str, Any] = {"keys": keys[:50]}

    design = request.get("design")
    ctx = request.get("context") or request.get("ctx")

    if isinstance(design, dict):
        summary["design_keys"] = list(design.keys())[:50]
    if isinstance(ctx, dict):
        summary["context_keys"] = list(ctx.keys())[:50]
        if "model_id" in ctx:
            summary["model_id"] = ctx.get("model_id")
        if "feasibility_engine_id" in ctx:
            summary["feasibility_engine_id"] = ctx.get("feasibility_engine_id")

    return summary
