"""Generator capabilities — the "what can it do" axis, orthogonal to category.

Part of the GFR catalog value contracts. Vocabulary only; imports nothing from
the framework and nothing from any generator implementation.

A category answers *what kind of thing a generator makes*; a capability answers
*what a caller can ask of it*. The two are deliberately independent: a
BODY_GEOMETRY generator and a NECK_HEADSTOCK generator may both advertise
`DXF_EXPORT`, and one generator may advertise several capabilities.

Capabilities are **descriptive metadata**. Declaring `DXF_EXPORT` does not give
the catalog any way to produce a DXF — the catalog never imports or invokes an
implementation. It records that the implementation claims the capability, so a
human or a downstream execution system can find it.
"""

from __future__ import annotations

from enum import Enum


class GeneratorCapability(str, Enum):
    """What a caller can ask a generator to do.

    `(str, Enum)` so a record serializes to a stable string. The `.value` of
    every member is part of the catalog's external contract and is pinned by
    `tests/generators/framework/test_vocabulary.py`.
    """

    DXF_EXPORT = "dxf_export"
    """Emits DXF. Scope: the generator itself produces DXF entities or a DXF
    document. A generator that produces points someone else writes to DXF has
    GEOMETRY_SYNTHESIS, not this."""

    SVG_EXPORT = "svg_export"
    """Emits SVG. Kept distinct from DXF_EXPORT because the two have different
    consumers — SVG for preview and documentation, DXF for CAD and CAM — and a
    generator commonly supports one without the other."""

    GCODE_EXPORT = "gcode_export"
    """Emits machine G-code. Scope: dialect-specific controller output.
    System use: `app.generators.lespaul_gcode`."""

    GEOMETRY_SYNTHESIS = "geometry_synthesis"
    """Computes geometry — points, curves, surfaces — without committing to an
    output format. This is the capability of the calculation itself, and is what
    a generator advertises when a separate writer serializes its result."""

    PARAMETRIC_CONFIG = "parametric_config"
    """Accepts a structured configuration object that varies the output.
    Distinguished from PRESET_LIBRARY: this is the open parameter surface, that
    is the closed set of named points within it.
    System use: `app.generators.neck_headstock_config`, `lespaul_config`,
    `stratocaster_config`."""

    PRESET_LIBRARY = "preset_library"
    """Ships named presets — a closed, enumerable set of known-good
    configurations. System use: `app.generators.neck_headstock_presets`."""

    SPEC_DRIVEN = "spec_driven"
    """Reads an instrument specification as its primary input, rather than
    taking dimensions directly. Scope: the generator resolves a named
    instrument to dimensions itself."""

    PROFILE_SAMPLING = "profile_sampling"
    """Samples an existing profile or reference curve rather than synthesizing
    one. The read-side counterpart to GEOMETRY_SYNTHESIS, and the capability a
    REFERENCE_PROFILE_INPUT consumer advertises."""


__all__ = ["GeneratorCapability"]
