# services/api/app/art_studio/bracing_router.py
"""
Art Studio Bracing Router — production replacement.

Previously: returned hollow section properties, ignored radius fields,
exported flat rectangles as DXF, made scallop: bool do nothing.

Now:
    /preview    → real EI, real camber from dish radius, mean area for mass
    /batch      → same for a set, with totals
    /presets    → instrument-specific presets with correct dimensions
    /export-dxf → DXF that includes scallop profile polylines, not rectangles
    /back       → back brace pattern generator (new)
"""

from __future__ import annotations

import io
import math
from typing import List, Optional
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..calculators import bracing_calc
from ..calculators.bracing_calc import BracingCalcInput, BraceSectionResult
from ..util.dxf_compat import (
    create_document, add_polyline,
    validate_version, DxfVersion, DXF_VERSIONS,
)
from ..instrument_geometry.bracing.back_brace import (
    generate_back_bracing, list_body_styles, get_profile_label,
)
from ..pipelines.bracing.bracing_calc import brace_scallop_height_at as scallop_height_at
from .bracing_presets_bridge import get_instrument_presets

router = APIRouter(prefix="/art-studio/bracing", tags=["Art Studio - Bracing"])


# ── Request / Response models ─────────────────────────────────────────────────

class BracingPreviewRequest(BaseModel):
    profile_type: str = Field(default="parabolic")
    width_mm: float = Field(default=12.0, ge=1.0, le=50.0)
    height_mm: float = Field(default=8.0, ge=1.0, le=30.0)
    h_end_mm: float = Field(default=3.5, description="Scallop tip height (scalloped only)")
    scallop_length_mm: float = Field(default=40.0, description="Scallop taper length each end")
    length_mm: float = Field(default=300.0, ge=10.0, le=600.0)
    density_kg_m3: float = Field(default=420.0, ge=200.0, le=1200.0)
    material: str = Field(default="sitka_spruce")
    back_radius_mm: float = Field(
        default=0.0,
        description="Back dish radius in mm (e.g. 6096 = 20ft). 0 = no camber.",
    )
    top_radius_mm: float = Field(
        default=0.0,
        description="Top dish radius in mm. 0 = no camber.",
    )
    plate: str = Field(default="top", description="'top' or 'back'")

    def to_calc_input(self) -> BracingCalcInput:
        return BracingCalcInput(
            profile_type=self.profile_type,
            width_mm=self.width_mm,
            height_mm=self.height_mm,
            h_end_mm=self.h_end_mm,
            scallop_length_mm=self.scallop_length_mm,
            length_mm=self.length_mm,
            density_kg_m3=self.density_kg_m3,
            material=self.material,
            back_radius_mm=self.back_radius_mm,
            top_radius_mm=self.top_radius_mm,
            plate=self.plate,
        )


class BracingPreviewResponse(BaseModel):
    section: BraceSectionResult
    mass_grams: float
    # human-readable interpretation
    camber_note: str


class BracingBatchRequest(BaseModel):
    braces: List[BracingPreviewRequest]
    name: str = "Bracing Set"


class BracingBatchResponse(BaseModel):
    name: str
    braces: List[dict]
    totals: dict


class BracingPreset(BaseModel):
    id: str
    name: str
    description: str
    braces: List[BracingPreviewRequest]
    source: str = "generic"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/preview", response_model=BracingPreviewResponse)
def preview_bracing(req: BracingPreviewRequest) -> BracingPreviewResponse:
    """
    Real brace section properties: EI, camber, mean mass.

    back_radius_mm / top_radius_mm are now used to compute pre-bend camber.
    mass_grams uses mean cross-section (accounts for scallop taper).
    EI is the Euler-Bernoulli bending stiffness at the center section.
    """
    calc_input = req.to_calc_input()
    section    = bracing_calc.calculate_brace_section(calc_input)
    mass       = bracing_calc.estimate_mass_grams(calc_input)

    radius = req.back_radius_mm if req.plate == "back" else req.top_radius_mm
    if radius > 0 and section.camber_mm > 0:
        r_ft   = radius / 304.8
        note   = (
            f"Pre-bend camber {section.camber_mm:.2f}mm required for "
            f"{r_ft:.0f}ft ({radius:.0f}mm) dish radius."
        )
    else:
        note = "No dish radius specified — brace cut flat."

    return BracingPreviewResponse(
        section=section,
        mass_grams=round(mass, 2),
        camber_note=note,
    )


@router.post("/batch", response_model=BracingBatchResponse)
def batch_bracing(req: BracingBatchRequest) -> BracingBatchResponse:
    result = bracing_calc.calculate_brace_set([b.to_calc_input() for b in req.braces])
    return BracingBatchResponse(
        name=req.name,
        braces=result["braces"],
        totals=result["totals"],
    )


