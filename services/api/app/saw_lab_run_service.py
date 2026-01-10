from __future__ import annotations

from typing import Any, Dict, List, Optional


def plan_saw_toolpaths_for_design(
    *,
    spec_payload: Dict[str, Any],
    plan_payload: Dict[str, Any],
    selected_setup_key: str,
    selected_op_ids: List[str],
    context: Dict[str, Any],
    include_gcode: bool = True,
) -> Dict[str, Any]:
    """
    Single choke point for saw toolpath generation (Saw Lab internal).
    RMOS must never import saw_lab; saw_lab services call into this.

    This function can evolve as the Saw Lab planner/builder matures.
    """
    # Lazy imports to avoid circular dependencies
    from app.saw_lab.toolpath_builder import SawToolpathBuilder
    from app.saw_lab.models import SawContext

    # Convert plan/spec into segments. If you already have a segment adapter elsewhere,
    # route it here so it stays centralized.
    try:
        from app.saw_lab.path_planner import build_segments_from_plan  # type: ignore

        segments = build_segments_from_plan(
            spec_payload=spec_payload,
            plan_payload=plan_payload,
            selected_setup_key=selected_setup_key,
            selected_op_ids=selected_op_ids,
        )
    except (ImportError, AttributeError):
        # Fallback: build minimal segments from spec items
        segments = _build_fallback_segments(spec_payload, plan_payload, selected_setup_key, selected_op_ids)

    saw_ctx = SawContext(
        kerf_width_mm=float(context.get("kerf_width", context.get("kerf_width_mm", 2.0))),
        stock_thickness_mm=float(context.get("stock_thickness", context.get("stock_thickness_mm", 25.0))),
        feed_rate_mm_per_min=float(context.get("feed_rate", context.get("feed_rate_mm_per_min", 500.0))),
        max_rpm=int(context.get("spindle_rpm", context.get("max_rpm", 3000))),
    )

    builder = SawToolpathBuilder()
    plan = builder.build(segments, saw_ctx)

    out: Dict[str, Any] = {
        "moves": [m.model_dump() if hasattr(m, "model_dump") else m.__dict__ for m in plan.moves],
        "statistics": {
            "total_length_mm": plan.total_length_mm,
            "cut_count": plan.cut_count,
            "move_count": len(plan.moves),
        },
    }
    if include_gcode:
        # If your builder already has to_gcode(), use it.
        if hasattr(builder, "to_gcode"):
            out["gcode_text"] = builder.to_gcode(plan, saw_ctx)  # type: ignore
        else:
            # Minimal fallback (kept deterministic)
            g = []
            g.append("G21 ; Units: mm")
            g.append("G90 ; Absolute positioning")
            g.append("G17 ; XY plane selection")
            g.append(f"S{saw_ctx.max_rpm} ; Spindle speed: {saw_ctx.max_rpm} RPM")
            g.append("M3 ; Spindle on CW")
            g.append(f"G0 Z{saw_ctx.safe_z_mm} ; Move to safe height")
            for mv in plan.moves:
                mt = getattr(mv, "move_type", None)
                x = float(getattr(mv, "x", 0.0))
                y = float(getattr(mv, "y", 0.0))
                z = float(getattr(mv, "z", 0.0))
                cmt = getattr(mv, "comment", "") or ""
                if mt == "rapid":
                    g.append(f"G0 X{x:.3f} Y{y:.3f} Z{z:.3f} ; {cmt}")
                else:
                    f = float(getattr(mv, "feed_rate", saw_ctx.feed_rate_mm_per_min))
                    g.append(f"G1 X{x:.3f} Y{y:.3f} Z{z:.3f} F{f:.1f} ; {cmt}")
            g.append(f"G0 Z{saw_ctx.safe_z_mm} ; Final retract to safe height")
            g.append("M5 ; Spindle off")
            g.append("M30 ; Program end")
            out["gcode_text"] = "\n".join(g)
    return out


def _build_fallback_segments(
    spec_payload: Dict[str, Any],
    plan_payload: Dict[str, Any],
    selected_setup_key: str,
    selected_op_ids: List[str],
) -> List[Any]:
    """
    Fallback segment builder when path_planner.build_segments_from_plan is not available.
    Returns minimal segment objects for toolpath building.
    """
    from app.saw_lab.models import SawSegment  # type: ignore
    
    segments = []
    items = spec_payload.get("items", [])
    
    # Find the selected setup in plan
    setups = plan_payload.get("setups", [])
    selected_ops = []
    for setup in setups:
        if setup.get("setup_key") == selected_setup_key:
            selected_ops = [op for op in setup.get("ops", []) if op.get("op_id") in selected_op_ids]
            break
    
    # Build segments from selected ops
    y_offset = 0.0
    for op in selected_ops:
        part_id = op.get("part_id", "")
        # Find matching item in spec
        item = next((i for i in items if i.get("part_id") == part_id), None)
        if item:
            length_mm = float(item.get("length_mm", 300.0))
            width_mm = float(item.get("width_mm", 30.0))
            try:
                seg = SawSegment(
                    start_x=0.0,
                    start_y=y_offset,
                    end_x=length_mm,
                    end_y=y_offset,
                    cut_type=op.get("cut_type", "crosscut"),
                )
                segments.append(seg)
            except Exception:
                # If SawSegment doesn't exist, create a simple dict
                segments.append({
                    "start_x": 0.0,
                    "start_y": y_offset,
                    "end_x": length_mm,
                    "end_y": y_offset,
                    "cut_type": op.get("cut_type", "crosscut"),
                })
            y_offset += width_mm + 10.0  # Spacing between cuts
    
    return segments
