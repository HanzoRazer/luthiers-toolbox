from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Optional


def sha256_text(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    b = text.encode("utf-8", errors="replace")
    return hashlib.sha256(b).hexdigest()


def sha256_json(obj: Any) -> str:
    # Stable, deterministic JSON hashing (sorted keys)
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256_text(s) or ""


def sha256_toolpaths_payload(payload: Any) -> str:
    # Alias to sha256_json for now; specialize later if needed
    return sha256_json(payload)


def summarize_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produce a small, redaction-friendly summary for audit/logging.
    Conservative by default; expand later as request schema stabilizes.
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