@router.get("/presets", response_model=List[BracingPreset])
def get_bracing_presets() -> List[BracingPreset]:
    generic = [
        BracingPreset(
            id="x-brace-standard", name="Standard X-Brace",
            description="Martin-style scalloped X-bracing, steel string acoustic",
            source="generic",
            braces=[
                BracingPreviewRequest(profile_type="scalloped", width_mm=12.0,
                    height_mm=15.0, h_end_mm=4.0, scallop_length_mm=45.0,
                    length_mm=280.0, density_kg_m3=420.0, material="sitka_spruce"),
                BracingPreviewRequest(profile_type="scalloped", width_mm=12.0,
                    height_mm=15.0, h_end_mm=4.0, scallop_length_mm=45.0,
                    length_mm=280.0, density_kg_m3=420.0, material="sitka_spruce"),
            ],
        ),
        BracingPreset(
            id="back-ladder-om", name="OM Ladder Back (6 braces)",
            description="Martin OM-style scalloped ladder bracing, 20ft radius",
            source="generic",
            braces=[
                BracingPreviewRequest(
                    profile_type="scalloped", width_mm=6.5, height_mm=10.0,
                    h_end_mm=3.5, scallop_length_mm=40.0,
                    length_mm=L, density_kg_m3=420.0, material="sitka_spruce",
                    back_radius_mm=6096.0, plate="back",
                )
                for L in [262, 245, 227, 311, 348, 304]
            ],
        ),
    ]
    return generic + get_instrument_presets()


# ── Back brace endpoint ───────────────────────────────────────────────────────

class BackBraceRequest(BaseModel):
    body_style: str = Field(default="martin_om")
    stations_mm: Optional[List[float]] = None
    width_mm: float = Field(default=6.5)
    h_center_mm: float = Field(default=10.0)
    h_end_mm: float = Field(default=3.5)
    scallop_length_mm: float = Field(default=40.0)
    back_radius_ft: Optional[float] = Field(default=None)
    material: str = Field(default="sitka_spruce")


@router.post("/back")
def generate_back_pattern(req: BackBraceRequest):
    """
    Generate a ladder-brace back pattern for a given body style.

    Returns per-brace geometry including camber, scallop points for CNC,
    length (body-width-aware), mass, and center seam protection analysis.
    """
    pattern = generate_back_bracing(
        body_style=req.body_style,
        stations_mm=req.stations_mm,
        width_mm=req.width_mm,
        h_center_mm=req.h_center_mm,
        h_end_mm=req.h_end_mm,
        scallop_length_mm=req.scallop_length_mm,
        back_radius_ft=req.back_radius_ft,
        material=req.material,
    )

    return {
        "body_style":       pattern.body_style,
        "back_radius_mm":   pattern.back_radius_mm,
        "back_radius_ft":   round(pattern.back_radius_mm / 304.8, 1),
        "total_mass_g":     pattern.total_mass_g,
        "max_seam_span_mm": pattern.max_seam_span_mm,
        "seam_adequate":    pattern.seam_adequate,
        "seam_warning":     pattern.seam_warning,
        "braces": [
            {
                "index":              b.index,
                "station_mm":         b.station_mm,
                "body_width_mm":      b.body_width_mm,
                "length_mm":          b.length_mm,
                "width_mm":           b.width_mm,
                "h_center_mm":        b.h_center_mm,
                "h_end_mm":           b.h_end_mm,
                "scallop_length_mm":  b.scallop_length_mm,
                "full_height_length_mm": b.full_height_length_mm,
                "back_radius_mm":     b.back_radius_mm,
                "camber_mm":          b.camber_mm,
                "mass_g":             b.mass_g,
                "span_to_prev_mm":    b.span_to_prev_mm,
                "span_to_next_mm":    b.span_to_next_mm,
                "seam_risk":          b.seam_risk,
                "scallop_points":     b.scallop_points(n=20),
            }
            for b in pattern.braces
        ],
    }


@router.get("/back/body-styles")
def get_back_body_styles():
    return [{"key": k, "label": get_profile_label(k)} for k in list_body_styles()]


# ── DXF export ────────────────────────────────────────────────────────────────

class BraceLayoutItem(BaseModel):
    profile_type: str = "parabolic"
    width_mm: float = Field(default=12.0, ge=1.0, le=50.0)
    height_mm: float = Field(default=8.0, ge=1.0, le=30.0)
    h_end_mm: float = Field(default=3.5)
    scallop_length_mm: float = Field(default=40.0)
    length_mm: float = Field(default=300.0, ge=10.0, le=600.0)
    x_mm: float = 0.0
    y_mm: float = 0.0
    angle_deg: float = 0.0
    name: str = ""


class BracingDxfExportRequest(BaseModel):
    braces: List[BraceLayoutItem]
    dxf_version: str = "R12"
    soundhole_diameter_mm: Optional[float] = None
    soundhole_x_mm: float = 0.0
    soundhole_y_mm: float = 0.0
    include_centerlines: bool = True
    include_outlines: bool = True
    include_scallop_profiles: bool = True  # NEW — was ignored before
    include_labels: bool = True
    filename: str = "bracing_layout"
    scallop_profile_offset_mm: float = Field(
        default=20.0,
        description="Y offset below layout to place scallop profile drawings",
    )


