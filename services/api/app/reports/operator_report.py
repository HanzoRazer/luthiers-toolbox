# Patch N14.x - Operator Report Skeleton
#
# Builds a Markdown operator checklist for a single rosette CNC export.
# Uses CNCExportBundle + CNCSimulationResult metadata.
#
# Later bundles will:
#   - Render this Markdown into a PDF
#   - Attach job_id / pattern_id more deeply
#   - Add signature / timestamp blocks

from __future__ import annotations

from datetime import datetime
from typing import Optional

from ..cam.rosette.cnc import CNCExportBundle, CNCSimulationResult


def build_operator_markdown_report(
    job_id: Optional[str],
    export_bundle: CNCExportBundle,
    simulation: CNCSimulationResult,
    pattern_id: Optional[str] = None,
) -> str:
    """
    Construct a Markdown operator report for a per-ring CNC export.

    The structure is intentionally simple and deterministic so that
    later we can convert it to PDF or other formats.

    Args:
        job_id: JobLog ID for traceability
        export_bundle: CNC export bundle with toolpaths, safety, metadata
        simulation: Simulation results with runtime estimates
        pattern_id: Optional pattern identifier

    Returns:
        Markdown-formatted operator checklist

    Example:
        report = build_operator_markdown_report(
            job_id="JOB-ROSETTE-20251201-123456-abc123",
            export_bundle=bundle,
            simulation=sim_result,
            pattern_id="rosette_001"
        )
    """
    ring_id = export_bundle.ring_id
    meta = export_bundle.metadata or {}
    origin = meta.get("origin", {})
    safety = meta.get("safety_decision", {})
    seg_count = meta.get("segment_count", len(export_bundle.toolpaths.segments))

    ts = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    safety_decision = safety.get("decision", export_bundle.safety_decision.decision)
    safety_risk = safety.get("risk_level", export_bundle.safety_decision.risk_level)
    safety_override = safety.get(
        "requires_override",
        export_bundle.safety_decision.requires_override,
    )
    safety_reasons = safety.get("reasons", export_bundle.safety_decision.reasons)

    # Basic runtime display
    runtime_sec = simulation.estimated_runtime_sec
    runtime_min = runtime_sec / 60.0 if runtime_sec > 0 else 0.0

    # Markdown body
    lines: list[str] = []

    lines.append(f"# RMOS Studio – Operator Checklist (Ring {ring_id})")
    lines.append("")
    lines.append(f"- **Generated at:** {ts}")
    if job_id:
        lines.append(f"- **Job ID:** `{job_id}`")
    if pattern_id:
        lines.append(f"- **Pattern ID:** `{pattern_id}`")
    lines.append(f"- **Ring ID:** `{ring_id}`")
    lines.append("")
    lines.append("## 1. Setup Summary")
    lines.append("")
    lines.append("- **Machine Origin (mm):** "
                 f"X = {origin.get('origin_x_mm', 0.0):.2f}, "
                 f"Y = {origin.get('origin_y_mm', 0.0):.2f}")
    lines.append(f"- **Jig Rotation (deg):** {origin.get('rotation_deg', 0.0):.1f}")
    lines.append(f"- **Toolpath segments:** {seg_count}")
    lines.append("")
    lines.append("## 2. Safety Status")
    lines.append("")
    lines.append(f"- **Decision:** `{safety_decision}`")
    lines.append(f"- **Risk level:** `{safety_risk}`")
    lines.append(f"- **Override required:** `{bool(safety_override)}`")
    if safety_reasons:
        lines.append("")
        lines.append("**Safety Notes:**")
        for reason in safety_reasons:
            lines.append(f"- {reason}")
    else:
        lines.append("")
        lines.append("_No safety notes recorded._")

    lines.append("")
    lines.append("## 3. Runtime Estimate")
    lines.append("")
    lines.append(f"- **Estimated runtime:** {runtime_sec:.1f} seconds "
                 f"({runtime_min:.2f} minutes)")
    lines.append(f"- **Passes:** {simulation.passes}")
    lines.append(f"- **Max feed:** {simulation.max_feed_mm_per_min:.0f} mm/min")
    lines.append(f"- **Envelope OK:** `{simulation.envelope_ok}`")

    lines.append("")
    lines.append("## 4. Pre-Run Checklist")
    lines.append("")
    lines.append("- [ ] Verify correct **material** and **thickness** are loaded")
    lines.append("- [ ] Confirm **jig alignment** (origin & rotation) matches setup")
    lines.append("- [ ] Confirm **blade/bit selection** and condition")
    lines.append("- [ ] Check **workholding / clamping** is secure")
    lines.append("- [ ] Verify **dust collection** is active (if required)")
    lines.append("- [ ] Perform **dry run / air cut** if risk level is above LOW")

    lines.append("")
    lines.append("## 5. Post-Run Notes")
    lines.append("")
    lines.append("> Operator comments:")
    lines.append("> ")
    lines.append("> ")

    return "\n".join(lines)
