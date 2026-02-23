# services/api/app/routers/pipeline_helpers.py
"""Pipeline helper functions for building requests and processing responses."""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from .pipeline_context import PipelineContext


def build_plan_request(
    ctx: PipelineContext, params: Dict[str, Any], mp: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Build adaptive plan request payload."""
    plan_req = {
        "loops": [{"pts": loop.pts} for loop in ctx.loops],
        "units": params.get("units", ctx.units),
        "tool_d": float(params.get("tool_d", ctx.tool_d)),
        "stepover": float(params.get("stepover", 0.45)),
        "stepdown": float(params.get("stepdown", 2.0)),
        "margin": float(params.get("margin", 0.5)),
        "strategy": params.get("strategy", "Spiral"),
        "smoothing": float(params.get("smoothing", 0.5)),
        "climb": bool(params.get("climb", True)),
        "feed_xy": float(params.get("feed_xy", mp.get("max_feed_xy") if mp else 1200)),
        "safe_z": float(
            params.get("safe_z", mp.get("safe_z_default") if mp and "safe_z_default" in mp else 5.0)
        ),
        "z_rough": float(params.get("z_rough", -1.5)),
    }

    # Apply machine profile defaults
    if mp:
        for key, mp_key in [
            ("machine_profile_id", "id"),
            ("machine_feed_xy", "max_feed_xy"),
            ("machine_rapid", "rapid"),
            ("machine_accel", "accel"),
            ("machine_jerk", "jerk"),
        ]:
            plan_req.setdefault(key, mp.get(mp_key))

    # Optional numeric params
    for key in ("corner_radius_min", "target_stepover", "slowdown_feed_pct"):
        if key in params:
            plan_req[key] = float(params[key])

    # Trochoid params
    if "use_trochoids" in params:
        plan_req["use_trochoids"] = bool(params["use_trochoids"])
    for key in ("trochoid_radius", "trochoid_pitch"):
        if key in params:
            plan_req[key] = float(params[key])

    return plan_req


def moves_to_gcode(moves: List[Dict[str, Any]]) -> str:
    """Convert move list to G-code string."""
    lines = []
    for move in moves:
        parts = [move.get("code", "G0")]
        if "x" in move:
            parts.append(f"X{move['x']:.4f}")
        if "y" in move:
            parts.append(f"Y{move['y']:.4f}")
        if "z" in move:
            parts.append(f"Z{move['z']:.4f}")
        if "f" in move:
            parts.append(f"F{move['f']:.1f}")
        lines.append(" ".join(parts))
    return "\n".join(lines)


def load_post_config(post_id: str) -> Dict[str, Any]:
    """Load post-processor configuration file."""
    post_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data",
        "posts",
        f"{post_id.lower()}.json",
    )
    if not os.path.exists(post_file):
        raise HTTPException(status_code=404, detail=f"Post-processor '{post_id}' not found")

    with open(post_file, "r") as f:
        return json.load(f)


def apply_post_profile(post_config: Dict[str, Any], pp: Optional[Dict[str, Any]]) -> None:
    """Apply post profile overrides to config."""
    if not pp:
        return
    if "post" in pp:
        post_config["dialect"] = pp["post"]
    if "header" in pp:
        post_config["header"] = pp["header"]
    if "footer" in pp:
        post_config["footer"] = pp["footer"]


def build_posted_gcode(
    raw_gcode: str, post_config: Dict[str, Any], post_id: str, units: str
) -> tuple:
    """Build final posted G-code with header/footer."""
    lines = []
    lines.append("G21" if units == "mm" else "G20")

    if "header" in post_config:
        lines.extend(post_config["header"])

    lines.append(f"(POST={post_id};UNITS={units};DATE={datetime.utcnow().isoformat()})")
    lines.append(raw_gcode)

    if "footer" in post_config:
        lines.extend(post_config["footer"])

    return "\n".join(lines), len(lines)


def build_sim_request(
    params: Dict[str, Any], mp: Optional[Dict[str, Any]], gcode: str
) -> Dict[str, Any]:
    """Build simulation request payload."""
    body = {
        "gcode": gcode,
        "accel": float(params.get("accel", mp.get("accel") if mp else 800)),
        "clearance_z": float(
            params.get("safe_z", mp.get("safe_z_default") if mp and "safe_z_default" in mp else 5.0)
        ),
        "as_csv": False,
    }

    if mp:
        if "feed_xy" not in params and "max_feed_xy" in mp:
            body["feed_xy"] = mp["max_feed_xy"]
        if "feed_z" not in params and "max_feed_z" in mp:
            body["feed_z"] = mp["max_feed_z"]
        if "rapid" not in params and "rapid" in mp:
            body["rapid"] = mp["rapid"]

    return body
