# services/api/app/ai_context_adapter/routes.py
"""
AI Context Adapter API Routes

Endpoints:
- GET /api/ai/context?run_id=... (envelope for existing run)
- GET /api/ai/context/health (health check)
- POST /api/ai/context/build (bounded context assembly)

This is the ONLY interface AI systems should use to get ToolBox context.

HARD BOUNDARY RULE: Context payloads must NEVER contain:
- toolpaths (manufacturing execution paths)
- gcode (machine instructions)
- sensitive manufacturing parameters

Contract: toolbox_ai_context_envelope_v1
"""

from __future__ import annotations

import os
import re
import subprocess
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from .assembler.default import build_context_envelope

router = APIRouter(
    prefix="/api/ai/context",
    tags=["AI Context"],
)

# Feature flag for context adapter
_AI_CONTEXT_ENABLED = os.getenv("AI_CONTEXT_ENABLED", "true").lower() == "true"

# =============================================================================
# HARD BOUNDARY RULES - Manufacturing Secrets Fence
# =============================================================================

# Keys that must NEVER appear in any context payload
FORBIDDEN_KEYS: Set[str] = {
    "toolpaths",
    "toolpath",
    "gcode",
    "g_code",
    "gcode_text",
    "gcode_path",
    "nc_program",
    "machine_instructions",
}

# Patterns that indicate manufacturing secrets in values
FORBIDDEN_PATTERNS: List[re.Pattern] = [
    re.compile(r"G[012][0-9]", re.IGNORECASE),  # G-code commands
    re.compile(r"M[0-9]{1,2}", re.IGNORECASE),  # M-codes
    re.compile(r"X-?\d+\.?\d*\s*Y-?\d+\.?\d*", re.IGNORECASE),  # Coordinates
]


def _contains_forbidden_content(obj: Any, path: str = "") -> List[str]:
    """
    Recursively check for forbidden manufacturing content.

    Returns list of violations found.
    """
    violations: List[str] = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            key_lower = key.lower()
            if key_lower in FORBIDDEN_KEYS:
                violations.append(f"Forbidden key '{key}' at {path or 'root'}")
            violations.extend(_contains_forbidden_content(value, f"{path}.{key}" if path else key))

    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            violations.extend(_contains_forbidden_content(item, f"{path}[{i}]"))

    elif isinstance(obj, str):
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.search(obj):
                violations.append(f"Forbidden pattern '{pattern.pattern}' found at {path}")
                break

    return violations


def enforce_boundary_gate(context: Dict[str, Any]) -> None:
    """
    Enforce hard boundary rule: no manufacturing secrets in context.

    Raises HTTPException if violations found.
    """
    violations = _contains_forbidden_content(context)
    if violations:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "boundary_violation",
                "message": "Context contains forbidden manufacturing content",
                "violations": violations[:10],  # Limit to first 10
            },
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


# =============================================================================
# POST /build - Bounded Context Assembly
# =============================================================================

class AiContextBuildRequest(BaseModel):
    """Request to build a bounded AI context bundle."""
    # Identify what the user is working on
    run_id: Optional[str] = Field(None, description="RMOS run ID")
    pattern_id: Optional[str] = Field(None, description="Pattern/design ID")

    # What the UI wants to include (explicit allowlist)
    include: List[str] = Field(
        default_factory=list,
        description="What to include: rosette_param_spec, manufacturing_candidates, run_summary, design_intent, governance_notes",
    )

    # Optional UI-provided notes (kept separate so we can fence it)
    user_notes: Optional[str] = Field(None, description="User-provided notes for context")


class AiContextBuildResponse(BaseModel):
    """Response with bounded AI context bundle."""
    schema_id: str = Field(default="toolbox_ai_context", description="Schema identifier")
    schema_version: str = Field(default="v1", description="Schema version")
    context_id: str = Field(..., description="Unique context bundle ID")
    summary: str = Field(..., description="Human-readable summary of what's included")
    context: Dict[str, Any] = Field(default_factory=dict, description="The bounded context payload")
    warnings: List[str] = Field(default_factory=list, description="Warnings about missing or stubbed data")


# Allowlisted includes (explicit opt-in)
ALLOWED_INCLUDES: Set[str] = {
    "rosette_param_spec",
    "manufacturing_candidates",
    "run_summary",
    "design_intent",
    "governance_notes",
    "docs_excerpt",
    "ui_state_hint",
}


def _build_run_summary(run_id: str) -> Dict[str, Any]:
    """Build run summary context (no manufacturing secrets)."""
    run = _fetch_run(run_id)
    if not run:
        return {"status": "not_found", "run_id": run_id}
    return run


def _build_design_intent(pattern_id: str) -> Dict[str, Any]:
    """Build design intent context."""
    return _fetch_design_intent(pattern_id)


