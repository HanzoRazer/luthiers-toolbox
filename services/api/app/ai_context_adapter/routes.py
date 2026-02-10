# services/api/app/ai_context_adapter/routes.py
"""AI Context Adapter API Routes"""

from __future__ import annotations

import os
import re
import subprocess
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, HTTPException, Query

from .schemas import AiContextBuildRequest, AiContextBuildResponse

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
    """Check for forbidden manufacturing content. Returns violations."""
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
    """Enforce hard boundary rule. Raises HTTPException if violations found."""
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
    except (OSError, ValueError):  # WP-1: narrowed from except Exception
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
    except (KeyError, TypeError, AttributeError, ValueError):  # WP-1: narrowed from except Exception
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
    except (KeyError, TypeError, AttributeError, ValueError):  # WP-1: narrowed from except Exception
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
    """Get AI context envelope for a run."""
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


# Allowlisted includes (explicit opt-in)
ALLOWED_INCLUDES: Set[str] = {
    "rosette_param_spec",
    "manufacturing_candidates",
    "run_summary",
    "design_intent",
    "governance_notes",
    "docs_excerpt",
    "ui_state_hint",
    "diff_summary",
    "artifact_manifest",
}

# Supported modes
ALLOWED_MODES: Set[str] = {"run_first", "art_studio_first"}


def _build_run_summary(run_id: str) -> Dict[str, Any]:
    """Build run summary context (no manufacturing secrets)."""
    run = _fetch_run(run_id)
    if not run:
        return {"status": "not_found", "run_id": run_id}
    return run


def _build_design_intent(pattern_id: str) -> Dict[str, Any]:
    """Build design intent context."""
    return _fetch_design_intent(pattern_id)


def _build_rosette_param_spec(snapshot_id: Optional[str]) -> Dict[str, Any]:
    """Build rosette parameter spec context."""
    if not snapshot_id:
        return {
            "status": "rosette_snapshot_unbound",
            "note": "Provide snapshot_id to fetch rosette params. Art Studio UI knows this value.",
        }

    try:
        from app.art_studio.services.rosette_snapshot_store import RosetteSnapshotStore

        store = RosetteSnapshotStore()
        snapshot = store.get(snapshot_id)
        if snapshot:
            # Extract only design-safe parameters from snapshot.design (RosetteParamSpec)
            design = getattr(snapshot, "design", None)
            result = {
                "status": "ok",
                "snapshot_id": snapshot_id,
                "design_fingerprint": getattr(snapshot, "design_fingerprint", None),
                "created_at_utc": getattr(snapshot, "created_at_utc", None),
                "run_id": getattr(snapshot, "run_id", None),  # if bound
            }
            if design:
                # Safe design params only - NO machining/toolpath params
                result["design"] = {
                    "pattern_type": getattr(design, "pattern_type", "unknown"),
                    "ring_count": getattr(design, "ring_count", None),
                    "outer_diameter_mm": getattr(design, "outer_diameter_mm", None),
                    "material": getattr(design, "material", None),
                }
            return result
    except ImportError:
        return {"status": "store_unavailable", "snapshot_id": snapshot_id}
    except (KeyError, TypeError, AttributeError, ValueError) as e:  # WP-1: narrowed from except Exception
        return {"status": "error", "snapshot_id": snapshot_id, "error": str(e)[:100]}

    return {"status": "not_found", "snapshot_id": snapshot_id}


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


def _build_diff_summary(run_id: str, compare_run_id: Optional[str] = None) -> Dict[str, Any]:
    """Build diff summary context (safe text only, no manufacturing data)."""
    if not compare_run_id:
        return {
            "status": "no_comparison",
            "summary": "No comparison run specified.",
            "note": "Provide compare_run_id to compute diff.",
        }

    try:
        from app.rmos.runs_v2.store import get_run
        from app.rmos.runs_v2.diff import diff_runs, diff_summary

        run_a = get_run(run_id)
        run_b = get_run(compare_run_id)

        if not run_a or not run_b:
            return {
                "status": "run_not_found",
                "summary": f"One or both runs not found: {run_id}, {compare_run_id}",
            }

        diff_result = diff_runs(run_a, run_b)
        summary_text = diff_summary(diff_result)

        return {
            "status": "ok",
            "summary": summary_text,
            "severity": diff_result.get("diff_severity", "INFO"),
            "changed_count": len(diff_result.get("changed_paths", [])),
            # Note: raw diff detail excluded - only safe summary text
        }
    except ImportError:
        return {"status": "unavailable", "summary": "Diff engine not available."}
    except (KeyError, TypeError, AttributeError, ValueError) as e:  # WP-1: narrowed from except Exception
        return {"status": "error", "summary": str(e)[:200]}


def _build_artifact_manifest(run_id: str) -> Dict[str, Any]:
    """
    Build artifact manifest (metadata only, NO bytes, NO toolpaths/gcode content).

    Returns list of artifacts with: artifact_id, kind, sha256, bytes (size), mime, filename, created_utc.
    """
    try:
        from app.rmos.runs_v2.store import get_run

        run = get_run(run_id)
        if not run:
            return {"status": "not_found", "run_id": run_id, "artifact_count": 0, "artifacts": []}

        attachments = getattr(run, "attachments", None) or []
        manifest = []

        for att in attachments:
            # Only include metadata, never actual content
            entry = {
                "kind": getattr(att, "kind", "unknown"),
                "sha256": getattr(att, "sha256", None),
                "size_bytes": getattr(att, "size_bytes", 0),
                "mime": getattr(att, "mime", "application/octet-stream"),
                "filename": getattr(att, "filename", ""),
                "created_at_utc": str(getattr(att, "created_at_utc", "")),
            }
            manifest.append(entry)

        return {
            "status": "ok",
            "run_id": run_id,
            "artifact_count": len(manifest),
            "artifacts": manifest,
            # Note: NO raw bytes, NO toolpath/gcode content
        }
    except ImportError:
        return {"status": "unavailable", "run_id": run_id, "artifact_count": 0, "artifacts": []}
    except (KeyError, TypeError, AttributeError, ValueError) as e:  # WP-1: narrowed from except Exception
        return {"status": "error", "run_id": run_id, "artifact_count": 0, "error": str(e)[:200], "artifacts": []}


@router.post("/build", response_model=AiContextBuildResponse)
def build_context(payload: AiContextBuildRequest) -> AiContextBuildResponse:
    """Build a bounded AI context bundle."""
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
        # snapshot_id preferred, pattern_id as deprecated fallback
        sid = payload.snapshot_id or payload.pattern_id
        context["rosette_param_spec"] = _build_rosette_param_spec(sid)

    if "manufacturing_candidates" in allowed:
        context["manufacturing_candidates"] = _build_manufacturing_candidates(payload.run_id)

    if "governance_notes" in allowed:
        context["governance_notes"] = _build_governance_notes()

    # Art-studio-first mode includes
    if "diff_summary" in allowed and payload.run_id:
        context["diff_summary"] = _build_diff_summary(payload.run_id, payload.compare_run_id)

    if "artifact_manifest" in allowed and payload.run_id:
        context["artifact_manifest"] = _build_artifact_manifest(payload.run_id)

    # Include user notes (kept separate for fencing)
    if payload.user_notes:
        context["user_notes"] = payload.user_notes

    # Add metadata
    context["_meta"] = {
        "run_id": payload.run_id,
        "pattern_id": payload.pattern_id,
        "compare_run_id": payload.compare_run_id,
        "mode": payload.mode,
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
