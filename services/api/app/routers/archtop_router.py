"""Archtop analysis router — contours, stiffness mapping, modal analysis.

Free tier endpoints for archtop plate design and acoustic analysis.
Wraps the archtop pipeline scripts via library functions.

Endpoints:
  POST /api/archtop/contours      — generate contour rings from surface points
  POST /api/archtop/stiffness_map — compute curvature-based stiffness proxy
  POST /api/archtop/modal_analysis — predict mode shapes and frequencies
  GET  /api/archtop/health        — smoke test
"""

from __future__ import annotations

import base64
import io
import logging
import time
from typing import List, Literal, Tuple

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..cam.dxf_writer import create_dxf_writer

_log = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/archtop",
    tags=["Archtop", "CAM"],
)


# =============================================================================
# SHARED MODELS
# =============================================================================


class SurfacePoint(BaseModel):
    """A measured point on the archtop surface."""
    x_mm: float
    y_mm: float
    height_mm: float


class StiffnessGridPoint(BaseModel):
    """A point in the stiffness grid (output from stiffness_map, input to modal)."""
    x_mm: float
    y_mm: float
    K_eff_Nm: float
    height_mm: float


# =============================================================================
# CONTOURS ENDPOINT
# =============================================================================


class ContoursRequest(BaseModel):
    """Request for contour generation."""
    points: List[SurfacePoint] = Field(..., min_length=4)
    levels_mm: List[float] = Field(..., min_length=1)
    resolution_mm: float = Field(2.0, gt=0, le=20)
    out_format: Literal["dxf", "svg", "both"] = "both"


class ContoursResponse(BaseModel):
    """Response with contour rings."""
    dxf_b64: str | None = None
    svg_content: str | None = None
    contour_count: int
    levels_found_mm: List[float]
    bbox_mm: Tuple[float, float, float, float]
    processing_ms: int


@router.post("/contours", response_model=ContoursResponse)
def generate_contours(payload: ContoursRequest) -> ContoursResponse:
    """Generate contour rings from measured surface points.

    Uses IDW interpolation to create a height grid, then extracts
    iso-height contours at the specified levels.
    """
    start_ms = time.perf_counter_ns() // 1_000_000

    try:
        from ..cam.archtop.archtop_contour_generator import (
            generate_contours_from_points,
        )
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"Contour module unavailable: {e}")

    # Convert to arrays
    xs = np.array([p.x_mm for p in payload.points], dtype=float)
    ys = np.array([p.y_mm for p in payload.points], dtype=float)
    hs = np.array([p.height_mm for p in payload.points], dtype=float)

    # Generate contours
    try:
        result = generate_contours_from_points(
            xs=xs,
            ys=ys,
            heights=hs,
            levels=payload.levels_mm,
            resolution=payload.resolution_mm,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    paths = result["paths"]
    levels_found = result["levels_found"]

    if not paths:
        raise HTTPException(
            status_code=422,
            detail="No contours found at specified levels. Try different level values or finer resolution.",
        )

    # Compute bounding box
    all_x = np.concatenate([p[:, 0] for p in paths])
    all_y = np.concatenate([p[:, 1] for p in paths])
    bbox = (float(all_x.min()), float(all_y.min()), float(all_x.max()), float(all_y.max()))

    # Generate DXF if requested
    dxf_b64 = None
    if payload.out_format in ("dxf", "both"):
        writer = create_dxf_writer(["Contours"])
        for path in paths:
            vertices = [(float(x), float(y)) for x, y in path]
            writer.add_polyline("Contours", vertices, closed=True)
        dxf_b64 = base64.b64encode(writer.to_bytes()).decode("ascii")

    # Generate SVG if requested
    svg_content = None
    if payload.out_format in ("svg", "both"):
        svg_content = _paths_to_svg(paths, bbox)

    elapsed_ms = (time.perf_counter_ns() // 1_000_000) - start_ms

    return ContoursResponse(
        dxf_b64=dxf_b64,
        svg_content=svg_content,
        contour_count=len(paths),
        levels_found_mm=levels_found,
        bbox_mm=bbox,
        processing_ms=elapsed_ms,
    )


def _paths_to_svg(paths: List[np.ndarray], bbox: Tuple[float, float, float, float]) -> str:
    """Convert contour paths to SVG string."""
    minx, miny, maxx, maxy = bbox
    pad = 10
    vw = (maxx - minx) + 2 * pad
    vh = (maxy - miny) + 2 * pad

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vw:.3f} {vh:.3f}">',
        f'<g transform="translate({pad - minx:.3f},{pad + maxy:.3f}) scale(1,-1)">',
    ]

    for p in paths:
        d = "M " + " L ".join([f"{x:.3f},{y:.3f}" for x, y in p]) + " Z"
        lines.append(f'  <path d="{d}" fill="none" stroke="black" stroke-width="0.3"/>')

    lines.append("</g>")
    lines.append("</svg>")

    return "\n".join(lines)