def _build_rosette_param_spec(pattern_id: Optional[str]) -> Dict[str, Any]:
    """
    Build rosette parameter spec context.

    Does NOT include manufacturing parameters - only design parameters.
    """
    if not pattern_id:
        return {"status": "no_pattern_id", "note": "Provide pattern_id to fetch rosette params"}

    try:
        from app.art_studio.services.rosette_snapshot_store import RosetteSnapshotStore

        store = RosetteSnapshotStore()
        snapshot = store.get(pattern_id)
        if snapshot:
            # Extract only design-safe parameters
            return {
                "status": "ok",
                "pattern_id": pattern_id,
                "pattern_type": getattr(snapshot, "pattern_type", "unknown"),
                "ring_count": getattr(snapshot, "ring_count", None),
                "target_diameter_mm": getattr(snapshot, "target_diameter_mm", None),
                "material_type": getattr(snapshot, "material_type", None),
                # Note: NO toolpaths, NO gcode, NO machining params
            }
    except ImportError:
        pass
    except Exception:
        pass

    return {"status": "not_found", "pattern_id": pattern_id}


def _build_manufacturing_candidates(run_id: Optional[str]) -> Dict[str, Any]:
    """
    Build manufacturing candidates summary (counts only, no details).

    Returns counts of candidates by status, not the actual candidate data.
    """
    if not run_id:
        return {"status": "no_run_id", "note": "Provide run_id to fetch candidates"}

    counts, recent = _fetch_artifacts_summary(run_id)

    # Return only aggregate info, no actual manufacturing data
    return {
        "status": "ok",
        "run_id": run_id,
        "counts": counts,
        "recent_count": len(recent),
        # Note: actual candidate details are NOT included
    }


def _build_governance_notes(intent: str = "") -> Dict[str, Any]:
    """Build governance notes for common topics."""
    return {
        "status": "ok",
        "topics": [
            {"topic": "feasibility", "summary": "Feasibility checks ensure safe manufacturing parameters."},
            {"topic": "boundary", "summary": "Boundary validation prevents tool crashes."},
            {"topic": "export_blocked", "summary": "Export blocked when run not in approved state."},
        ],
        "note": "Wire to full governance_notes provider for detailed explanations.",
    }


@router.post("/build", response_model=AiContextBuildResponse)
def build_context(payload: AiContextBuildRequest) -> AiContextBuildResponse:
    """
    Build a bounded AI context bundle.

    This endpoint assembles context from ToolBox state based on explicit includes.
    It does NOT call any AI provider - it only prepares context for later AI consumption.

    **HARD BOUNDARY RULE**: Context will NEVER contain toolpaths, G-code, or
    sensitive manufacturing execution data. The boundary gate enforces this.

    Use this endpoint to gather context before making an AI call.
    """
    if not _AI_CONTEXT_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="AI context adapter disabled by AI_CONTEXT_ENABLED=false",
        )

    warnings: List[str] = []
    context: Dict[str, Any] = {}

    # Filter to allowed includes only
    requested = set(payload.include)
    unknown = requested - ALLOWED_INCLUDES
    if unknown:
        warnings.append(f"Unknown includes ignored: {', '.join(unknown)}")

    allowed = requested & ALLOWED_INCLUDES

    # Build requested context sections
    if "run_summary" in allowed and payload.run_id:
        context["run_summary"] = _build_run_summary(payload.run_id)

    if "design_intent" in allowed and payload.pattern_id:
        context["design_intent"] = _build_design_intent(payload.pattern_id)

    if "rosette_param_spec" in allowed:
        context["rosette_param_spec"] = _build_rosette_param_spec(payload.pattern_id)

    if "manufacturing_candidates" in allowed:
        context["manufacturing_candidates"] = _build_manufacturing_candidates(payload.run_id)

    if "governance_notes" in allowed:
        context["governance_notes"] = _build_governance_notes()

    # Include user notes (kept separate for fencing)
    if payload.user_notes:
        context["user_notes"] = payload.user_notes

    # Add metadata
    context["_meta"] = {
        "run_id": payload.run_id,
        "pattern_id": payload.pattern_id,
        "includes_requested": list(allowed),
        "environment": _get_environment(),
        "commit": _get_git_commit(),
    }

    # ==========================================================================
    # CRITICAL: Enforce hard boundary gate before returning
    # ==========================================================================
    enforce_boundary_gate(context)

    # Build context ID
    context_id = f"ctx:{payload.run_id or 'none'}:{payload.pattern_id or 'none'}:{len(context)}"

    # Add standard warnings
    if not context.get("run_summary") and not context.get("design_intent"):
        warnings.append("No run_id or pattern_id provided - context is minimal.")
    warnings.append("Manufacturing secrets (toolpaths/G-code) are excluded by design.")

    return AiContextBuildResponse(
        schema_id="toolbox_ai_context",
        schema_version="v1",
        context_id=context_id,
        summary="Bounded ToolBox context bundle for AI consumption (no manufacturing secrets).",
        context=context,
        warnings=warnings,
    )
