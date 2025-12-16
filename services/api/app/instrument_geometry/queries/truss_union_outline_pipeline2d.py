"""
Stub for truss union outline pipeline.

This module provides the 2D outline for truss union pocket geometry.
Replace with actual implementation when available.

Target: instrument_geometry/queries/truss_union_outline_pipeline2d.py
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Point2D:
    """Simple 2D point with mm coordinates."""
    x_mm: float
    y_mm: float


@dataclass
class Outline2D:
    """2D outline representation."""
    points: List[Point2D]


def get_truss_union_outline_final_2d(geom) -> Outline2D:
    """
    Get the final 2D outline for truss union pocket.
    
    This is a stub implementation. Replace with actual geometry
    extraction from your instrument geometry system.
    
    Args:
        geom: InstrumentGeometry instance
        
    Returns:
        Outline2D with the pocket boundary points
    """
    # Stub: return empty outline or extract from geom if available
    # In production, this should extract the actual truss union outline
    # from the instrument geometry data
    
    # Check if geom has a method to get outline
    if hasattr(geom, 'get_truss_union_outline'):
        raw_points = geom.get_truss_union_outline()
        return Outline2D(points=[Point2D(x_mm=p[0], y_mm=p[1]) for p in raw_points])
    
    # Fallback: return a simple rectangle as placeholder
    return Outline2D(points=[
        Point2D(x_mm=0.0, y_mm=0.0),
        Point2D(x_mm=100.0, y_mm=0.0),
        Point2D(x_mm=100.0, y_mm=50.0),
        Point2D(x_mm=0.0, y_mm=50.0),
    ])
