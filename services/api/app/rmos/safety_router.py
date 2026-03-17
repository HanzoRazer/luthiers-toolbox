"""
RMOS Safety Router

Safety evaluation endpoints using real RMOS feasibility engine.
Extracted from stub_routes.py during decomposition.
"""

from __future__ import annotations

import os
import secrets
from datetime import datetime, timezone, timedelta
from typing import Any, Dict

from fastapi import APIRouter

from .feasibility.engine import compute_feasibility
from .feasibility.schemas import FeasibilityInput, MaterialHardness


router = APIRouter(tags=["rmos", "safety"])


# In-memory token store (ephemeral - cleared on restart)
_override_tokens: Dict[str, Dict[str, Any]] = {}


def _parse_feasibility_input(payload: Dict[str, Any]) -> FeasibilityInput:
    """Parse payload into FeasibilityInput with sensible defaults."""

    hardness = payload.get("material_hardness")
    if hardness and isinstance(hardness, str):
        try:
            hardness = MaterialHardness(hardness.lower())
        except ValueError:
            hardness = None

    return FeasibilityInput(
        pipeline_id=payload.get("pipeline_id", "safety_evaluate_v1"),
        post_id=payload.get("post_id", "GRBL"),
        units=payload.get("units", "mm"),
        tool_d=float(payload.get("tool_diameter_mm", payload.get("tool_d", 6.0))),
        stepover=float(payload.get("stepover_percent", payload.get("stepover", 40.0))) / 100.0,
        stepdown=float(payload.get("depth_of_cut_mm", payload.get("stepdown", 3.0))),
        z_rough=float(payload.get("z_rough", payload.get("final_depth_mm", -10.0))),
        feed_xy=float(payload.get("feed_xy_mm_min", payload.get("feed_xy", 1000.0))),
        feed_z=float(payload.get("feed_z_mm_min", payload.get("feed_z", 200.0))),
        rapid=float(payload.get("rapid", 3000.0)),
        safe_z=float(payload.get("safe_z", 5.0)),
        strategy=payload.get("strategy", payload.get("operation", "profile")),
        layer_name=payload.get("layer_name", "0"),
        climb=payload.get("climb", True),
        smoothing=float(payload.get("smoothing", 0.0)),
        margin=float(payload.get("margin", 0.0)),
        has_closed_paths=payload.get("has_closed_paths"),
        loop_count_hint=payload.get("loop_count_hint"),
        entity_count=payload.get("entity_count"),
        bbox=payload.get("bbox"),
        material_id=payload.get("material", payload.get("material_id")),
        material_hardness=hardness,
        material_thickness_mm=payload.get("material_thickness_mm"),
        material_resinous=payload.get("material_resinous"),
        geometry_width_mm=payload.get("geometry_width_mm"),
        geometry_depth_mm=payload.get("geometry_depth_mm"),
        wall_thickness_mm=payload.get("wall_thickness_mm"),
        tool_flute_length_mm=payload.get("tool_flute_length_mm"),
        tool_stickout_mm=payload.get("tool_stickout_mm"),
        coolant_enabled=payload.get("coolant_enabled"),
    )


@router.post("/safety/evaluate")
def evaluate_safety(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Evaluate safety constraints using real RMOS feasibility engine."""
    if payload is None:
        payload = {}

    try:
        fi = _parse_feasibility_input(payload)
        result = compute_feasibility(fi)

        decision = "BLOCK" if result.blocking else "ALLOW"

        return {
            "ok": True,
            "decision": decision,
            "risk_level": result.risk_level.value,
            "warnings": result.warnings,
            "blocks": result.blocking_reasons,
            "rules_triggered": result.rules_triggered,
            "engine_version": result.engine_version,
        }
    except (ValueError, TypeError, KeyError, AttributeError) as e:
        return {
            "ok": False,
            "decision": "ERROR",
            "risk_level": "UNKNOWN",
            "warnings": [],
            "blocks": [str(e)],
            "error": str(e),
        }


@router.get("/safety/mode")
def get_safety_mode() -> Dict[str, Any]:
    """Get current safety mode settings from environment."""
    mode = os.environ.get("RMOS_SAFETY_MODE", "standard")
    strict = os.environ.get("RMOS_STRICT_MODE", "false").lower() in ("1", "true", "yes")
    allow_overrides = os.environ.get("RMOS_ALLOW_OVERRIDES", "true").lower() in ("1", "true", "yes")
    allow_red_override = os.environ.get("RMOS_ALLOW_RED_OVERRIDE", "false").lower() in ("1", "true", "yes")

    return {
        "mode": mode,
        "strict_mode": strict,
        "allow_overrides": allow_overrides,
        "allow_red_override": allow_red_override,
    }


def _generate_token() -> str:
    """Generate a short, human-readable override token."""
    return secrets.token_hex(4).upper()


def _clean_expired_tokens() -> None:
    """Remove expired tokens from store."""
    now = datetime.now(timezone.utc)
    expired = []
    for token, data in _override_tokens.items():
        try:
            expires = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
            if expires < now:
                expired.append(token)
        except (ValueError, KeyError):
            expired.append(token)
    for token in expired:
        del _override_tokens[token]


@router.post("/safety/create-override")
def create_safety_override(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create a one-time override token for apprenticeship mode.

    Mentors generate these tokens for apprentices to bypass safety checks
    on specific actions. Tokens are single-use and time-limited.
    """
    if payload is None:
        payload = {}

    _clean_expired_tokens()

    action = payload.get("action", "unknown_action")
    created_by = payload.get("created_by") or "anonymous"
    ttl_minutes = int(payload.get("ttl_minutes", 15))
    ttl_minutes = max(1, min(120, ttl_minutes))

    token = _generate_token()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
    expires_at_str = expires_at.strftime("%Y-%m-%dT%H:%M:%SZ")

    _override_tokens[token] = {
        "action": action,
        "created_by": created_by,
        "expires_at": expires_at_str,
        "used": False,
    }

    return {
        "token": token,
        "action": action,
        "created_by": created_by,
        "expires_at": expires_at_str,
    }