# =============================================================================
# STIFFNESS MAP ENDPOINT
# =============================================================================


class StiffnessMapRequest(BaseModel):
    """Request for stiffness map computation."""
    points: List[SurfacePoint] = Field(..., min_length=4)
    E_gpa: float = Field(11.0, gt=0, description="Young's modulus in GPa")
    nu: float = Field(0.35, gt=0, lt=0.5, description="Poisson ratio")
    thickness_mm: float = Field(4.0, gt=0, description="Plate thickness in mm")
    alpha: float = Field(1.0, gt=0, description="Shell stiffness scale factor")
    Lref_mm: float = Field(250.0, gt=0, description="Reference span for combined index")
    resolution_mm: float = Field(2.0, gt=0, le=20)
    heatmap: Literal["K_eff", "K_shell", "R_eff", "height"] = "K_eff"


class StiffnessMapResponse(BaseModel):
    """Response with stiffness map and summary statistics."""
    png_b64: str
    grid: List[StiffnessGridPoint]
    D_b_Nm: float
    max_K_shell_N_per_m: float
    mean_K_shell_N_per_m: float
    max_K_eff_Nm: float
    mean_K_eff_Nm: float
    grid_shape: Tuple[int, int]
    processing_ms: int


@router.post("/stiffness_map", response_model=StiffnessMapResponse)
def compute_stiffness_map(payload: StiffnessMapRequest) -> StiffnessMapResponse:
    """Compute curvature-based stiffness proxy map.

    Takes measured surface points and material properties, returns
    a grid of effective stiffness values plus a heatmap PNG.
    """
    start_ms = time.perf_counter_ns() // 1_000_000

    try:
        from ..cam.archtop.archtop_stiffness_map import (
            compute_stiffness_from_points,
        )
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"Stiffness module unavailable: {e}")

    # Convert to arrays
    xs = np.array([p.x_mm for p in payload.points], dtype=float)
    ys = np.array([p.y_mm for p in payload.points], dtype=float)
    hs = np.array([p.height_mm for p in payload.points], dtype=float)

    try:
        result = compute_stiffness_from_points(
            xs_mm=xs,
            ys_mm=ys,
            heights_mm=hs,
            E_gpa=payload.E_gpa,
            nu=payload.nu,
            thickness_mm=payload.thickness_mm,
            alpha=payload.alpha,
            Lref_mm=payload.Lref_mm,
            resolution_mm=payload.resolution_mm,
            heatmap_type=payload.heatmap,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Convert grid to response format
    grid_points = []
    X_mm = result["X_mm"]
    Y_mm = result["Y_mm"]
    K_eff = result["K_eff"]
    height_mm = result["height_mm"]

    ny, nx = X_mm.shape
    for i in range(ny):
        for j in range(nx):
            grid_points.append(StiffnessGridPoint(
                x_mm=float(X_mm[i, j]),
                y_mm=float(Y_mm[i, j]),
                K_eff_Nm=float(K_eff[i, j]),
                height_mm=float(height_mm[i, j]),
            ))

    elapsed_ms = (time.perf_counter_ns() // 1_000_000) - start_ms

    return StiffnessMapResponse(
        png_b64=result["png_b64"],
        grid=grid_points,
        D_b_Nm=result["D_b"],
        max_K_shell_N_per_m=result["max_K_shell"],
        mean_K_shell_N_per_m=result["mean_K_shell"],
        max_K_eff_Nm=result["max_K_eff"],
        mean_K_eff_Nm=result["mean_K_eff"],
        grid_shape=(ny, nx),
        processing_ms=elapsed_ms,
    )


# =============================================================================
# MODAL ANALYSIS ENDPOINT
# =============================================================================


class ModeResult(BaseModel):
    """Single mode result."""
    mode_number: int
    frequency_hz: float
    angular_frequency_rad_s: float


class ModalAnalysisRequest(BaseModel):
    """Request for modal analysis."""
    stiffness_map: List[StiffnessGridPoint] = Field(..., min_length=9)
    density_kg_m3: float = Field(450.0, gt=0, description="Wood density")
    thickness_mm: float = Field(4.0, gt=0, description="Plate thickness")
    num_modes: int = Field(6, ge=1, le=20)
    # NOTE: simply_supported removed — solver only implements clamped
    # TODO: Add simply_supported when solver supports it


class ModalAnalysisResponse(BaseModel):
    """Response with mode shapes and frequencies."""
    modes: List[ModeResult]
    mode_shapes_png_b64: str
    lowest_mode_hz: float
    air_mode_estimate_hz: float
    grid_shape: Tuple[int, int]
    processing_ms: int


@router.post("/modal_analysis", response_model=ModalAnalysisResponse)
def run_modal_analysis(payload: ModalAnalysisRequest) -> ModalAnalysisResponse:
    """Predict natural frequencies and mode shapes.

    Takes a stiffness map (from /stiffness_map endpoint) and material
    properties, solves the plate vibration eigenvalue problem.

    Uses clamped boundary conditions (plate edges fixed).
    """
    start_ms = time.perf_counter_ns() // 1_000_000

    try:
        from ..cam.archtop.archtop_modal_analysis import (
            solve_modes_from_grid,
        )
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"Modal module unavailable: {e}")

    # Reconstruct grid from flat list
    # Need to figure out grid dimensions from unique x/y values
    xs = sorted(set(p.x_mm for p in payload.stiffness_map))
    ys = sorted(set(p.y_mm for p in payload.stiffness_map))
    nx, ny = len(xs), len(ys)

    if nx * ny != len(payload.stiffness_map):
        raise HTTPException(
            status_code=422,
            detail=f"Stiffness map is not a regular grid. Expected {nx}x{ny}={nx*ny} points, got {len(payload.stiffness_map)}",
        )

    # Build lookup and arrays
    lookup = {(p.x_mm, p.y_mm): p for p in payload.stiffness_map}
    X_mm = np.zeros((ny, nx), dtype=float)
    Y_mm = np.zeros((ny, nx), dtype=float)
    K_eff = np.zeros((ny, nx), dtype=float)
    height_mm = np.zeros((ny, nx), dtype=float)

    for i, y in enumerate(ys):
        for j, x in enumerate(xs):
            p = lookup.get((x, y))
            if p is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"Missing grid point at ({x}, {y})",
                )
            X_mm[i, j] = x
            Y_mm[i, j] = y
            K_eff[i, j] = p.K_eff_Nm
            height_mm[i, j] = p.height_mm

    try:
        result = solve_modes_from_grid(
            X_mm=X_mm,
            Y_mm=Y_mm,
            K_eff=K_eff,
            height_mm=height_mm,
            density_kg_m3=payload.density_kg_m3,
            thickness_mm=payload.thickness_mm,
            num_modes=payload.num_modes,
            boundary="clamped",
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        _log.exception("Modal analysis failed")
        raise HTTPException(status_code=500, detail=f"Modal solver error: {e}")

    modes = [
        ModeResult(
            mode_number=i + 1,
            frequency_hz=f,
            angular_frequency_rad_s=2 * np.pi * f,
        )
        for i, f in enumerate(result["frequencies_hz"])
    ]

    elapsed_ms = (time.perf_counter_ns() // 1_000_000) - start_ms

    return ModalAnalysisResponse(
        modes=modes,
        mode_shapes_png_b64=result["modes_png_b64"],
        lowest_mode_hz=result["frequencies_hz"][0] if result["frequencies_hz"] else 0.0,
        air_mode_estimate_hz=result["frequencies_hz"][0] * 0.7 if result["frequencies_hz"] else 0.0,
        grid_shape=(ny, nx),
        processing_ms=elapsed_ms,
    )


# =============================================================================
# HEALTH ENDPOINT
# =============================================================================


class ArchtopHealthResponse(BaseModel):
    """Health check response."""
    status: Literal["ok"]
    archtop_contour: str
    archtop_stiffness: str
    archtop_modal: str
    dxf_writer: str
    scipy_available: bool


@router.get("/health", response_model=ArchtopHealthResponse)
def health_check() -> ArchtopHealthResponse:
    """Smoke test for archtop module availability."""

    def check_import(module_path: str) -> str:
        try:
            __import__(module_path, fromlist=[""])
            return "loaded"
        except ImportError as e:
            return f"import_error: {e}"

    scipy_ok = False
    try:
        from scipy.sparse.linalg import eigs  # noqa: F401
        scipy_ok = True
    except ImportError:
        pass

    return ArchtopHealthResponse(
        status="ok",
        archtop_contour=check_import("app.cam.archtop.archtop_contour_generator"),
        archtop_stiffness=check_import("app.cam.archtop.archtop_stiffness_map"),
        archtop_modal=check_import("app.cam.archtop.archtop_modal_analysis"),
        dxf_writer=check_import("app.cam.dxf_writer"),
        scipy_available=scipy_ok,
    )
