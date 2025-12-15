the complete /docs/RMOS_STUDIO_SAW_PIPELINE.md file, written in a professional engineering tone and structured for immediate inclusion in your repository.

RMOS_STUDIO_SAW_PIPELINE.md
RMOS Studio – Saw Pipeline & Slicing Algorithm Specification

Version 1.0 — Engineering Document

1. Purpose

This document defines the saw pipeline for RMOS Studio. It provides a complete technical specification of:

The slicing algorithms

Tile segmentation → slice generation

Slice angle computation

Kerf-adjusted geometry

Batch ordering rules

Output artifacts used by manufacturing

Error and safety checks

This pipeline is the core mechanical translation system that converts rosette pattern definitions into physical saw operations.

2. Pipeline Overview

The RMOS Saw Pipeline consists of the following phases:

Ring Circumference Computation

Tile Segmentation

Slice Definition

Angle/Twist Application

Kerf Compensation

Saw Batch Assembly

Output File Generation

Validation & Safety Checks

The pipeline must produce deterministic and reproducible slice sets.

3. Geometry Fundamentals
3.1 Ring Circumference

For each ring:

C = 2πR


Where:

C = circumference (mm)

R = ring radius (mm)

3.2 Tile Count

Tiles must be uniform around the ring.

N = floor(C / tile_length_mm)


Constraints:

N ≥ 2

Recommended upper bound: N ≤ 300

3.3 Effective Tile Length

To eliminate fractional leftover segments:

effective_tile_length = C / N


This value is used for tile-based slicing.

4. Tile Segmentation Algorithm
4.1 Tile Indexing

Tiles are indexed:

tile_index = 0, 1, 2, ..., N-1


Each tile corresponds to one saw slice.

4.2 Tile-Origin Angle

Each tile has a start angle computed as:

θ₀ = (tile_index / N) * 360°


Angles increase clockwise unless defined otherwise by material feed direction.

4.3 Tile Bounds

Tile angular bounds:

θ_start = θ₀
θ_end   = θ₀ + (360° / N)


RMOS Studio displays these as radial boundaries in the Multi-Ring Preview.

5. Slice Definition

A slice is the physical vertical cut taken through the column stack.

Each slice includes:

Tile index

Angle start / end

Effective tile length

Column cross-section at slice location

Material and color attributes

Strip-family assignment

Slices must be computed before twist or herringbone operations are applied.

6. Twist, Angle, and Herringbone Logic
6.1 Twist Angle

User-defined rotation applied to an entire ring.

θ_twisted_start = θ_start + twist_angle
θ_twisted_end   = θ_end   + twist_angle


The twist shifts the entire pattern around the circumference.

6.2 Herringbone Mode

Herringbone patterns require alternating slice angles.

For alternating tiles:

if tile_index is even:
    slice_angle = +herringbone_angle
else:
    slice_angle = -herringbone_angle


Typical herringbone angles: 25°–45°

6.3 Angle Priority Order

If multiple angle modifiers exist:

Tile segmentation (base angle)

Twist angle

Pattern-specific angle (e.g., herringbone)

Final slice angle:

final_angle = base_angle + twist_angle + pattern_angle

7. Kerf Compensation

Kerf is the blade thickness that removes material during cutting.
Typical kerf: 0.5–1.0 mm

7.1 Radial Kerf Offset

Each slice must apply kerf offset:

kerf_adjusted_angle = final_angle - (kerf / R)


Compensation prevents cumulative alignment drift.

7.2 Material Centering

The slice must preserve:

Tile boundaries

Strip alignment

Visual continuity

Kerf-adjusted geometry ensures predictable tile width.

8. Saw Batch Assembly

Saw batches represent the ordered sequence of all slices needed to produce a ring.

8.1 Slice Ordering

Slices must be ordered sequentially by tile index:

slice_order = 0 → N-1


RMOS enforces ascending order unless operator defines reverse-feed mode.

8.2 Batch Structure

Batch metadata:

Batch {
    ring_id: int
    radius_mm: float
    N_tiles: int
    tile_length_mm: float
    twist_angle: float
    herringbone_angle: float
    kerf_mm: float
    slices: List<Slice>
}

8.3 Slice Object Structure
Slice {
    index: int
    angle_start: float
    angle_end: float
    slice_angle: float
    material_map: List<Color/Material>
    strip_family_map: List<FamilyID>
}

9. Output Artifacts

RMOS Studio produces the following files:

9.1 JSON Saw Batch File

Contains all computed geometry and slice parameters.

Example structure:

{
    "ring_id": 1,
    "radius_mm": 47.0,
    "tile_count": 128,
    "tile_length_mm": 2.304,
    "twist_angle": 3.0,
    "kerf_mm": 0.6,
    "slices": [
        {
            "index": 0,
            "angle_start": 0.0,
            "angle_end": 2.8125,
            "slice_angle": 25.0,
            "material_map": [...],
            "strip_family_map": [...]
        },
        ...
    ]
}


Exported as:

/exports/rings/{ring_id}/saw_batch.json

9.2 Tile Sequence Preview Image

Rasterized or vector image of tile segmentation.

9.3 Slice Angle Diagram

Visual diagram of twist/herringbone geometry.

10. Validation & Safety Checks
10.1 Geometric Validation

N ≥ 2

effective_tile_length > 0

radius_mm > minimum allowed

no negative angles

kerf-adjusted angle must remain monotonic

10.2 Manufacturability Validation

Strip widths allow slicing without collapse

Tile lengths not below 1 mm

Max tiles per ring not exceeded

No cumulative angular drift

Warnings are displayed in UI.

Errors block slice generation.

10.3 Operator Safety Constraints

No overlapping slice angles

No reverse-angle cuts unless explicitly approved

Batch must end at tile_index = N-1

11. Performance Requirements

Handle rings up to N = 300 tiles

Compute full batch in < 50 ms on standard hardware

Real-time UI updates must be < 16 ms per update

12. Future Extensions

Variable-kerf adaptive models

Multi-blade composite saws

Distributed slicing simulation

Grain-direction-aware slicing

3D curvature compensation for arched surfaces

13. File Location

This document belongs in:

/docs/RMOS_STUDIO_SAW_PIPELINE.md

End of Document

RMOS Studio — Saw Pipeline Specification (Engineering Version)