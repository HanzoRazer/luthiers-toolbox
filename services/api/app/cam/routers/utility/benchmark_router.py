"""
CAM Adaptive Benchmark Router

Benchmarking and visualization for adaptive toolpath algorithms.

Migrated from: routers/cam_adaptive_benchmark_router.py

Architecture Layer: ROUTER (Layer 6)
See: docs/governance/ARCHITECTURE_INVARIANTS.md

Endpoints:
    POST /offset_spiral.svg      - Generate inward offset spiral SVG
    POST /trochoid_corners.svg   - Generate trochoidal corner loops SVG
    POST /bench                  - Run performance benchmark
"""

from __future__ import annotations

import time
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from ....util.adaptive_geom import (
    inward_offset_spiral_rect,
    rect_offset_path,
    svg_polyline,
    trochoid_corner_loops,
)

router = APIRouter()


class SpiralReq(BaseModel):
    """Request model for offset spiral generation"""
    width: float = 100.0
    height: float = 60.0
    tool_dia: float = 6.0
    stepover: float = 2.4
    corner_fillet: float = 0.0


@router.post("/offset_spiral.svg", response_class=Response)
def offset_spiral(req: SpiralReq) -> Response:
    """
    Generate inward offset spiral toolpath for rectangular pocket.
    Returns SVG visualization.
    """
    if req.tool_dia <= 0:
        raise HTTPException(status_code=422, detail="Tool diameter must be positive")
    if req.width <= 0 or req.height <= 0:
        raise HTTPException(status_code=422, detail="Width and height must be positive")
    if req.stepover < 0:
        raise HTTPException(status_code=422, detail="Stepover cannot be negative")

    pts = inward_offset_spiral_rect(
        req.width,
        req.height,
        req.tool_dia,
        req.stepover,
        req.corner_fillet
    )
    return Response(
        content=svg_polyline(pts, stroke="purple"),
        media_type="image/svg+xml"
    )


class TrochReq(BaseModel):
    """Request model for trochoidal corner loops"""
    width: float = 100.0
    height: float = 60.0
    tool_dia: float = 6.0
    loop_pitch: float = 2.5
    amp: float = 0.4


@router.post("/trochoid_corners.svg", response_class=Response)
def trochoid_corners(req: TrochReq) -> Response:
    """
    Generate trochoidal loops around rectangle corners.
    Illustrates corner load management technique.
    Returns SVG visualization.
    """
    if req.tool_dia <= 0:
        raise HTTPException(status_code=422, detail="Tool diameter must be positive")
    if req.width <= 0 or req.height <= 0:
        raise HTTPException(status_code=422, detail="Width and height must be positive")
    if req.loop_pitch <= 0:
        raise HTTPException(status_code=422, detail="Loop pitch must be positive")

    outer = rect_offset_path(req.width, req.height, 0.0)
    pts = trochoid_corner_loops(outer, req.tool_dia, req.loop_pitch, req.amp)
    return Response(
        content=svg_polyline(pts, stroke="teal"),
        media_type="image/svg+xml"
    )


class BenchReq(BaseModel):
    """Request model for performance benchmarking"""
    width: float = 100.0
    height: float = 60.0
    tool_dia: float = 6.0
    stepover: float = 2.4
    runs: int = 20


@router.post("/bench")
def bench(req: BenchReq) -> Dict[str, Any]:
    """
    Run performance benchmark on inward offset spiral algorithm.
    Measures average execution time over multiple runs.

    Returns:
        JSON with timing statistics and test parameters
    """
    if req.tool_dia <= 0:
        raise HTTPException(status_code=422, detail="Tool diameter must be positive")
    if req.width <= 0 or req.height <= 0:
        raise HTTPException(status_code=422, detail="Width and height must be positive")
    if req.stepover < 0:
        raise HTTPException(status_code=422, detail="Stepover cannot be negative")
    if req.runs <= 0:
        raise HTTPException(status_code=422, detail="Runs must be positive")

    # Individual run timing for better accuracy
    run_times = []
    for _ in range(req.runs):
        t0 = time.perf_counter()
        _ = inward_offset_spiral_rect(
            req.width,
            req.height,
            req.tool_dia,
            req.stepover,
            0.6  # Fixed fillet for consistent benchmarking
        )
        t1 = time.perf_counter()
        run_times.append((t1 - t0) * 1000.0)

    total_ms = sum(run_times)
    avg_ms = total_ms / req.runs

    return {
        "runs": req.runs,
        "total_ms": round(total_ms, 3),
        "avg_ms": round(avg_ms, 3),
        "width": req.width,
        "height": req.height,
        "tool_dia": req.tool_dia,
        "stepover": req.stepover
    }
