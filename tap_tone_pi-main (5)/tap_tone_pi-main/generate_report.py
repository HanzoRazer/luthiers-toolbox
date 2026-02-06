#!/usr/bin/env python3
"""
Generate a headless, workstation/Pi-friendly PDF lab report from a Tap Tone Lab bundle.

Design goals:
- Pure ReportLab (no LaTeX, no GUI)
- Robust to missing optional artifacts
- Produces a clean "instrumentation lab" report structure:
  Cover -> Abstract -> Setup -> Protocol -> Signal Processing -> Results -> Error Analysis -> Appendices

Expected bundle layout (flexible):
bundle/
  metadata.json                (optional but recommended)
  geometry.json                (optional)
  grid.json                    (optional)
  excitation.json              (optional)
  derived/wolf_map.json        (optional)
  derived/resonance_table.json (optional)
  derived/confidence_mask.json (optional)
  plots/*.png                  (optional)
  manifest.json                (optional)

Usage:
  python workstation/reports/generate_report.py --bundle ./captures/run_123 --out ./captures/run_123/report.pdf
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
from pathlib import Path
from typing import Any, Optional, Sequence

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether
)

# ----------------------------
# Helpers
# ----------------------------

def _read_json(path: Path) -> Optional[dict[str, Any]]:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return None

def _fmt_dt(dt: _dt.datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def _safe(v: Any, default: str = "n/a") -> str:
    if v is None:
        return default
    if isinstance(v, (int, float)):
        return f"{v}"
    if isinstance(v, str) and v.strip() == "":
        return default
    return str(v)

def _h1(styles) -> ParagraphStyle:
    return ParagraphStyle(
        "H1",
        parent=styles["Heading1"],
        spaceBefore=14,
        spaceAfter=10,
    )

def _h2(styles) -> ParagraphStyle:
    return ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        spaceBefore=10,
        spaceAfter=6,
    )

def _body(styles) -> ParagraphStyle:
    return ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        leading=13,
        spaceAfter=6,
    )

def _mono(styles) -> ParagraphStyle:
    return ParagraphStyle(
        "Mono",
        parent=styles["BodyText"],
        fontName="Courier",
        fontSize=9,
        leading=11,
        spaceAfter=6,
    )

def _kv_table(kv: Sequence[tuple[str, str]], col_widths=(2.1*inch, 4.9*inch)) -> Table:
    data = [[k, v] for k, v in kv]
    t = Table(data, colWidths=list(col_widths))
    t.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LINEBELOW", (0,0), (-1,-1), 0.25, colors.lightgrey),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.whitesmoke, colors.white]),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    return t

def _simple_table(headers: list[str], rows: list[list[str]], col_widths: list[float]) -> Table:
    data = [headers] + rows
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1f2937")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), 9),
        ("FONTNAME", (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,1), (-1,-1), 8.5),
        ("GRID", (0,0), (-1,-1), 0.25, colors.lightgrey),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
        ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]))
    return t

def _find_plot_images(bundle: Path, max_images: int = 8) -> list[Path]:
    plots_dir = bundle / "plots"
    if not plots_dir.exists():
        return []
    imgs = sorted([p for p in plots_dir.glob("*.png") if p.is_file()])
    return imgs[:max_images]

def _add_header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.grey)
    # Header
    canvas.drawString(doc.leftMargin, doc.pagesize[1] - 0.55*inch, doc.title or "Lab Report")
    # Footer
    page = canvas.getPageNumber()
    canvas.drawRightString(doc.pagesize[0] - doc.rightMargin, 0.5*inch, f"Page {page}")
    canvas.restoreState()

# ----------------------------
# Report builder
# ----------------------------

def build_report(bundle_dir: Path, out_pdf: Path, *, title: str, author: str) -> None:
    styles = getSampleStyleSheet()
    H1, H2, BODY, MONO = _h1(styles), _h2(styles), _body(styles), _mono(styles)

    metadata = _read_json(bundle_dir / "metadata.json") or {}
    geometry = _read_json(bundle_dir / "geometry.json") or {}
    grid = _read_json(bundle_dir / "grid.json") or {}
    excitation = _read_json(bundle_dir / "excitation.json") or {}
    wolf = _read_json(bundle_dir / "derived" / "wolf_map.json") or _read_json(bundle_dir / "wolf_map.json") or {}
    resonance = _read_json(bundle_dir / "derived" / "resonance_table.json") or _read_json(bundle_dir / "resonance_table.json") or {}
    manifest = _read_json(bundle_dir / "manifest.json") or {}

    # Derived "front matter" values
    now = _dt.datetime.now()
    experiment_id = metadata.get("experiment_id") or manifest.get("experiment_id") or metadata.get("run_id") or "n/a"
    instrument_id = metadata.get("instrument_id") or "n/a"
    build_stage = metadata.get("build_stage") or "n/a"
    units = (grid.get("units") or geometry.get("units") or metadata.get("units") or "mm")

    doc = SimpleDocTemplate(
        str(out_pdf),
        pagesize=letter,
        leftMargin=0.85*inch,
        rightMargin=0.85*inch,
        topMargin=0.9*inch,
        bottomMargin=0.85*inch,
        title=title,
        author=author,
    )

    story: list[Any] = []

    # Cover
    story.append(Paragraph(title, styles["Title"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Operational Acoustic-Structural Mapping (Speaker Drive, Roving Measurement)", BODY))
    story.append(Spacer(1, 16))

    cover_kv = [
        ("Author", author),
        ("Date", _fmt_dt(now)),
        ("Experiment ID", _safe(experiment_id)),
        ("Instrument ID", _safe(instrument_id)),
        ("Build Stage", _safe(build_stage)),
        ("Bundle Path", str(bundle_dir)),
        ("Units", _safe(units)),
    ]
    story.append(_kv_table(cover_kv))
    story.append(Spacer(1, 18))

    story.append(Paragraph("<b>Abstract</b>", H2))
    abstract_text = metadata.get("abstract") or (
        "This report summarizes an operational roving measurement of an acoustic guitar driven by a reproducible "
        "speaker-air excitation. A fixed reference microphone and a roving microphone were used to estimate "
        "complex transfer behavior and coherence over a defined spatial grid. Results include resonance features, "
        "coherence-based confidence, and spatial localization indicators to support wolf-region identification."
    )
    story.append(Paragraph(abstract_text, BODY))
    story.append(PageBreak())

    # 1 Introduction
    story.append(Paragraph("1. Introduction", H1))
    story.append(Paragraph(
        "Goal: achieve high observability of coupled vibro-acoustic behavior with minimal intrusion (no added plate mass). "
        "This report documents apparatus, protocol, signal processing, results, and an error/confidence framework suitable "
        "for repeatable shop or lab use.",
        BODY
    ))

    # 2 System Description
    story.append(Paragraph("2. Physical System Description", H1))
    sys_kv = [
        ("Instrument ID", _safe(instrument_id)),
        ("Build Stage", _safe(build_stage)),
        ("Strings", _safe(metadata.get("strings_state"))),
        ("Support Condition", _safe(metadata.get("support_condition"))),
        ("Temperature", _safe(metadata.get("temperature_c"))),
        ("Humidity", _safe(metadata.get("humidity_pct"))),
    ]
    story.append(_kv_table(sys_kv))
    story.append(Spacer(1, 10))

    if geometry:
        story.append(Paragraph("2.1 Geometry", H2))
        geom_lines = json.dumps(geometry, indent=2, sort_keys=True)
        story.append(Paragraph("Geometry payload (recorded):", BODY))
        story.append(Paragraph(f"<pre>{geom_lines}</pre>", MONO))

    if grid:
        story.append(Paragraph("2.2 Measurement Grid", H2))
        pts = grid.get("points") or []
        story.append(Paragraph(f"Grid points: {_safe(len(pts))}. Units: {_safe(units)}.", BODY))
        if pts:
            rows = []
            for p in pts[:24]:
                rows.append([_safe(p.get("label")), _safe(p.get("x_mm", p.get("x"))), _safe(p.get("y_mm", p.get("y")))])
            story.append(_simple_table(
                ["Label", "x (mm)", "y (mm)"],
                rows,
                col_widths=[1.6*inch, 2.6*inch, 2.6*inch],
            ))
            if len(pts) > 24:
                story.append(Paragraph(f"(Showing first 24 of {len(pts)} points.)", BODY))

    # 3 Apparatus
    story.append(Paragraph("3. Experimental Apparatus", H1))
    app_kv = [
        ("Excitation", _safe(excitation.get("type") or metadata.get("excitation_type") or "speaker-air drive")),
        ("Signal", _safe(excitation.get("signal") or metadata.get("excitation_signal"))),
        ("Drive Range (Hz)", _safe(excitation.get("freq_range_hz") or metadata.get("freq_range_hz"))),
        ("Reference Mic", _safe(metadata.get("reference_mic_model"))),
        ("Roving Mic", _safe(metadata.get("roving_mic_model"))),
        ("Sample Rate (Hz)", _safe(metadata.get("sample_rate") or excitation.get("sample_rate"))),
        ("Duration (s)", _safe(metadata.get("duration_s") or excitation.get("duration_s"))),
    ]
    story.append(_kv_table(app_kv))

    # 4 Protocol
    story.append(Paragraph("4. Measurement Protocol", H1))
    prot = metadata.get("protocol") or (
        "Place the instrument on a repeatable support fixture. Position the excitation speaker at the documented "
        "distance and angle. Keep the reference microphone fixed at the documented location. Move the roving "
        "microphone to each grid point (mm coordinates) and record synchronized 2-channel audio for the configured "
        "duration. Repeat as required to quantify variance. Apply gating when using impulse response methods to "
        "reduce room reflection contamination."
    )
    story.append(Paragraph(prot, BODY))

    # 5 Signal Processing
    story.append(Paragraph("5. Signal Processing", H1))
    story.append(Paragraph(
        "Operational transfer estimate uses cross/auto spectral densities: H_ir(f)=G_ir(f)/G_rr(f). "
        "Coherence is used as a validity gate. For time-gated impulse response workflows, a deconvolution "
        "step yields h(t), followed by windowing h_g(t) prior to FFT.",
        BODY
    ))

    # 6 Results
    story.append(Paragraph("6. Results", H1))

    # Wolf map summary
    story.append(Paragraph("6.1 Wolf-Region Indicators", H2))
    if isinstance(wolf, dict) and wolf:
        # wolf_map.json might be list or dict; accept both
        wolf_points = wolf.get("points") if isinstance(wolf.get("points"), list) else None
        if wolf_points is None and isinstance(wolf, dict) and "0" not in wolf:
            # maybe the dict is actually a list serialized differently; ignore
            pass

    wolf_data = None
    if isinstance(wolf, list):
        wolf_data = wolf
    elif isinstance(wolf, dict) and isinstance(wolf.get("points"), list):
        wolf_data = wolf["points"]

    if wolf_data:
        # show top localized points
        wolf_sorted = sorted(
            wolf_data,
            key=lambda r: float(r.get("localization_index", 0.0) or 0.0),
            reverse=True,
        )
        top = wolf_sorted[:12]
        rows = []
        for r in top:
            rows.append([
                _safe(r.get("label")),
                _safe(r.get("x_mm")),
                _safe(r.get("y_mm")),
                f"{float(r.get('localization_index', 0.0) or 0.0):.3f}",
                f"{float(r.get('coherence_mean', 0.0) or 0.0):.3f}",
            ])
        story.append(_simple_table(
            ["Point", "x (mm)", "y (mm)", "Localization", "Coherence"],
            rows,
            col_widths=[1.3*inch, 1.15*inch, 1.15*inch, 1.3*inch, 1.3*inch],
        ))
        story.append(Paragraph(
            "Interpretation: high localization combined with high coherence suggests spatially concentrated resonant behavior "
            "and is a candidate indicator of wolf-prone regions when correlated with playing tests.",
            BODY
        ))
    else:
        story.append(Paragraph(
            "No wolf_map.json found. If you ran the roving-grid tool, confirm it wrote derived/wolf_map.json or wolf_map.json.",
            BODY
        ))

    # Resonance table summary (optional)
    story.append(Paragraph("6.2 Resonance Summary (optional)", H2))
    res_rows = []
    if isinstance(resonance, dict) and isinstance(resonance.get("rows"), list):
        for r in resonance["rows"][:16]:
            res_rows.append([_safe(r.get("freq_hz")), _safe(r.get("q")), _safe(r.get("note")), _safe(r.get("confidence"))])
    elif isinstance(resonance, list):
        for r in resonance[:16]:
            if isinstance(r, dict):
                res_rows.append([_safe(r.get("freq_hz")), _safe(r.get("q")), _safe(r.get("note")), _safe(r.get("confidence"))])

    if res_rows:
        story.append(_simple_table(
            ["f0 (Hz)", "Q", "Note", "Conf."],
            res_rows,
            col_widths=[1.4*inch, 1.0*inch, 2.6*inch, 1.6*inch],
        ))
    else:
        story.append(Paragraph("No resonance_table.json present (this is optional).", BODY))

    # Plots section
    story.append(Paragraph("6.3 Plots", H2))
    imgs = _find_plot_images(bundle_dir, max_images=10)
    if imgs:
        story.append(Paragraph("Selected plots included from bundle/plots:", BODY))
        for img_path in imgs:
            # fit image to page width
            im = Image(str(img_path))
            im._restrictSize(6.4*inch, 4.5*inch)
            story.append(KeepTogether([Paragraph(f"<b>{img_path.name}</b>", BODY), im, Spacer(1, 10)]))
    else:
        story.append(Paragraph("No PNG plots found in bundle/plots.", BODY))

    # 7 Error analysis
    story.append(Paragraph("7. Error Analysis and Confidence", H1))
    story.append(Paragraph(
        "Uncertainty sources include microphone positioning tolerances, excitation repeatability, environmental reflections "
        "(mitigated via close placement and time gating), and support-condition variability. Confidence should be assessed "
        "using coherence thresholds and repeated-trial variance (e.g., coefficient of variation across runs).",
        BODY
    ))

    # 8 Appendices
    story.append(Paragraph("8. Appendices", H1))
    story.append(Paragraph("8.1 Manifest (if present)", H2))
    if manifest:
        story.append(Paragraph(f"<pre>{json.dumps(manifest, indent=2, sort_keys=True)}</pre>", MONO))
    else:
        story.append(Paragraph("manifest.json not present.", BODY))

    # Build
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    doc.build(story, onFirstPage=_add_header_footer, onLaterPages=_add_header_footer)


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Generate a PDF lab report from a Tap Tone bundle.")
    ap.add_argument("--bundle", type=str, required=True, help="Path to bundle directory")
    ap.add_argument("--out", type=str, required=True, help="Output PDF path")
    ap.add_argument("--title", type=str, default="Tap Tone Lab Report", help="Report title")
    ap.add_argument("--author", type=str, default="(author)", help="Author name")
    return ap.parse_args()


def main() -> None:
    args = _parse_args()
    build_report(
        bundle_dir=Path(args.bundle).expanduser().resolve(),
        out_pdf=Path(args.out).expanduser().resolve(),
        title=args.title,
        author=args.author,
    )


if __name__ == "__main__":
    main()
