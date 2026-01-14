# services/api/app/ai_context_adapter/assembler/default.py
"""
Default envelope assembler for AI context.

Builds a complete toolbox_ai_context_envelope_v1 from:
- Run data
- Design intent
- Artifact counts and recent list
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from ..providers.run_summary import get_run_summary
from ..providers.design_intent import get_design_intent_summary
from ..redactor.strict import redact_strict


def utc_now_iso() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def build_context_envelope(
    *,
    repo: str,
    commit: str,
    environment: str,
    context_id: str,
    run: Dict[str, Any],
    design_intent: Dict[str, Any],
    artifacts_counts: Dict[str, int],
    recent_artifacts: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build a complete AI context envelope.

    Args:
        repo: Repository name (e.g., "luthiers-toolbox")
        commit: Git commit hash (at least 7 chars)
        environment: One of "dev", "ci", "prod"
        context_id: Stable identifier for this context snapshot
        run: Run data dict (will be sanitized)
        design_intent: Design intent dict (will be sanitized)
        artifacts_counts: Dict with advisories, candidates, executions counts
        recent_artifacts: List of recent artifact dicts

    Returns:
        Schema-valid, redacted envelope dict
    """
    # Build raw envelope
    raw = {
        "schema_id": "toolbox_ai_context_envelope",
        "schema_version": "v1",
        "created_at_utc": utc_now_iso(),
        "context_id": context_id,
        "source": {
            "system": "toolbox",
            "repo": repo[:256],
            "commit": commit[:80],
            "environment": environment if environment in ("dev", "ci", "prod") else "dev",
        },
        "capabilities": {
            "allow_sensitive_manufacturing": False,  # Hard-locked
            "allow_pii": False,  # Hard-locked
            "allow_audio_raw": False,
        },
        "redaction": {
            "mode": "strict",
            "ruleset": "toolbox_ai_redaction_strict_v1",
            "warnings": [],
        },
        "payload": {
            "run_summary": get_run_summary(run),
            "design_intent": get_design_intent_summary(design_intent),
            "artifacts": {
                "counts": {
                    "advisories": int(artifacts_counts.get("advisories", 0)),
                    "candidates": int(artifacts_counts.get("candidates", 0)),
                    "executions": int(artifacts_counts.get("executions", 0)),
                },
                "recent": [
                    {
                        "kind": str(a.get("kind", ""))[:64],
                        "id": str(a.get("id", ""))[:128],
                        "created_at_utc": str(a.get("created_at_utc", utc_now_iso())),
                        "summary": str(a.get("summary", ""))[:2000],
                    }
                    for a in recent_artifacts[:50]
                ],
            },
        },
    }

    # Enforce strict redaction (belt + suspenders)
    result = redact_strict(raw)
    return result.redacted
