"""
CAM Metrics Router

Energy and heat analysis endpoints for M.3 Energy & Heat Model.

Migrated from: routers/cam_metrics_router.py

Architecture Layer: ROUTER (Layer 6)
See: docs/governance/ARCHITECTURE_INVARIANTS.md

Endpoints:
    POST /energy                - Calculate cutting energy and heat distribution
    POST /energy_csv            - Export per-segment energy breakdown as CSV
    POST /heat_timeseries       - Calculate heat generation over time
    POST /bottleneck_csv        - Export bottleneck data as CSV
    POST /thermal_report_md     - Generate thermal report as Markdown
    POST /thermal_report_bundle - Export thermal report as ZIP bundle
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from zipfile import ZipFile

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ...energy_model import energy_breakdown
from ...heat_timeseries import heat_timeseries
from ....routers.machine_router import get_profile
from ....routers.material_router import get_material
from ....util.names import safe_stem

router = APIRouter()


class EnergyIn(BaseModel):
    """Request body for energy analysis."""
    moves: List[Dict[str, Any]] = Field(..., description="Toolpath moves from /plan endpoint")
    material_id: str = Field(default="maple_hard", description="Material ID from material database")
    tool_d: float = Field(..., description="Tool diameter in mm")
    stepover: float = Field(..., description="Stepover ratio (0..1)")
    stepdown: float = Field(..., description="Depth per pass in mm")
    job_name: Optional[str] = Field(default=None, description="Optional job identifier")


@router.post("/energy")
def energy(body: EnergyIn) -> Dict[str, Any]:
    """
    Calculate cutting energy and heat distribution for a toolpath.

    Args:
        body: EnergyIn with moves, material_id, tool parameters

    Returns:
        {
            "material": material_id,
            "job_name": job_name or null,
            "totals": {
                "volume_mm3": float,
                "energy_j": float,
                "heat": {"chip_j": float, "tool_j": float, "work_j": float}
            },
            "segments": [
                {"idx": int, "code": str, "len_mm": float, "vol_mm3": float, "energy_j": float}
            ]
        }

    Raises:
        HTTPException: 404 if material not found
    """
    # Get material properties
    mat = get_material(body.material_id)

    # Calculate energy breakdown
    out = energy_breakdown(
        moves=body.moves,
        sce_j_per_mm3=float(mat["sce_j_per_mm3"]),
        tool_d_mm=float(body.tool_d),
        stepover=float(body.stepover),
        stepdown=float(body.stepdown),
        heat_partition=mat.get("heat_partition", {"chip": 0.7, "tool": 0.2, "work": 0.1})
    )

    # Add metadata
    out["material"] = mat["id"]
    out["job_name"] = body.job_name

    return out


@router.post("/energy_csv")
def energy_csv(body: EnergyIn) -> StreamingResponse:
    """
    Export per-segment energy breakdown as CSV.

    Args:
        body: EnergyIn with moves, material_id, tool parameters

    Returns:
        CSV file with columns: idx, code, len_mm, vol_mm3, energy_j, cum_energy_j
    """
    # Get material properties
    mat = get_material(body.material_id)

    # Calculate energy breakdown
    out = energy_breakdown(
        moves=body.moves,
        sce_j_per_mm3=float(mat["sce_j_per_mm3"]),
        tool_d_mm=float(body.tool_d),
        stepover=float(body.stepover),
        stepdown=float(body.stepdown),
        heat_partition=mat.get("heat_partition", {"chip": 0.7, "tool": 0.2, "work": 0.1})
    )

    # Generate safe filename stem
    stem = safe_stem(body.job_name, prefix="energy")

    # Build CSV in memory
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["idx", "code", "len_mm", "vol_mm3", "energy_j", "cum_energy_j"])

    cumulative = 0.0
    for seg in out["segments"]:
        cumulative += float(seg["energy_j"])
        w.writerow([
            seg["idx"],
            seg.get("code", ""),
            f'{seg.get("len_mm", 0):.4f}',
            f'{seg["vol_mm3"]:.4f}',
            f'{seg["energy_j"]:.4f}',
            f'{cumulative:.4f}'
        ])

    # Convert to bytes for streaming
    data = io.BytesIO(buf.getvalue().encode("utf-8"))

    return StreamingResponse(
        iter([data.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{stem}.csv"'}
    )


# ========== Heat Timeseries ==========

class HeatIn(BaseModel):
    """Input for heat timeseries: power (J/s) over time."""
    moves: List[Dict[str, Any]]
    machine_profile_id: str
    material_id: str = "maple_hard"
    tool_d: float
    stepover: float
    stepdown: float
    bins: int = Field(default=120, ge=10, le=2000)


@router.post("/heat_timeseries")
def heat_ts(body: HeatIn) -> Dict[str, Any]:
    """
    Calculate heat generation over time: power (J/s) in chip, tool, work.

    Response:
    {
      "t": [0.0, 0.5, 1.0, ...],        // time axis (s)
      "p_chip": [12.3, 15.6, ...],      // chip power (J/s)
      "p_tool": [3.5, 4.5, ...],        // tool power (J/s)
      "p_work": [1.8, 2.2, ...],        // work power (J/s)
      "total_s": 120.5,                 // total time (s)
      "material": "maple_hard",
      "machine_profile_id": "default"
    }
    """
    mat = get_material(body.material_id)
    prof = get_profile(body.machine_profile_id)

    out = heat_timeseries(
        body.moves, prof,
        tool_d_mm=float(body.tool_d),
        stepover=float(body.stepover),
        stepdown=float(body.stepdown),
        sce_j_per_mm3=float(mat["sce_j_per_mm3"]),
        heat_partition=mat.get("heat_partition", {"chip": 0.7, "tool": 0.2, "work": 0.1}),
        bins=int(body.bins)
    )

    out["material"] = mat["id"]
    out["machine_profile_id"] = body.machine_profile_id
    return out


# ========== Bottleneck CSV Export ==========

class BottleneckCsvIn(BaseModel):
    """Input for bottleneck CSV export."""
    moves: List[Dict[str, Any]]
    machine_profile_id: str
    job_name: str = "pocket"


@router.post("/bottleneck_csv")
def bottleneck_csv_export(body: BottleneckCsvIn) -> StreamingResponse:
    """
    Export per-segment bottleneck data as CSV.

    Columns: idx, code, x, y, len_mm, limit
    limit: "feed_cap", "accel", "jerk", "none"
    """
    prof = get_profile(body.machine_profile_id)

    # Safe filename
    stem = f"bottleneck_{safe_stem(body.job_name)}"

    # Generate CSV
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["idx", "code", "x", "y", "len_mm", "limit"])

    for i, m in enumerate(body.moves):
        code = m.get("code", "")
        x = m.get("x", "")
        y = m.get("y", "")

        # Calculate length and determine limit
        len_mm = 0.0
        limit = "none"

        if code in ("G1", "G2", "G3"):
            # Get previous position
            prev_x = body.moves[i-1].get("x", 0.0) if i > 0 else 0.0
            prev_y = body.moves[i-1].get("y", 0.0) if i > 0 else 0.0

            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                dx = float(x) - float(prev_x)
                dy = float(y) - float(prev_y)
                len_mm = (dx*dx + dy*dy)**0.5

                # Determine bottleneck (simplified from M.1.1 logic)
                if len_mm > 0:
                    feed_f = m.get("f", 0.0)
                    feed_cap = prof.get("feed_xy", 1200.0)
                    accel = prof.get("accel", 500.0)
                    jerk = prof.get("jerk", 1000.0)

                    # Check feed cap
                    if feed_f >= feed_cap * 0.95:
                        limit = "feed_cap"
                    # Check if accel-limited (short move)
                    elif len_mm < (feed_f/60.0)**2 / (2*accel):
                        limit = "accel"
                    # Check if jerk-limited (very short move)
                    elif len_mm < (feed_f/60.0)**3 / (jerk * accel):
                        limit = "jerk"

        w.writerow([
            str(i),
            code,
            f'{x:.4f}' if isinstance(x, (int, float)) else "",
            f'{y:.4f}' if isinstance(y, (int, float)) else "",
            f'{len_mm:.4f}',
            limit
        ])

    # Convert to bytes for streaming
    data = io.BytesIO(buf.getvalue().encode("utf-8"))

    return StreamingResponse(
        iter([data.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{stem}.csv"'}
    )


# ========== Thermal Report (Markdown) ==========

_SPARK = "▁▂▃▄▅▆▇█"


def _sparkline(values: List[float], width: int = 60) -> str:
    """Generate ASCII sparkline from values."""
    if not values:
        return ""
    # Downsample to `width` and normalize 0..1
    if len(values) > width:
        step = len(values) / width
        vals = [values[int(i*step)] for i in range(width)]
    else:
        vals = values[:]
    vmax = max(vals) or 1.0
    return "".join(_SPARK[min(7, int((v / vmax) * 7))] for v in vals)


class ThermalBudget(BaseModel):
    """Budget limits for chip/tool/work heat in Joules."""
    chip_j: float = 500.0
    tool_j: float = 150.0
    work_j: float = 100.0


class ThermalReportIn(BaseModel):
    """Input for thermal report generation."""
    moves: List[Dict[str, Any]]
    machine_profile_id: str = "Mach4_Router_4x8"
    material_id: str = "maple_hard"
    tool_d: float
    stepover: float          # 0..1
    stepdown: float
    bins: int = Field(default=200, ge=10, le=5000)
    job_name: Optional[str] = None
    budgets: ThermalBudget = ThermalBudget()
    include_csv_links: bool = False  # Include CSV download commands in footer


@router.post("/thermal_report_md")
def thermal_report_md(body: ThermalReportIn) -> StreamingResponse:
    """
    Generate comprehensive thermal report as Markdown with:
    - Job context (machine, material, tool)
    - Energy totals and heat partition
    - Budget compliance (OK/WARN/OVER)
    - ASCII sparklines for power over time
    - Bottleneck distribution

    Downloads as: thermal_report_{job_name}.md
    """
    # Lookups
    mat = get_material(body.material_id)
    prof = get_profile(body.machine_profile_id)

    # Energy & heat totals
    energy_data = energy_breakdown(
        moves=body.moves,
        sce_j_per_mm3=float(mat["sce_j_per_mm3"]),
        tool_d_mm=float(body.tool_d),
        stepover=float(body.stepover),
        stepdown=float(body.stepdown),
        heat_partition=mat.get("heat_partition", {"chip": 0.7, "tool": 0.2, "work": 0.1})
    )

    # Heat time-series
    ts = heat_timeseries(
        moves=body.moves, profile=prof,
        tool_d_mm=float(body.tool_d), stepover=float(body.stepover), stepdown=float(body.stepdown),
        sce_j_per_mm3=float(mat["sce_j_per_mm3"]),
        heat_partition=mat.get("heat_partition", {"chip": 0.7, "tool": 0.2, "work": 0.1}),
        bins=int(body.bins)
    )

    # Budgets
    bj = body.budgets
    use = energy_data["totals"]["heat"]

    def _state(val: float, lim: float) -> str:
        if val <= lim*0.85:
            return "OK"
        if val <= lim:
            return "WARN"
        return "OVER"

    chip_state = _state(use["chip_j"], bj.chip_j)
    tool_state = _state(use["tool_j"], bj.tool_j)
    work_state = _state(use["work_j"], bj.work_j)

    # Sparklines
    spark_chip = _sparkline(ts["p_chip"], width=60)
    spark_tool = _sparkline(ts["p_tool"], width=60)
    spark_work = _sparkline(ts["p_work"], width=60)

    # Optional bottlenecks from moves
    caps: Dict[str, int] = {"feed_cap": 0, "accel": 0, "jerk": 0, "none": 0}
    for m in body.moves:
        lim = m.get("meta", {}).get("limit")
        if lim in caps:
            caps[lim] += 1

    # Compose Markdown
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")
    stem = safe_stem(body.job_name or "thermal_report")
    md = io.StringIO()
    w = md.write

    w(f"# Thermal Report — {body.job_name or 'Untitled Job'}\n\n")
    w(f"_Generated: {now}_\n\n")
    w("## Context\n")
    w(f"- **Machine**: `{body.machine_profile_id}`  \n")
    w(f"- **Material**: `{mat['title']}` (`{mat['id']}`)  \n")
    w(f"- **Tool Ø**: {body.tool_d:.3f} mm  \n")
    w(f"- **Step-over**: {(body.stepover*100):.1f}%  \n")
    w(f"- **Step-down**: {body.stepdown:.3f} mm  \n")
    w(f"- **Bins**: {body.bins}  \n\n")

    w("## Totals\n")
    w(f"- **Volume removed**: {energy_data['totals']['volume_mm3']:.0f} mm³  \n")
    w(f"- **Total energy**: {energy_data['totals']['energy_j']:.1f} J  \n")
    w(f"- **Time (est.)**: {ts['total_s']:.1f} s  \n\n")

    w("### Heat partition\n")
    w("| Sink | Joules | Budget | Status |\n")
    w("|---|---:|---:|:--:|\n")
    w(f"| Chip | {use['chip_j']:.1f} | {bj.chip_j:.1f} | {chip_state} |\n")
    w(f"| Tool | {use['tool_j']:.1f} | {bj.tool_j:.1f} | {tool_state} |\n")
    w(f"| Work | {use['work_j']:.1f} | {bj.work_j:.1f} | {work_state} |\n\n")

    w("## Power (J/s) sparklines\n")
    w("```\n")
    w(f"Chip: {spark_chip}\n")
    w(f"Tool: {spark_tool}\n")
    w(f"Work: {spark_work}\n")
    w("```\n\n")

    w("## Bottleneck share (counts)\n")
    w(f"- feed_cap: {caps['feed_cap']}, accel: {caps['accel']}, jerk: {caps['jerk']}, none: {caps['none']}\n\n")

    w("> Notes: Sparklines are ASCII summaries of power over normalized time. Use the CSV exports for exact values.\n")

    # --- OPTIONAL FOOTER WITH CSV LINKS ---
    if body.include_csv_links:
        # Predict filenames (server uses these stems in CSV endpoints)
        energy_stem = safe_stem(body.job_name, prefix="energy")
        heat_stem = safe_stem(body.job_name, prefix="heat_ts")
        bott_stem = safe_stem(body.job_name, prefix="bottlenecks")

        w("\n---\n\n")
        w("## CSV Downloads\n")
        w("Set `$API` to your canonical base URL, e.g. `http://127.0.0.1:8000/api`.\n\n")
        w("The following commands will download CSVs generated with the same inputs as this report.\n\n")
        w("**Energy per segment** → `")
        w(f"{energy_stem}.csv")
        w("`\n\n")
        w("```bash\n")
        w("curl -X POST $API/cam/metrics/energy_csv \\\n")
        w("  -H 'Content-Type: application/json' \\\n")
        w("  -d '{")
        w(f"\"moves\":<PASTE_MOVES_JSON>,\"material_id\":\"{mat['id']}\",\"tool_d\":{body.tool_d},\"stepover\":{body.stepover},\"stepdown\":{body.stepdown},\"job_name\":\"{body.job_name or ''}\"")
        w("}' -o ")
        w(f"{energy_stem}.csv\n")
        w("```\n\n")

        w("**Heat time-series** → `")
        w(f"{heat_stem}.csv")
        w("`\n\n")
        w("```bash\n")
        w("curl -X POST $API/cam/metrics/heat_timeseries_csv \\\n")
        w("  -H 'Content-Type: application/json' \\\n")
        w("  -d '{")
        w(f"\"moves\":<PASTE_MOVES_JSON>,\"machine_profile_id\":\"{body.machine_profile_id}\",\"material_id\":\"{mat['id']}\",\"tool_d\":{body.tool_d},\"stepover\":{body.stepover},\"stepdown\":{body.stepdown},\"bins\":{body.bins},\"job_name\":\"{body.job_name or ''}\"")
        w("}' -o ")
        w(f"{heat_stem}.csv\n")
        w("```\n\n")

        w("**Bottleneck tags** → `")
        w(f"{bott_stem}.csv")
        w("`\n\n")
        w("```bash\n")
        w("curl -X POST $API/cam/metrics/bottleneck_csv \\\n")
        w("  -H 'Content-Type: application/json' \\\n")
        w("  -d '{")
        w(f"\"moves\":<PASTE_MOVES_JSON>,\"job_name\":\"{body.job_name or ''}\"")
        w("}' -o ")
        w(f"{bott_stem}.csv\n")
        w("```\n\n")
        w("> Tip: in the app UI, you can also click **Export CSV** buttons without using curl.\n")

    data = md.getvalue().encode("utf-8")
    return StreamingResponse(
        iter([data]),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{stem}.md"'}
    )


@router.post("/thermal_report_bundle")
def thermal_report_bundle(body: ThermalReportIn) -> StreamingResponse:
    """
    Export thermal report as ZIP bundle containing:
    - thermal_report_<job>.md (Markdown report)
    - moves_<job>.json (Ready-to-paste moves array for CSV curl commands)

    This solves the "where's my moves JSON?" problem when using CSV-links footer.
    User can extract moves.json and paste directly into curl commands.

    Returns ZIP file via StreamingResponse.
    """
    mat = get_material(body.material_id)
    prof = get_profile(body.machine_profile_id)

    # Compute energy and heat (reuse existing logic)
    energy_data = energy_breakdown(
        moves=body.moves,
        sce_j_per_mm3=float(mat["sce_j_per_mm3"]),
        tool_d_mm=float(body.tool_d),
        stepover=float(body.stepover),
        stepdown=float(body.stepdown),
        heat_partition=mat.get("heat_partition", {"chip": 0.7, "tool": 0.2, "work": 0.1}),
    )

    ts = heat_timeseries(
        moves=body.moves,
        profile=prof,
        tool_d_mm=float(body.tool_d),
        stepover=float(body.stepover),
        stepdown=float(body.stepdown),
        sce_j_per_mm3=float(mat["sce_j_per_mm3"]),
        heat_partition=mat.get("heat_partition", {"chip": 0.7, "tool": 0.2, "work": 0.1}),
        bins=int(body.bins),
    )

    use = energy_data["usage"]
    bj = body.budgets

    # Compute budget states
    def _state(val: float, lim: float) -> str:
        if val <= lim * 0.85:
            return "OK"
        if val <= lim:
            return "WARN"
        return "OVER"

    chip_state = _state(use["chip_j"], bj.chip_j)
    tool_state = _state(use["tool_j"], bj.tool_j)
    work_state = _state(use["work_j"], bj.work_j)

    # Generate sparklines
    spark_chip = _sparkline(ts["p_chip"], width=60)
    spark_tool = _sparkline(ts["p_tool"], width=60)
    spark_work = _sparkline(ts["p_work"], width=60)

    # Bottleneck counts
    caps = energy_data.get("caps", {"feed_cap": 0, "accel": 0, "jerk": 0, "none": 0})

    # Compose Markdown
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")
    stem = safe_stem(body.job_name, prefix="thermal_report")
    md = io.StringIO()
    w = md.write

    w(f"# Thermal Report — {body.job_name or 'Untitled Job'}\n\n")
    w(f"_Generated: {now}_\n\n")
    w("## Context\n")
    w(f"- Machine: `{body.machine_profile_id}`  \n- Material: `{mat['id']}`  \n")
    w(f"- Tool Ø: {body.tool_d:.3f} mm, Step-over: {(body.stepover*100):.1f}%, Step-down: {body.stepdown:.3f} mm\n\n")

    w("## Totals\n")
    w(f"- Volume: {energy_data['totals']['volume_mm3']:.0f} mm³, Energy: {energy_data['totals']['energy_j']:.1f} J, Time: {ts['total_s']:.1f} s\n\n")

    w("## Heat partition budget\n")
    w("| Sink | Used (J) | Budget (J) | State |\n")
    w("|------|----------|------------|-------|\n")
    w(f"| Chip | {use['chip_j']:.1f} | {bj.chip_j:.1f} | {chip_state} |\n")
    w(f"| Tool | {use['tool_j']:.1f} | {bj.tool_j:.1f} | {tool_state} |\n")
    w(f"| Work | {use['work_j']:.1f} | {bj.work_j:.1f} | {work_state} |\n\n")

    w("## Power (J/s) sparklines\n")
    w(f"- Chip: `{spark_chip}`\n")
    w(f"- Tool: `{spark_tool}`\n")
    w(f"- Work: `{spark_work}`\n\n")

    w("## Bottleneck share (counts)\n")
    w(f"- feed_cap: {caps['feed_cap']}, accel: {caps['accel']}, jerk: {caps['jerk']}, none: {caps['none']}\n\n")

    w("> Notes: Sparklines are ASCII summaries of power over normalized time. Use the CSV exports for exact values.\n")

    # Optional CSV links footer
    if body.include_csv_links:
        energy_stem = safe_stem(body.job_name, prefix="energy")
        heat_stem = safe_stem(body.job_name, prefix="heat_ts")
        bott_stem = safe_stem(body.job_name, prefix="bottlenecks")

        w("\n---\n\n")
        w("## CSV Downloads\n")
        w("The following commands will download CSVs generated with the same inputs as this report.\n\n")
        w("**Energy per segment** → `")
        w(f"{energy_stem}.csv")
        w("`\n\n")
        w("```bash\n")
        w("curl -X POST $API/cam/metrics/energy_csv \\\n")
        w("  -H 'Content-Type: application/json' \\\n")
        w("  -d '{")
        w(f"\"moves\":<PASTE_MOVES_JSON>,\"material_id\":\"{mat['id']}\",\"tool_d\":{body.tool_d},\"stepover\":{body.stepover},\"stepdown\":{body.stepdown},\"job_name\":\"{body.job_name or ''}\"")
        w("}' -o ")
        w(f"{energy_stem}.csv\n")
        w("```\n\n")

        w("**Heat time-series** → `")
        w(f"{heat_stem}.csv")
        w("`\n\n")
        w("```bash\n")
        w("curl -X POST $API/cam/metrics/heat_timeseries_csv \\\n")
        w("  -H 'Content-Type: application/json' \\\n")
        w("  -d '{")
        w(f"\"moves\":<PASTE_MOVES_JSON>,\"machine_profile_id\":\"{body.machine_profile_id}\",\"material_id\":\"{mat['id']}\",\"tool_d\":{body.tool_d},\"stepover\":{body.stepover},\"stepdown\":{body.stepdown},\"bins\":{body.bins},\"job_name\":\"{body.job_name or ''}\"")
        w("}' -o ")
        w(f"{heat_stem}.csv\n")
        w("```\n\n")

        w("**Bottleneck tags** → `")
        w(f"{bott_stem}.csv")
        w("`\n\n")
        w("```bash\n")
        w("curl -X POST $API/cam/metrics/bottleneck_csv \\\n")
        w("  -H 'Content-Type: application/json' \\\n")
        w("  -d '{")
        w(f"\"moves\":<PASTE_MOVES_JSON>,\"job_name\":\"{body.job_name or ''}\"")
        w("}' -o ")
        w(f"{bott_stem}.csv\n")
        w("```\n\n")
        w("> Tip: in the app UI, you can also click **Export CSV** buttons without using curl.\n")
        w("> **Note:** The `moves.json` file in this bundle contains the ready-to-paste moves array.\n")

    md_bytes = md.getvalue().encode("utf-8")

    # Generate moves.json
    moves_name = safe_stem(body.job_name, prefix="moves") + ".json"
    moves_bytes = json.dumps(body.moves, separators=(",", ":")).encode("utf-8")

    # Create ZIP bundle
    buf = io.BytesIO()
    with ZipFile(buf, "w") as zf:
        zf.writestr(stem + ".md", md_bytes)
        zf.writestr(moves_name, moves_bytes)

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{stem}.zip"'},
    )
