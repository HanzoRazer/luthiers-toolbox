"""CAM Metrics — Thermal Report endpoints.

Extracted from metrics_router.py (WP-3) for god-object decomposition.
Sub-router: included by metrics_router.router.
"""

from __future__ import annotations

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


_SPARK = "▁▂▃▄▅▆▇█"


def _sparkline(values: List[float], width: int = 60) -> str:
    """Generate ASCII sparkline from values."""
    if not values:
        return ""
    if len(values) > width:
        step = len(values) / width
        vals = [values[int(i * step)] for i in range(width)]
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
    include_csv_links: bool = False


def _thermal_state(val: float, lim: float) -> str:
    if val <= lim * 0.85:
        return "OK"
    if val <= lim:
        return "WARN"
    return "OVER"


def _build_thermal_md(
    body: ThermalReportIn,
    mat: Dict[str, Any],
    energy_data: Dict[str, Any],
    ts: Dict[str, Any],
) -> str:
    """Build the thermal report markdown string."""
    bj = body.budgets
    use = energy_data["totals"]["heat"]

    chip_state = _thermal_state(use["chip_j"], bj.chip_j)
    tool_state = _thermal_state(use["tool_j"], bj.tool_j)
    work_state = _thermal_state(use["work_j"], bj.work_j)

    spark_chip = _sparkline(ts["p_chip"], width=60)
    spark_tool = _sparkline(ts["p_tool"], width=60)
    spark_work = _sparkline(ts["p_work"], width=60)

    caps: Dict[str, int] = {"feed_cap": 0, "accel": 0, "jerk": 0, "none": 0}
    for m in body.moves:
        lim = m.get("meta", {}).get("limit")
        if lim in caps:
            caps[lim] += 1

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")
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

    if body.include_csv_links:
        energy_stem = safe_stem(body.job_name, prefix="energy")
        heat_stem = safe_stem(body.job_name, prefix="heat_ts")
        bott_stem = safe_stem(body.job_name, prefix="bottlenecks")

        w("\n---\n\n")
        w("## CSV Downloads\n")
        w("Set `$API` to your canonical base URL, e.g. `http://127.0.0.1:8000/api`.\n\n")
        w("The following commands will download CSVs generated with the same inputs as this report.\n\n")
        w(f"**Energy per segment** → `{energy_stem}.csv`\n\n")
        w("```bash\n")
        w("curl -X POST $API/cam/metrics/energy_csv \\\n")
        w("  -H 'Content-Type: application/json' \\\n")
        w(f"  -d '{{\"moves\":<PASTE_MOVES_JSON>,\"material_id\":\"{mat['id']}\",\"tool_d\":{body.tool_d},\"stepover\":{body.stepover},\"stepdown\":{body.stepdown},\"job_name\":\"{body.job_name or ''}\"}}' -o {energy_stem}.csv\n")
        w("```\n\n")

        w(f"**Heat time-series** → `{heat_stem}.csv`\n\n")
        w("```bash\n")
        w("curl -X POST $API/cam/metrics/heat_timeseries_csv \\\n")
        w("  -H 'Content-Type: application/json' \\\n")
        w(f"  -d '{{\"moves\":<PASTE_MOVES_JSON>,\"machine_profile_id\":\"{body.machine_profile_id}\",\"material_id\":\"{mat['id']}\",\"tool_d\":{body.tool_d},\"stepover\":{body.stepover},\"stepdown\":{body.stepdown},\"bins\":{body.bins},\"job_name\":\"{body.job_name or ''}\"}}' -o {heat_stem}.csv\n")
        w("```\n\n")

        w(f"**Bottleneck tags** → `{bott_stem}.csv`\n\n")
        w("```bash\n")
        w("curl -X POST $API/cam/metrics/bottleneck_csv \\\n")
        w("  -H 'Content-Type: application/json' \\\n")
        w(f"  -d '{{\"moves\":<PASTE_MOVES_JSON>,\"job_name\":\"{body.job_name or ''}\"}}' -o {bott_stem}.csv\n")
        w("```\n\n")
        w("> Tip: in the app UI, you can also click **Export CSV** buttons without using curl.\n")

    return md.getvalue()


def _compute_energy_and_heat(body: ThermalReportIn, mat: Dict, prof: Dict) -> tuple:
    """Compute energy and heat data from body inputs."""
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
    return energy_data, ts


