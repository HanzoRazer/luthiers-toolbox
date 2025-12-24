"""
RMOS Art Studio Binding Service - Bundle RMOS_BIND_ART_STUDIO_CANDIDATE_V1

Authority gate that binds Art Studio candidate attachments (SVG/spec) into a
RunArtifact with ALLOW/BLOCK, GREEN/YELLOW/RED, feasibility_sha256, and attachments[].

Mints artifact via validate_and_persist (or persist_run for HEAD compatibility).
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from .attachments import (
    get_bytes_attachment,
    get_attachment_path,
    load_json_attachment,
    verify_attachment,
)
from .schemas import RunAttachment
from .hashing import sha256_of_text, sha256_of_obj

ENGINE_VERSION = "rmos.bind_art_studio_candidate.v1"

# Required candidate parts (strict mode)
REQUIRED_KINDS = {"geometry_svg", "geometry_spec_json"}


def _bytes_to_utf8(b: bytes) -> str:
    """Decode bytes to UTF-8 string."""
    return b.decode("utf-8", errors="strict")


def _infer_kind_from_filename(filename: str) -> Optional[str]:
    """Infer attachment kind from filename extension."""
    f = (filename or "").lower()
    if f.endswith(".svg"):
        return "geometry_svg"
    if f.endswith(".json"):
        return "geometry_spec_json"
    return None


def _risk_from_svg(svg_text: str) -> Tuple[str, str, float, Optional[str]]:
    """
    Returns: (decision, risk_level, score, reason)

    decision: "ALLOW" | "BLOCK"
    risk_level: "GREEN" | "YELLOW" | "RED"
    score: 0.0-1.0 (higher = better)
    reason: short machine-readable tag (None if ok)

    Policy:
    - BLOCK: <script>, <foreignObject>, <image> (security risks)
    - ALLOW+YELLOW: <text> (manufacturing risk - fonts need outlining)
    - ALLOW: <path> and all geometry elements (expected in rosettes)
    """
    lower = (svg_text or "").lower()

    # Hard security blocks (bind-time)
    if "<script" in lower:
        return ("BLOCK", "RED", 0.0, "svg_script")
    if "foreignobject" in lower:
        return ("BLOCK", "RED", 0.0, "svg_foreignobject")
    if "<image" in lower:
        return ("BLOCK", "RED", 0.10, "svg_image_embed")

    # <text> is allowed but flagged YELLOW (manufacturing risk: fonts need outlining)
    if "<text" in lower:
        return ("ALLOW", "YELLOW", 0.75, "svg_text_requires_outline")

    # All geometry elements are expected and allowed
    # <path>, <circle>, <rect>, <line>, <polygon>, <polyline> are all fine
    return ("ALLOW", "GREEN", 1.0, None)


def _normalize_run_attachment(meta: Dict[str, Any], sha256: str) -> RunAttachment:
    """
    Normalize attachment metadata dict into RunAttachment.

    verify_attachment(sha256) returns a dict. We normalize into RunAttachment.
    Expected fields: sha256, kind, mime, filename, size_bytes, created_at_utc
    """
    # Handle 'mime' vs 'mime_type' variations
    mime = meta.get("mime") or meta.get("mime_type") or "application/octet-stream"
    kind = meta.get("kind") or _infer_kind_from_filename(meta.get("filename", "") or "") or "unknown"
    filename = meta.get("filename") or f"{sha256}"
    size_bytes = int(meta.get("size_bytes") or meta.get("size") or 0)
    created_at_utc = meta.get("created_at_utc") or meta.get("created_at") or ""

    return RunAttachment(
        sha256=sha256,
        kind=kind,
        mime=mime,
        filename=filename,
        size_bytes=size_bytes,
        created_at_utc=created_at_utc,
    )


def bind_art_studio_candidate(
    *,
    run_id: str,
    attachment_ids: List[str],
    operator_notes: Optional[str],
    strict: bool,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    RMOS authority binding:
    - Loads attachments by sha256 from CAS
    - Verifies integrity
    - Evaluates feasibility/risk deterministically
    - Returns binding result (caller persists the RunArtifact)
    - Persists BLOCKED artifacts too (200 + decision=BLOCK), except invalid requests (400 upstream)

    Args:
        run_id: The run to bind to
        attachment_ids: List of attachment IDs (sha256 or att-{sha256} format)
        operator_notes: Optional operator notes
        strict: If true, fail when required candidate components are missing
        request_id: Optional request ID for tracing

    Returns:
        Dict with decision, risk_level, score, attachments, feasibility_sha256, etc.

    Raises:
        ValueError: For missing attachments (strict mode) or integrity failures
    """
    req_id = request_id or "unknown"

    # Normalize + verify attachments, build RunAttachment list
    attachments: List[RunAttachment] = []
    kind_to_sha: Dict[str, str] = {}
    attachment_sha_map: Dict[str, str] = {}

    for att_id in attachment_ids:
        # Normalize: strip att- prefix if present
        sha = att_id.replace("att-", "") if att_id.startswith("att-") else att_id
        attachment_sha_map[att_id] = sha

        # Check attachment exists
        path = get_attachment_path(sha)
        if path is None:
            if strict:
                raise ValueError(f"Attachment not found in CAS: {att_id} (sha256: {sha})")
            continue

        # Verify integrity and get metadata
        meta = verify_attachment(sha)
        if not meta.get("ok", False):
            raise ValueError(f"Attachment integrity check failed: {sha} - {meta.get('error')}")

        ra = _normalize_run_attachment(meta, sha)
        attachments.append(ra)

        # Track required kinds
        k = ra.kind
        if k in REQUIRED_KINDS and k not in kind_to_sha:
            kind_to_sha[k] = sha

    if strict:
        missing = [k for k in REQUIRED_KINDS if k not in kind_to_sha]
        if missing:
            raise ValueError(f"Missing required candidate attachments: {missing}")

    # Load SVG + spec json (best-effort if not strict)
    svg_text: Optional[str] = None
    spec_json_obj: Optional[Dict[str, Any]] = None

    svg_sha = kind_to_sha.get("geometry_svg")
    if svg_sha:
        b = get_bytes_attachment(svg_sha)
        if b is None:
            raise ValueError(f"Attachment not found in CAS: {svg_sha}")
        svg_text = _bytes_to_utf8(b)

    spec_sha = kind_to_sha.get("geometry_spec_json")
    if spec_sha:
        spec_json_obj = load_json_attachment(spec_sha)
        if spec_json_obj is None:
            # If JSON loader can't load, treat as invalid request (fail-closed)
            raise ValueError(f"Spec JSON attachment could not be loaded: {spec_sha}")

    # Evaluate risk
    if not svg_text:
        decision, risk_level, score, reason = ("BLOCK", "ERROR", 0.0, "missing_svg")
    else:
        decision, risk_level, score, reason = _risk_from_svg(svg_text)

    # Deterministic feasibility hash (inputs + result + engine version)
    feasibility_payload = {
        "engine_version": ENGINE_VERSION,
        "request_id": req_id,
        "run_id": run_id,
        "inputs": {
            "svg_sha256": svg_sha,
            "spec_sha256": spec_sha,
        },
        "result": {
            "decision": decision,
            "risk_level": risk_level,
            "feasibility_score": score,
            "reason": reason,
        },
    }
    feasibility_sha256 = sha256_of_text(json.dumps(feasibility_payload, sort_keys=True))

    return {
        "decision": decision,
        "risk_level": risk_level,
        "feasibility_score": score,
        "feasibility_sha256": feasibility_sha256,
        "attachments": attachments,
        "attachment_sha256_map": attachment_sha_map,
        "engine_version": ENGINE_VERSION,
        "reason": reason,
        "operator_notes": operator_notes,
    }
