# services/api/app/ai_context_adapter/providers/design_intent.py
"""Design intent provider for AI context envelope."""

from __future__ import annotations

from typing import Any, Dict, List


ALLOWED_DOMAINS = frozenset({"rosette", "inlay", "unknown"})


def get_design_intent_summary(intent: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract schema-compatible design_intent from intent data.

    This is intentionally NOT raw geometry.
    It is a redacted narrative summary + optional IDs.

    Input: intent dict with domain, summary, optional spec_refs
    Output: schema-compatible design_intent object
    """
    # Normalize domain
    domain = intent.get("domain") or "unknown"
    if domain not in ALLOWED_DOMAINS:
        domain = "unknown"

    # Extract summary (required)
    summary = str(intent.get("summary") or "").strip()
    if not summary:
        summary = "No design intent summary available."

    # Extract spec_refs (optional, IDs only)
    spec_refs = intent.get("spec_refs") or []
    if not isinstance(spec_refs, list):
        spec_refs = []

    # Sanitize spec_refs - only strings, limited length
    clean_refs: List[str] = []
    for ref in spec_refs[:50]:
        if isinstance(ref, str):
            clean_refs.append(ref[:256])
        else:
            clean_refs.append(str(ref)[:256])

    return {
        "domain": domain,
        "summary": summary[:12000],
        "spec_refs": clean_refs,
    }