@router.post("/export-dxf")
def export_bracing_dxf(req: BracingDxfExportRequest):
    """
    Export bracing layout to DXF.

    Now includes scallop profile side-view drawings below the layout plan,
    one per unique brace profile. Previously only exported flat rectangles.
    """
    try:
        version = validate_version(req.dxf_version)
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e))

    doc = create_document(version)
    msp = doc.modelspace()

    for layer_name, color in [
        ("BRACES", 3), ("CENTERLINES", 1),
        ("REFERENCE", 5), ("LABELS", 7), ("SCALLOP_PROFILES", 4),
    ]:
        doc.layers.add(name=layer_name, color=color)

    if req.soundhole_diameter_mm:
        msp.add_circle(
            center=(req.soundhole_x_mm, req.soundhole_y_mm),
            radius=req.soundhole_diameter_mm / 2,
            dxfattribs={"layer": "REFERENCE"},
        )

    # ── Plan view ────────────────────────────────────────────────────────────
    for idx, brace in enumerate(req.braces):
        a_rad    = math.radians(brace.angle_deg)
        cos_a, sin_a = math.cos(a_rad), math.sin(a_rad)
        half_L   = brace.length_mm / 2
        half_w   = brace.width_mm / 2

        if req.include_outlines:
            corners = []
            for dx, dy in [(-half_L, -half_w), (half_L, -half_w),
                            (half_L, half_w), (-half_L, half_w)]:
                rx = dx * cos_a - dy * sin_a + brace.x_mm
                ry = dx * sin_a + dy * cos_a + brace.y_mm
                corners.append((rx, ry))
            add_polyline(msp, corners, layer="BRACES", closed=True, version=version)

        if req.include_centerlines:
            msp.add_line(
                (-half_L * cos_a + brace.x_mm, -half_L * sin_a + brace.y_mm),
                (half_L * cos_a + brace.x_mm,   half_L * sin_a + brace.y_mm),
                dxfattribs={"layer": "CENTERLINES"},
            )

        if req.include_labels:
            label = brace.name or f"Brace {idx + 1}"
            lx = -(half_w + 3) * sin_a + brace.x_mm
            ly =  (half_w + 3) * cos_a + brace.y_mm
            msp.add_text(label, dxfattribs={
                "layer": "LABELS", "height": 3.0,
                "rotation": brace.angle_deg, "insert": (lx, ly),
            })

    # ── Scallop profile drawings ──────────────────────────────────────────────
    if req.include_scallop_profiles:
        profile_x_cursor = 0.0
        profile_y_base   = -(req.scallop_profile_offset_mm)
        profile_spacing  = 20.0  # gap between profiles

        for idx, brace in enumerate(req.braces):
            h_c = brace.height_mm
            h_e = brace.h_end_mm
            sc  = brace.scallop_length_mm
            L   = brace.length_mm
            n_pts = max(20, int(L / 5))

            # Build profile polyline: bottom edge (flat) then top edge (scallop)
            bottom = [(profile_x_cursor + L * i / (n_pts - 1), profile_y_base)
                      for i in range(n_pts)]
            top    = []
            for i in range(n_pts):
                x = L * i / (n_pts - 1)
                h = scallop_height_at(x, L, h_c, h_e, sc) if sc > 0 else h_c
                top.append((profile_x_cursor + x, profile_y_base - h))

            # Closed profile: bottom left→right, then top right→left
            profile_pts = bottom + list(reversed(top))
            add_polyline(msp, profile_pts, layer="SCALLOP_PROFILES",
                         closed=True, version=version)

            # Label
            lbl = brace.name or f"Brace {idx + 1}"
            msp.add_text(lbl, dxfattribs={
                "layer": "LABELS", "height": 2.5,
                "insert": (profile_x_cursor + L / 2, profile_y_base + 4),
            })

            profile_x_cursor += L + profile_spacing

    # ── Serialise ────────────────────────────────────────────────────────────
    text_buf = io.StringIO()
    doc.write(text_buf)
    text_buf.seek(0)
    dxf_bytes = text_buf.getvalue().encode("utf-8")

    return StreamingResponse(
        io.BytesIO(dxf_bytes),
        media_type="application/dxf",
        headers={
            "Content-Disposition": f"attachment; filename={req.filename}.dxf",
            "X-DXF-Version": version,
            "X-Brace-Count": str(len(req.braces)),
        },
    )


@router.get("/dxf-versions")
def get_dxf_versions() -> dict:
    versions = [
        {
            "version": name, "ac_code": ac_code,
            "supports_lwpolyline": name != "R12",
            "recommended": name == "R12",
        }
        for name, ac_code in DXF_VERSIONS.items()
    ]
    return {"default": "R12", "versions": sorted(versions, key=lambda v: v["ac_code"])}
