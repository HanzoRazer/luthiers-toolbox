# services/api/app/ai_context_adapter/routes.py
"""
AI Context Adapter API Routes

Single endpoint that emits the toolbox_ai_context_envelope_v1.

GET /api/ai/context?run_id=...

This is the ONLY interface AI systems should use to get ToolBox context.
"""

from __future__ import annotations

import os
import subprocess
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query

from .assembler.default import build_context_envelope

router = APIRouter(
    prefix="/api/ai/context",
    tags=["AI Context"],
)


def _get_git_commit() -> str:
    """Get current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short=8", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip() or "unknown"
    except Exception:
        pass
    return "unknown"


def _get_environment() -> str:
    """Determine current environment."""
    env = os.getenv("TOOLBOX_ENV", os.getenv("ENVIRONMENT", "dev"))
    if env in ("prod", "production"):
        return "prod"
    if env in ("ci", "test", "testing"):
        return "ci"
    return "dev"


def _fetch_run(run_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch run data from RMOS runs store.

    Returns None if run not found.
    """
    try:
        from app.rmos.runs_v2.store import load_run

        run = load_run(run_id)
        if run:
            return {
                "run_id": run.run_id,
                "status": run.status,
                "event_type": getattr(run, "event_type", "unknown"),
                "created_at_utc": run.created_at.isoformat() if run.created_at else None,
                "notes": getattr(run, "notes", ""),
            }
    except ImportError:
        pass
    except Exception:
        pass

    return None


def _fetch_design_intent(run_id: str) -> Dict[str, Any]:
    """
    Extract design intent from run artifacts or metadata.

    Returns a safe default if not available.
    """
    # For now, return unknown - can be enhanced to extract from artifacts
    return {
        "domain": "unknown",
        "summary": "No design intent summary available.",
        "spec_refs": [],
    }


def _fetch_artifacts_summary(run_id: str) -> tuple[Dict[str, int], list[Dict[str, Any]]]:
    """
    Fetch artifact counts and recent artifacts for a run.

    Returns (counts_dict, recent_list).
    """
    counts = {"advisories": 0, "candidates": 0, "executions": 0}
    recent: list[Dict[str, Any]] = []

    try:
        from app.rmos.runs_v2.store import list_artifacts

        artifacts = list_artifacts(run_id)
        for art in artifacts[:50]:
            kind = getattr(art, "kind", "unknown")
            if "advisory" in kind.lower():
                counts["advisories"] += 1
            elif "candidate" in kind.lower():
                counts["candidates"] += 1
            elif "execution" in kind.lower():
                counts["executions"] += 1

            recent.append({
                "kind": kind,
                "id": getattr(art, "artifact_id", ""),
                "created_at_utc": getattr(art, "created_at", ""),
                "summary": getattr(art, "summary", ""),
            })
    except ImportError:
        pass
    except Exception:
        pass

    return counts, recent


@router.get("/health")
def health() -> Dict[str, Any]:
    """Health check for AI context endpoint."""
    return {
        "status": "ok",
        "schema_version": "v1",
        "environment": _get_environment(),
    }


@router.get("")
def get_context(
    run_id: str = Query(..., min_length=6, max_length=128, description="Run ID to get context for"),
) -> Dict[str, Any]:
    """
    Get AI context envelope for a run.

    Returns a schema-valid toolbox_ai_context_envelope_v1.
    All sensitive data is redacted.

    This is the ONLY interface AI systems should use.
    """
    # Fetch run data
    run = _fetch_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run_not_found")

    # Fetch design intent
    design_intent = _fetch_design_intent(run_id)

    # Fetch artifacts summary
    counts, recent = _fetch_artifacts_summary(run_id)

    # Build envelope
    envelope = build_context_envelope(
        repo="luthiers-toolbox",
        commit=_get_git_commit(),
        environment=_get_environment(),
        context_id=f"ctx_{run_id}",
        run=run,
        design_intent=design_intent,
        artifacts_counts=counts,
        recent_artifacts=recent,
    )

    return envelope