@router.post("/thermal_report_md")
def thermal_report_md(body: ThermalReportIn) -> StreamingResponse:
    """Generate comprehensive thermal report as Markdown with:"""
    mat = get_material(body.material_id)
    prof = get_profile(body.machine_profile_id)

    energy_data = energy_breakdown(
        moves=body.moves,
        sce_j_per_mm3=float(mat["sce_j_per_mm3"]),
        tool_d_mm=float(body.tool_d),
        stepover=float(body.stepover),
        stepdown=float(body.stepdown),
        heat_partition=mat.get("heat_partition", {"chip": 0.7, "tool": 0.2, "work": 0.1})
    )

    ts = heat_timeseries(
        moves=body.moves, profile=prof,
        tool_d_mm=float(body.tool_d), stepover=float(body.stepover), stepdown=float(body.stepdown),
        sce_j_per_mm3=float(mat["sce_j_per_mm3"]),
        heat_partition=mat.get("heat_partition", {"chip": 0.7, "tool": 0.2, "work": 0.1}),
        bins=int(body.bins)
    )

    md_text = _build_thermal_md(body, mat, energy_data, ts)
    stem = safe_stem(body.job_name or "thermal_report")
    data = md_text.encode("utf-8")
    return StreamingResponse(
        iter([data]),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{stem}.md"'}
    )


@router.post("/thermal_report_bundle")
def thermal_report_bundle(body: ThermalReportIn) -> StreamingResponse:
    """Export thermal report as ZIP bundle containing:"""
    mat = get_material(body.material_id)
    prof = get_profile(body.machine_profile_id)

    energy_data, ts = _compute_energy_and_heat(body, mat, prof)

    use = energy_data["usage"]
    bj = body.budgets

    chip_state = _thermal_state(use["chip_j"], bj.chip_j)
    tool_state = _thermal_state(use["tool_j"], bj.tool_j)
    work_state = _thermal_state(use["work_j"], bj.work_j)

    spark_chip = _sparkline(ts["p_chip"], width=60)
    spark_tool = _sparkline(ts["p_tool"], width=60)
    spark_work = _sparkline(ts["p_work"], width=60)

    caps = energy_data.get("caps", {"feed_cap": 0, "accel": 0, "jerk": 0, "none": 0})

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

    if body.include_csv_links:
        energy_stem = safe_stem(body.job_name, prefix="energy")
        heat_stem = safe_stem(body.job_name, prefix="heat_ts")
        bott_stem = safe_stem(body.job_name, prefix="bottlenecks")

        w("\n---\n\n")
        w("## CSV Downloads\n")
        w("The following commands will download CSVs generated with the same inputs as this report.\n\n")
        w(f"**Energy per segment** → `{energy_stem}.csv`\n\n")
        w("```bash\n")
        w("curl -X POST $API/cam/metrics/energy_csv \\\n")
        w("  -H 'Content-Type: application/json' \\\n")
        w(f"  -d '{{\"moves\":<PASTE_MOVES_JSON>,\"material_id\":\"{mat['id']}\",\"tool_d\":{body.tool_d},\"stepover\":{body.stepover},\"stepdown\":{body.stepdown},\"job_name\":\"{body.job_name or ''}\"}}' -o {energy_stem}.csv\n")
        w("```\n\n")

        w(f"**Heat time-series** → `{heat_stem}.csv`\n\n")
        w("```bash\n")
        w("curl -X POST $API/cam/metrics/heat_timeseries_csv \\\n")
        w("  -H 'Content-Type: application/json' \\\n")
        w(f"  -d '{{\"moves\":<PASTE_MOVES_JSON>,\"machine_profile_id\":\"{body.machine_profile_id}\",\"material_id\":\"{mat['id']}\",\"tool_d\":{body.tool_d},\"stepover\":{body.stepover},\"stepdown\":{body.stepdown},\"bins\":{body.bins},\"job_name\":\"{body.job_name or ''}\"}}' -o {heat_stem}.csv\n")
        w("```\n\n")

        w(f"**Bottleneck tags** → `{bott_stem}.csv`\n\n")
        w("```bash\n")
        w("curl -X POST $API/cam/metrics/bottleneck_csv \\\n")
        w("  -H 'Content-Type: application/json' \\\n")
        w(f"  -d '{{\"moves\":<PASTE_MOVES_JSON>,\"job_name\":\"{body.job_name or ''}\"}}' -o {bott_stem}.csv\n")
        w("```\n\n")
        w("> Tip: in the app UI, you can also click **Export CSV** buttons without using curl.\n")
        w("> **Note:** The `moves.json` file in this bundle contains the ready-to-paste moves array.\n")

    md_bytes = md.getvalue().encode("utf-8")

    moves_name = safe_stem(body.job_name, prefix="moves") + ".json"
    moves_bytes = json.dumps(body.moves, separators=(",", ":")).encode("utf-8")

    buf = io.BytesIO()
    with ZipFile(buf, "w") as zf:
        zf.writestr(stem + ".md", md_bytes)
        zf.writestr(moves_name, moves_bytes)

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{stem}.zip"'},
    )
